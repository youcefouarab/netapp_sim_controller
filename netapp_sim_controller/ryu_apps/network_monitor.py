# Copyright (C) 2016 Li Cheng at Beijing University of Posts
# and Telecommunications. www.muzixing.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from ryu.base.app_manager import RyuApp
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.controller.ofp_event import (EventOFPPortStatsReply,
                                      EventOFPPortDescStatsReply)
from ryu.ofproto.ofproto_v1_3 import OFPP_LOCAL
from ryu.lib.hub import spawn, sleep

from settings import *


class NetworkMonitor(RyuApp):
    '''
        Ryu app for collecting traffic information for ports by periodically 
        sending OFPPortDescStatsRequest and OFPPortStatsRequest to all 
        switches. Most recent measures are saved in dictionaries. 

        Requirements:
        -------------
        Switches app (built-in): for switch list.

        Attributes:
        -----------
        port_features: dict mapping DPID and port number to tuple of port's 
        state, connected link's state, and port's capacity in kB/s.

        port_stats: dict mapping DPID and port number to list of 5 most recent 
        measures of port's Tx and Rx bytes, errors, and loss, and period of 
        measure in seconds and nanoseconds.

        port_speed: dict mapping DPID and port number to list of 5 mist recent 
        measures of port's speeds (up and down) in B/s.

        free_bandwidth: dict mapping DPID and port number to tuple of port's 
        current available bandwidths (up and down) in Mbit/s.
    '''

    def __init__(self, *args, **kwargs):
        super(NetworkMonitor, self).__init__(*args, **kwargs)
        self.name = NETWORK_MONITOR

        self._switches = None

        self.port_features = {}
        self.port_stats = {}
        self.port_speed = {}
        self.free_bandwidth = {}
        spawn(self._monitor)

    def _monitor(self):
        while True:
            try:
                for datapath in self._switches.dps.values():
                    self._send_stats_request(datapath)

            except Exception as e:
                print(' *** ERROR in network_monitor._monitor:',
                      e.__class__.__name__, e)

            finally:
                sleep(MONITOR_PERIOD)

    def _send_stats_request(self, datapath):
        parser = datapath.ofproto_parser
        datapath.send_msg(parser.OFPPortDescStatsRequest(datapath, 0))
        datapath.send_msg(parser.OFPPortStatsRequest(datapath, 0))

    def _save_stats(self, _dict, key, value, length):
        _dict.setdefault(key, [])
        _dict[key].append(value)
        if len(_dict[key]) > length:
            _dict[key].pop(0)

    @set_ev_cls(EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def _port_desc_stats_reply_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        config_dict = {ofproto.OFPPC_PORT_DOWN: 'Down',
                       ofproto.OFPPC_NO_RECV: 'No Recv',
                       ofproto.OFPPC_NO_FWD: 'No Fwd',
                       ofproto.OFPPC_NO_PACKET_IN: 'No Packet-in'}
        state_dict = {ofproto.OFPPS_LINK_DOWN: 'Down',
                      ofproto.OFPPS_BLOCKED: 'Blocked',
                      ofproto.OFPPS_LIVE: 'Live'}

        dpid = datapath.id
        self.port_features.setdefault(dpid, {})
        for port in msg.body:
            port_no = port.port_no
            if port_no != OFPP_LOCAL:
                config = port.config
                state = port.state
                self.port_features[dpid][port_no] = (
                    config_dict[config] if config in config_dict else 'up',
                    state_dict[state] if state in state_dict else 'up',
                    port.curr_speed)

    @set_ev_cls(EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        msg = ev.msg
        dpid = msg.datapath.id
        self.free_bandwidth.setdefault(dpid, {})
        for stat in msg.body:
            port_no = stat.port_no
            if port_no != OFPP_LOCAL:
                key = (dpid, port_no)
                self._save_stats(
                    self.port_stats, key, (stat.tx_bytes, stat.rx_bytes,
                                           stat.tx_errors, stat.rx_errors,
                                           stat.tx_dropped, stat.rx_dropped,
                                           stat.duration_sec,
                                           stat.duration_nsec), 5)

                # =====================================================
                # this section of the code is changed from the original
                # the original code combines up speed and down speed
                # the new code separates them
                up_pre = 0
                down_pre = 0
                period = MONITOR_PERIOD
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    up_pre = tmp[-2][0]
                    down_pre = tmp[-2][1]
                    period = (tmp[-1][-2] + tmp[-1][-1] / (10 ** 9)
                              - tmp[-2][-2] + tmp[-2][-1] / (10 ** 9))
                up_speed = ((self.port_stats[key][-1][0] - up_pre) / period
                            ) if period else 0
                down_speed = ((self.port_stats[key][-1][1] - down_pre) / period
                              ) if period else 0
                self._save_stats(
                    self.port_speed, key, (up_speed, down_speed), 5)

                try:
                    capacity = self.port_features[dpid][port_no][2] / 10**3

                except KeyError:
                    pass

                except Exception as e:
                    print(' *** ERROR in network_monitor._port_stats_reply_handler:',
                          e.__class__.__name__, e)

                else:
                    self.free_bandwidth[dpid][port_no] = (
                        max(capacity - up_speed * 8/10**6, 0),    # unit: Mbit/s
                        max(capacity - down_speed * 8/10**6, 0))  # unit: Mbit/s
                # =====================================================
