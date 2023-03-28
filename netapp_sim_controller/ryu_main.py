from ryu.base.app_manager import RyuApp
from ryu.controller.ofp_handler import OFPHandler
from ryu.topology.switches import Switches
from ryu.lib.hub import spawn, sleep

from ryu_apps import *


class RyuMain(RyuApp):
    '''
        Main Ryu app to launch with 'ryu run' or 'ryu-manager' commands. 
        launches all custom Ryu apps defined in ryu_apps directory for network 
        monitoring.
    '''

    _CONTEXTS = {
        'ofp_handler': OFPHandler,
        'switches': Switches,
        SIMPLE_ARP: SimpleARP,
        NETWORK_MONITOR: NetworkMonitor,
        NETWORK_DELAY_DETECTOR: NetworkDelayDetector,
        DELAY_MONITOR: DelayMonitor,
        METRICS: Metrics
    }

    def __init__(self, *args, **kwargs):
        super(RyuMain, self).__init__(*args, **kwargs)
        self.switches = kwargs['switches']
        self.simple_arp = kwargs[SIMPLE_ARP]
        self.simple_arp._add_flow = self.add_flow
        self.network_monitor = kwargs[NETWORK_MONITOR]
        self.network_monitor._switches = self.switches
        self.network_delay_detector = kwargs[NETWORK_DELAY_DETECTOR]
        self.network_delay_detector._switches = self.switches
        self.delay_monitor = kwargs[DELAY_MONITOR]
        self.delay_monitor._switches = self.switches
        self.delay_monitor._simple_arp = self.simple_arp
        self.delay_monitor._network_delay_detector = self.network_delay_detector
        self.delay_monitor._add_flow = self.add_flow
        self.metrics = kwargs[METRICS]
        self.metrics._switches = self.switches
        self.metrics._simple_arp = self.simple_arp
        self.metrics._network_monitor = self.network_monitor
        self.metrics._network_delay_detector = self.network_delay_detector
        self.metrics._delay_monitor = self.delay_monitor

        # spawn(self._test)

    def add_flow(self, datapath, priority, match, actions):
        parser = datapath.ofproto_parser
        datapath.send_msg(
            parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match,
                instructions=[parser.OFPInstructionActions(
                    datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]))

    def _test(self):
        from pprint import pprint
        i = 0
        while True:
            sleep(1)
            i += 1
            # print(i)
            # print()
            # pprint(self.simple_arp.arp_table)
            # print()
            # pprint(self.simple_arp._in_ports)
            # print()
            # for src in self.network_delay_detector.lldp_latency:
            #    for dst in self.network_delay_detector.lldp_latency[src]:
            #        lat = self.network_delay_detector.lldp_latency[src][dst]
            #        print(src, '-->', dst, round(lat * 1000, 2), 'ms')
            # print()
            # for dpid in self.network_delay_detector.echo_latency:
            #    lat = self.network_delay_detector.echo_latency[dpid]
            #    print(dpid, '<-->', 'ctrl', round(lat * 1000, 2), 'ms')
            # print()
            # for src in self.network_delay_detector.delay:
            #    for dst in self.network_delay_detector.delay[src]:
            #        lat = self.network_delay_detector.delay[src][dst]
            #        print(src, '-->', dst, round(lat * 1000, 2), 'ms')
            # print()
            # for ip, delay in self.delay_monitor.delay.items():
            #    print(ip, ':', round(delay * 1000, 2), 'ms')
            # print()
            # pprint(self.network_monitor.port_features)
            # print()
            # pprint(self.network_monitor.port_stats)
            # print()
            # pprint(self.network_monitor.port_speed)
            # print()
            # pprint(self.network_monitor.free_bandwidth)
            # print()
