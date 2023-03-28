# Copyright 2017 Wildan Maulana Syahidillah

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from time import time

from ryu.base.app_manager import RyuApp
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.controller.ofp_event import EventOFPPacketIn
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.ipv4 import ipv4
from ryu.lib.packet.icmp import icmp, echo
from ryu.lib.packet.ether_types import ETH_TYPE_IP
from ryu.lib.packet.in_proto import IPPROTO_ICMP
from ryu.lib.hub import spawn, sleep
from ryu.topology.event import EventSwitchEnter

from settings import *


class DelayMonitor(RyuApp):
    '''
        Ryu app for monitoring delays between hosts and switches by sending 
        hosts ICMP packets (pings) by means of their respective switches, 
        receiving their responses, and calculating the total elapsed time. 
        The most recent measures are saved in a dictionary. 

        Requirements:
        -------------
        Switches app (built-in): for switch list.

        SimpleARP app: for ARP table and resolving decoy controller ARP 
        entries.

        NetworkDelayDetector app: for removing switch-controller latency.

        Attributes:
        -----------
        delay: dict mapping host IP address to delay of link to switch 
        in seconds (two-way).
    '''

    def __init__(self, *args, **kwargs):
        super(DelayMonitor, self).__init__(*args, **kwargs)
        self.name = DELAY_MONITOR
        self._hosts = set()

        self._switches = None
        self._simple_arp = None
        self._network_delay_detector = None
        self._add_flow = None

        self.delay = {}
        spawn(self._monitor)

    def _monitor(self):
        while True:
            try:
                for ip in list(self.delay):
                    if ip not in self._simple_arp._in_ports:
                        self.delay.pop(ip, None)

                for ip, (dpid, port) in self._simple_arp._in_ports.items():
                    self._send_icmp_packet(self._switches.dps[dpid], ip,
                                           self._simple_arp.arp_table[ip],
                                           port)

                    # Important! Don't send pings together, because that will
                    # generate a lot of replies almost at the same time, which
                    # will generate a lot of delay of waiting in queue when
                    # handling replies.
                    sleep(0.05)

            except Exception as e:
                print(' *** ERROR in delay_monitor._monitor:',
                      e.__class__.__name__, e)

            finally:
                sleep(MONITOR_PERIOD)

    def _send_icmp_packet(self, datapath, dst_ip, dst_mac, out_port):
        pkt = Packet()
        pkt.add_protocol(
            ethernet(ethertype=ETH_TYPE_IP, src=CONTROLLER_MAC, dst=dst_mac))
        pkt.add_protocol(
            ipv4(proto=IPPROTO_ICMP, src=CONTROLLER_IP, dst=dst_ip))
        pkt.add_protocol(
            icmp(data=echo(data=bytes('%f' % time(), 'utf-8'))))
        pkt.serialize()

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        datapath.send_msg(
            parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER, data=pkt.data,
                actions=[parser.OFPActionOutput(out_port)]))

    @set_ev_cls(EventSwitchEnter)
    def _switch_enter_handler(self, ev):
        datapath = ev.switch.dp
        parser = datapath.ofproto_parser

        # install flow to allow ARP replies to reach controller decoy
        while not self._add_flow:
            sleep(0.1)
        self._add_flow(
            datapath, 65535,
            parser.OFPMatch(eth_type=ETH_TYPE_IP, ip_proto=IPPROTO_ICMP,
                            ipv4_dst=CONTROLLER_IP),
            [parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER)])

    @set_ev_cls(EventOFPPacketIn, MAIN_DISPATCHER)
    def _icmp_packet_in_handler(self, ev):
        pkt = Packet(ev.msg.data)
        eth = pkt.get_protocol(ethernet)
        if eth.dst == CONTROLLER_MAC:
            icmp_pkt = pkt.get_protocol(icmp)
            if icmp_pkt:
                '''
                    ICMP packet:
                    Controller <---------------> Switch <---------------> Host
                                ctrl_switch_lat          switch_host_lat
                               <---------------------------------------->
                                                latency 

                    switch_host_lat = latency - ctrl_switch_lat
                '''
                try:
                    self.delay[pkt.get_protocol(ipv4).src] = max(
                        0, (ev.timestamp
                            - float(icmp_pkt.data.data)
                            - self._network_delay_detector.echo_latency[
                                ev.msg.datapath.id]))

                except Exception as e:
                    print(' *** ERROR in delay_monitor._icmp_packet_in_handler:',
                          e.__class__.__name__, e)
