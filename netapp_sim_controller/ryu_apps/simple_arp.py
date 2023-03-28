# Copyright 2017 Wildan Maulana Syahidillah

# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from ipaddress import ip_address
from re import sub

from ryu.base.app_manager import RyuApp
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.controller.ofp_event import EventOFPPacketIn
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.arp import arp, ARP_REQUEST, ARP_REPLY
from ryu.lib.packet.ether_types import ETH_TYPE_ARP
from ryu.lib.mac import BROADCAST_STR
from ryu.lib.hub import sleep, spawn
from ryu.topology.event import EventSwitchEnter, EventSwitchLeave

from settings import *


# get individual IP addresses from IP_POOL
IPS = []
_pools = sub('[^0-9.:,]+', '', IP_POOL).split(',')
for _pool in _pools:
    try:
        # if _pool is an interval
        _start, _end = _pool.split(':')
        for ip in range(int(ip_address(_start).packed.hex(), 16),
                        int(ip_address(_end).packed.hex(), 16) + 1):
            IPS.append(ip_address(ip).exploded)

    except:
        # if _pool is one value
        try:
            IPS.append(ip_address(_pool).exploded)

        except Exception as e:
            print(' *** ERROR in simple_arp:', e.__class__.__name__, e)


class SimpleARP(RyuApp):
    '''
        Ryu app for IPv4 layer discovery through ARP requests sent by 
        controller to pools of IP addresses by way of each connected switch 
        (at each consumption of EventSwitchEnter). Creates ARP table mapping 
        hosts' IP addresses to MAC addresses, updated periodically (by default 
        every 1 minute).

        Attributes:
        -----------
        arp_table: dict mapping hosts' IP addresses to MAC addresses.
    '''

    def __init__(self, *args, **kwargs):
        super(SimpleARP, self).__init__(*args, **kwargs)
        self.name = SIMPLE_ARP

        self._add_flow = None

        self.arp_table = {}
        self._in_ports = {}

    def _request_arp(self, datapath, dst_ip, out_port=None):
        pkt = Packet()
        pkt.add_protocol(
            ethernet(ethertype=ETH_TYPE_ARP, src=CONTROLLER_MAC,
                     dst=BROADCAST_STR))
        pkt.add_protocol(
            arp(opcode=ARP_REQUEST,
                src_mac=CONTROLLER_MAC, src_ip=CONTROLLER_IP,
                dst_mac=BROADCAST_STR, dst_ip=dst_ip))
        pkt.serialize()

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        if out_port == None:
            out_port = ofproto.OFPP_FLOOD

        datapath.send_msg(
            parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER, data=pkt.data,
                actions=[parser.OFPActionOutput(out_port)]))

    def _reply_arp(self, datapath, eth_dst, ip_dst, out_port):
        # this is needed to resolve decoy controller ARP entries for ARP
        # poisoning prevention systems, by replying to ARP requests sent
        # to controller
        pkt = Packet()
        pkt.add_protocol(
            ethernet(ethertype=ETH_TYPE_ARP, src=CONTROLLER_MAC, dst=eth_dst))
        pkt.add_protocol(
            arp(opcode=ARP_REPLY, src_mac=CONTROLLER_MAC, src_ip=CONTROLLER_IP,
                dst_mac=eth_dst, dst_ip=ip_dst))
        pkt.serialize()

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        datapath.send_msg(
            parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER, data=pkt.data,
                actions=[parser.OFPActionOutput(out_port)]))

    def _send_arp_requests(self, datapath):
        while True:
            try:
                for ip in IPS:
                    self._request_arp(datapath, ip)

                    # don't send ARP requests together to not overwhelm
                    # network with traffic and controller with handlers
                    sleep(0.05)

            except Exception as e:
                print('simple_arp._send_arp_requests', e.__class__.__name__, e)

            finally:
                if not self.arp_table:
                    sleep(10)
                else:
                    sleep(ARP_REFRESH)

    @set_ev_cls(EventSwitchEnter)
    def _switch_enter_handler(self, ev):
        datapath = ev.switch.dp
        parser = datapath.ofproto_parser

        # install flow to allow ARP replies to reach controller decoy
        while not self._add_flow:
            sleep(0.1)
        self._add_flow(
            datapath, 65535,
            parser.OFPMatch(eth_type=ETH_TYPE_ARP, arp_tpa=CONTROLLER_IP),
            [parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER)])

        spawn(self._send_arp_requests, datapath)

    @set_ev_cls(EventOFPPacketIn, MAIN_DISPATCHER)
    def _arp_packet_in_handler(self, ev):
        pkt = Packet(ev.msg.data)
        arp_pkt = pkt.get_protocol(arp)
        if arp_pkt:
            eth = pkt.get_protocol(ethernet)
            if eth.dst != BROADCAST_STR:
                src_ip = arp_pkt.src_ip
                self.arp_table[src_ip] = eth.src
                self._in_ports[src_ip] = (ev.msg.datapath.id,
                                          ev.msg.match['in_port'])
            else:
                self._reply_arp(ev.msg.datapath, eth.src, arp_pkt.src_ip,
                                ev.msg.match['in_port'])

    @set_ev_cls(EventSwitchLeave)
    def _switch_leave_handler(self, ev):
        for ip in list(self._in_ports):
            if self._in_ports[ip][0] == ev.switch.dp.id:
                self.arp_table.pop(ip, None)
                self._in_ports.pop(ip, None)
