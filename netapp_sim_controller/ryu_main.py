from logging import getLogger, WARNING

from ryu.base.app_manager import RyuApp, require_app
from ryu.controller.ofp_handler import OFPHandler
from ryu.topology.switches import Switches
from ryu.controller.dpset import DPSet
from ryu.app.wsgi import WSGIApplication
from ryu.lib.hub import spawn, sleep

from ryu_apps import *


require_app('ryu.app.rest_topology')

# hide WSGI messages on console
getLogger('ryu.lib.hub').setLevel(WARNING)


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
        METRICS: Metrics,

        WSGI: WSGIApplication,
        DPSET: DPSet,
        FLOW_MANAGER: FlowManager
    }

    def __init__(self, *args, **kwargs):
        super(RyuMain, self).__init__(*args, **kwargs)
        self.switches = kwargs[SWITCHES]
        self.simple_arp = kwargs[SIMPLE_ARP]
        self.network_monitor = kwargs[NETWORK_MONITOR]
        self.network_delay_detector = kwargs[NETWORK_DELAY_DETECTOR]
        self.delay_monitor = kwargs[DELAY_MONITOR]
        self.metrics = kwargs[METRICS]

        self.wsgi = kwargs[WSGI]
        self.dpset = kwargs[DPSET]
        self.flowmanager = kwargs[FLOW_MANAGER]
        self.flowmanager.wsgi = self.wsgi
        self.flowmanager.dpset = self.dpset

        spawn(self._test)

    def _test(self):
        from pprint import pprint
        i = 0
        while True:
            sleep(2)
            i += 1
            # print(i)
            # print()
            print('### ARP TABLE ###')
            pprint(self.simple_arp.arp_table)
            print('#################')
            print()
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
            print('### FREE BANDWIDTH ###')
            for dpid, ports in self.network_monitor.free_bandwidth.items():
                for port, (bw_up, bw_down) in ports.items():
                    print('< switch %d, port %d > : UP %.2f Mbps | '
                          'DOWN %.2f Mbps' % (dpid, port, bw_up, bw_down))
            print('######################')
            print()
            print('### LOSS RATE ###')
            for src in self.network_monitor.loss_rate:
                for dst in self.network_monitor.loss_rate[src]:
                    loss = self.network_monitor.loss_rate[src][dst]
                    print(src, '-->', dst, ':', round(loss * 100, 2), '%')
            print('#################')
            print()
            #for src in self.network_delay_detector.lldp_latency:
            #    for dst in self.network_delay_detector.lldp_latency[src]:
            #        lat = self.network_delay_detector.lldp_latency[src][dst]
            #        print(src, '-->', dst, round(lat * 1000, 2), 'ms')
            #print()
            #for dpid in self.network_delay_detector.echo_latency:
            #    lat = self.network_delay_detector.echo_latency[dpid]
            #    print(dpid, '<-->', 'ctrl', round(lat * 1000, 2), 'ms')
            #print()
            print('### SWITCH DELAY ###')
            for src in self.network_delay_detector.delay:
                for dst in self.network_delay_detector.delay[src]:
                    lat = self.network_delay_detector.delay[src][dst]
                    print(src, '-->', dst, ':', round(lat * 1000, 2), 'ms')
            print('####################')
            print()
            #for src, dst in self.network_delay_detector._delay_history:
            #    delays = self.network_delay_detector._delay_history[(src,dst)]
            #    print(src, '-->', dst, end='')
            #    pprint([round(delay * 1000, 2) for delay in delays])
            #print()
            print('### SWITCH JITTER ###')
            for src in self.network_delay_detector.jitter:
                for dst in self.network_delay_detector.jitter[src]:
                    jitter = self.network_delay_detector.jitter[src][dst]
                    print(src, '-->', dst, ':', round(jitter * 1000, 2), 'ms')
            print('#####################')
            print()
            #for ip, jitters in self.delay_monitor._delay_history.items():
            #    print(ip, ':', end='')
            #    pprint([round(jitter * 1000, 2) for jitter in jitters])
            #print()
            print('### HOST DELAY ###')
            for ip, delay in self.delay_monitor.delay.items():
                print(ip, '<-> switch :', round(delay * 1000, 2), 'ms')
            print('##################')
            print()
            print('### HOST JITTER ###')
            for ip, jitter in self.delay_monitor.jitter.items():
                print(ip, '<-> switch :', round(jitter * 1000, 2), 'ms')
            print('###################')
            print()
