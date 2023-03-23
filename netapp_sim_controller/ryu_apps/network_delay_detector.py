# Copyright (C) 2016 Li Cheng at Beijing University of Posts
# and Telecommunications. www.muzixing.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from time import time

from ryu.base.app_manager import RyuApp
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.controller.ofp_event import EventOFPPacketIn, EventOFPEchoReply
from ryu.lib.hub import spawn, sleep
from ryu.topology.switches import LLDPPacket

from settings import *


class NetworkDelayDetector(RyuApp):
    '''
        Ryu app for monitoring delays of links between switches by collecting 
        LLDP packets and calculating LLDP latencies, and periodically sending 
        OFPEchoRequest to all switches to monitor latencies between controller 
        and switches, and finally subtracting ECHO latencies from LLDP 
        latencies to get delays on each link. Most recent measures are saved 
        in dictionaries.

        Requirements:
        -------------
        Switches app (built-in): for switch and port lists.

        Attributes:
        ----------- 
        lldp_latency: dict mapping src DPID and dst DPID to LLDP latency 
        in seconds (one-way).

        echo_latency: dict mapping DPID to controller-switch latency 
        in seconds (two-way).

        delay: dict mapping src DPID and dst DPID to link delay 
        in seconds (one-way).
    '''

    def __init__(self, *args, **kwargs):
        super(NetworkDelayDetector, self).__init__(*args, **kwargs)
        self.name = NETWORK_DELAY_DETECTOR

        self._switches = None

        self.lldp_latency = {}
        self.echo_latency = {}
        self.delay = {}
        spawn(self._detector)

    def _detector(self):
        while True:
            try:
                self._send_echo_requests()
                for src in self.lldp_latency:
                    if self.lldp_latency[src]:
                        self.delay.setdefault(src, {})
                        for dst in self.lldp_latency[src]:
                            '''
                                                Controller
                                                |        |
                                src_echo_latency|        |dst_echo_latency
                                                |        |
                                        SwitchA--------SwitchB

                                fwd_lldp_latency------->
                                                <-------rpl_lldp_latency

                                fwd_delay = (fwd_lldp_latency - dst_echo_latency / 2)
                                rpl_delay = (rpl_lldp_latency - src_echo_latency / 2)
                            '''
                            try:
                                # one-way delay src -> dst
                                self.delay[src][dst] = max(
                                    0, (self.lldp_latency[src][dst]
                                        - self.echo_latency[dst] / 2))
                            except:
                                self.delay[src][dst] = float('inf')

            except Exception as e:
                print(' *** ERROR in network_delay_detector._detector:',
                      e.__class__.__name__, e)
            finally:
                sleep(MONITOR_PERIOD)

    def _send_echo_requests(self):
        for datapath in self._switches.dps.values():
            datapath.send_msg(
                datapath.ofproto_parser.OFPEchoRequest(
                    datapath, data=bytes('%f' % time(), 'utf-8')))

            # Important! Don't send echo requests together, because that will
            # generate a lot of echo replies almost at the same time, which
            # will generate a lot of delay of waiting in queue when handling
            # echo replies.
            sleep(0.05)

    @set_ev_cls(EventOFPPacketIn, MAIN_DISPATCHER)
    def _lldp_packet_in_handler(self, ev):
        msg = ev.msg
        try:
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            for port in self._switches.ports:
                if src_dpid == port.dpid and src_port_no == port.port_no:
                    self.lldp_latency.setdefault(src_dpid, {})
                    self.lldp_latency[src_dpid][msg.datapath.id] = (
                        ev.timestamp - self._switches.ports[port].timestamp)
                    return

        except LLDPPacket.LLDPUnknownFormat:
            return

        except Exception as e:
            print(' *** ERROR in network_delay_detector._lldp_packet_in_handler:',
                  e.__class__.__name__, e)

    @set_ev_cls(EventOFPEchoReply, MAIN_DISPATCHER)
    def _echo_reply_handler(self, ev):
        try:
            self.echo_latency[ev.msg.datapath.id] = (
                ev.timestamp - eval(ev.msg.data))

        except Exception as e:
            print(' *** ERROR in network_delay_detector._echo_reply_handler:',
                  e.__class__.__name__, e)
