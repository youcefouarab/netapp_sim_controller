from ryu.base.app_manager import RyuApp
from ryu.controller.ofp_handler import OFPHandler
from ryu.topology.switches import Switches
from ryu.lib.hub import spawn, sleep

from ryu_apps import *


class RyuMain(RyuApp):
    '''
        Main Ryu app to launch with 'ryu run' or 'ryu-manager' commands. 
        Launches all custom Ryu apps defined in ryu_apps directory for network 
        monitoring.
    '''

    _CONTEXTS = {
        OFP_HANDLER: OFPHandler,
        SWITCHES: Switches,
        SIMPLE_ARP: SimpleARP,
        NETWORK_MONITOR: NetworkMonitor,
        NETWORK_DELAY_DETECTOR: NetworkDelayDetector,
        DELAY_MONITOR: DelayMonitor,
        METRICS: Metrics
    }

    def __init__(self, *args, **kwargs):
        super(RyuMain, self).__init__(*args, **kwargs)
        self.switches = kwargs[SWITCHES]
        self.simple_arp = kwargs[SIMPLE_ARP]
        self.network_monitor = kwargs[NETWORK_MONITOR]
        self.network_delay_detector = kwargs[NETWORK_DELAY_DETECTOR]
        self.delay_monitor = kwargs[DELAY_MONITOR]
        self.metrics = kwargs[METRICS]

        #spawn(self._test)

    def _test(self):
        from pprint import pprint
        i = 0
        while True:
            sleep(1)
            i += 1
            # print(i)
            # print()
            #pprint(self.simple_arp.arp_table)
            #print()
            #pprint(self.simple_arp._reverse_arp_table)
            #print()
            #pprint(self.simple_arp._in_ports)
            #print()
            #pprint(self.network_monitor.port_features)
            #print()
            #pprint(self.network_monitor.port_stats)
            #print()
            #pprint(self.network_monitor.port_speed)
            #print()
            #pprint(self.network_monitor.free_bandwidth)
            #print()
            #pprint(self.network_monitor.loss_rate)
            #print()
            #for src in self.network_delay_detector.lldp_latency:
            #    for dst in self.network_delay_detector.lldp_latency[src]:
            #        lat = self.network_delay_detector.lldp_latency[src][dst]
            #        print(src, '-->', dst, round(lat * 1000, 2), 'ms')
            #print()
            #for dpid in self.network_delay_detector.echo_latency:
            #    lat = self.network_delay_detector.echo_latency[dpid]
            #    print(dpid, '<-->', 'ctrl', round(lat * 1000, 2), 'ms')
            #print()
            #for src in self.network_delay_detector.delay:
            #    for dst in self.network_delay_detector.delay[src]:
            #        lat = self.network_delay_detector.delay[src][dst]
            #        print(src, '-->', dst, round(lat * 1000, 2), 'ms')
            #print()
            #for src, dst in self.network_delay_detector._delay_history:
            #    delays = self.network_delay_detector._delay_history[(src,dst)]
            #    print(src, '-->', dst, end='')
            #    pprint([round(delay * 1000, 2) for delay in delays])
            #print()
            #for src in self.network_delay_detector.jitter:
            #    for dst in self.network_delay_detector.jitter[src]:
            #        jitter = self.network_delay_detector.jitter[src][dst]
            #        print(src, '-->', dst, round(jitter * 1000, 2), 'ms')
            #print()
            #for ip, jitters in self.delay_monitor._delay_history.items():
            #    print(ip, ':', end='')
            #    pprint([round(jitter * 1000, 2) for jitter in jitters])
            #print()
            #for ip, jitter in self.delay_monitor.jitter.items():
            #    print(ip, ':', round(jitter * 1000, 2), 'ms')
            #print()
