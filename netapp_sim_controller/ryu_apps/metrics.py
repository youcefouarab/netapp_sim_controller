from time import time

from ryu.base.app_manager import RyuApp
from ryu.lib.hub import spawn, sleep

from keystoneauth1.session import Session
from keystoneauth1.identity.v3 import Password
from gnocchiclient.client import Client
from gnocchiclient.exceptions import Conflict, NotFound

from settings import *


RESOURCE_TYPES = {
    'sdn_port': {
        'def': {
            'name': 'sdn_port',
            'attributes': {
                'name': {
                    'max_length': 255,
                    'min_length': 0,
                    'required': True,
                    'type': 'string'
                },
                'number': {
                    'max': 4294967295,
                    'min': 0,
                    'required': False,
                    'type': 'number'
                },
                'node': {
                    'max_length': 255,
                    'min_length': 0,
                    'required': True,
                    'type': 'string'
                }
            }
        },
        'metrics': ['bandwidth.up', 'bandwidth.down'],
        'units': ['Mbit/s', 'Mbit/s']
    },
    'sdn_link': {
        'def': {
            'name': 'sdn_link',
            'attributes': {
                'src': {
                    'max_length': 255,
                    'min_length': 0,
                    'required': True,
                    'type': 'string'
                },
                'dst': {
                    'max_length': 255,
                    'min_length': 0,
                    'required': True,
                    'type': 'string'
                }
            }
        },
        'metrics': ['bandwidth', 'delay'],
        'units': ['Mbit/s', 's']
    }
}


class Metrics(RyuApp):
    '''
        Ryu app for sending monitoring measures collected from various other 
        apps (like network_monitor, network_delay_detector and delay_monitor) 
        periodically to OpenStack's Ceilometer (Gnocchi time series database).

        Requirements:
        -------------
        Switches app (built-in): for datapath and port lists.

        SimpleARP app: for host in-ports mapping.

        NetworkMonitor app: for port stats.

        NetworkDelayDetector app: for switch-switch link delays.

        DelayMonitor: for host-switch link delays.
    '''

    def __init__(self, *args, **kwargs):
        super(Metrics, self).__init__(*args, **kwargs)
        self.name = METRICS

        self._switches = None
        self._simple_arp = None
        self._network_monitor = None
        self._network_delay_detector = None
        self._delay_monitor = None

        self._session = None
        self._client = None
        try:
            self._os_authenticate()
            self._archive_policies = [
                ap['name'] for ap in self._client.archive_policy.list()]

        except Exception as e:
            print(' *** ERROR in metrics.__init__:', e.__class__.__name__, e)

        else:
            spawn(self._add_measures)

    def _add_measures(self):
        while True:
            err = False
            try:
                measures = {}
                t = time()
                for dpid, ports in self._network_monitor.free_bandwidth.items():
                    for port_no, (bw_up, bw_down) in ports.items():
                        try:
                            node = str(dpid).zfill(16)
                            port_name = self._switches.dps[dpid].ports[
                                port_no].name.decode()
                            id = node + ':' + port_name
                            self._ensure_resource('sdn_port', {
                                'id': id,
                                'name': port_name,
                                'number': port_no,
                                'node': node
                            })

                            measures.update({
                                id: {
                                    'bandwidth.up': [{
                                        'timestamp': t,
                                        'value': bw_up
                                    }],
                                    'bandwidth.down': [{
                                        'timestamp': t,
                                        'value': bw_down
                                    }]
                                }
                            })

                        except Exception as e:
                            print(' *** ERROR in metrics._add_measures:',
                                  e.__class__.__name__, e)

                for src_dpid, dsts in self._network_delay_detector.delay.items():
                    for dst_dpid, delay in dsts.items():
                        try:
                            src = str(src_dpid).zfill(16)
                            dst = str(dst_dpid).zfill(16)
                            id = src + '->' + dst
                            self._ensure_resource('sdn_link', {
                                'id': id,
                                'src': src,
                                'dst': dst
                            })

                            measures.update({
                                id: {
                                    'delay': [{
                                        'timestamp': t,
                                        'value': delay
                                    }]
                                }
                            })

                        except Exception as e:
                            print(' *** ERROR in metrics._add_measures:',
                                  e.__class__.__name__, e)

                for src, delay in self._delay_monitor.delay.items():
                    try:
                        dst = str(self._simple_arp._in_ports[src][0]).zfill(16)
                        id = src + '->' + dst
                        self._ensure_resource('sdn_link', {
                            'id': id,
                            'src': src,
                            'dst': dst
                        })

                        measures.update({
                            id: {
                                'delay': [{
                                    'timestamp': t,
                                    'value': delay
                                }]
                            }
                        })

                        id = dst + '->' + src
                        self._ensure_resource('sdn_link', {
                            'id': id,
                            'src': dst,
                            'dst': src
                        })

                        measures.update({
                            id: {
                                'delay': [{
                                    'timestamp': t,
                                    'value': delay
                                }]
                            }
                        })

                    except Exception as e:
                        print(' *** ERROR in metrics._add_measures:',
                              e.__class__.__name__, e)

            except Exception as e:
                err = True
                print(' *** ERROR in metrics._add_measures:',
                      e.__class__.__name__, e)

            else:
                try:
                    self._client.metric.batch_resources_metrics_measures(
                        measures)

                except Exception as e:
                    err = True
                    print(' *** ERROR in metrics._add_measures:',
                          e.__class__.__name__, e)

            finally:
                if err:
                    sleep(1)
                else:
                    sleep(MONITOR_PERIOD)

    def _os_authenticate(self):
        self._session = Session(Password(auth_url=OS_URL + ':' + OS_AUTH_PORT,
                                         username=OS_USERNAME,
                                         password=OS_PASSWORD,
                                         user_domain_id=OS_USER_DOMAIN_ID,
                                         project_id=OS_PROJECT_ID))
        self._client = Client(1, self._session)

    def _os_ensure_resource_types(self):
        for type in RESOURCE_TYPES.values():
            try:
                self._client.resource_type.create(type['def'])
            except Conflict:
                pass

    def _os_ensure_metrics(self, resource_id: str, metrics: list, units: list):
        os_archive_policy = OS_ARCHIVE_POLICY
        if os_archive_policy not in self._archive_policies:
            print(' *** WARNING in metrics._os_ensure_metrics: '
                  'OPENSTACK:ARCHIVE_POLICY parameter invalid or missing from '
                  'conf.yml. Defaulting to ceilometer-low.')
            os_archive_policy = 'ceilometer-low'
        for i, name in enumerate(metrics):
            try:
                self._client.metric.create(
                    name=name, resource_id=resource_id, unit=units[i],
                    archive_policy_name=os_archive_policy)
            except Conflict:
                pass

    def _os_ensure_resource(self, resource_type: str, attributes: dict):
        attributes.update({
            'user_id': OS_USER_ID,
            'project_id': OS_PROJECT_ID
        })
        try:
            self._client.resource.create(resource_type, attributes)
        except NotFound:
            self._os_ensure_resource_types()
            self._client.resource.create(resource_type, attributes)
        except Conflict:
            pass

    def _ensure_resource(self, resource_type, attributes):
        self._os_ensure_resource(resource_type, attributes)
        self._os_ensure_metrics(attributes['id'],
                                RESOURCE_TYPES[resource_type]['metrics'],
                                RESOURCE_TYPES[resource_type]['units'])
