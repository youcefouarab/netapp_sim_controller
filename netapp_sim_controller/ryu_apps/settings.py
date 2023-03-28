from os import getenv

import config


# =====================
#     RYU APP NAMES
#  =====================


SIMPLE_ARP = 'simple_arp'
NETWORK_MONITOR = 'network_monitor'
NETWORK_DELAY_DETECTOR = 'network_delay_detector'
DELAY_MONITOR = 'delay_monitor'
METRICS = 'metrics'


# ==============
#      CONFIG
# ==============


CONTROLLER_MAC = getenv('NETWORK_CONTROLLER_MAC', None)
if CONTROLLER_MAC == None:
    print(' *** ERROR in settings: '
          'NETWORK:CONTROLLER_MAC parameter missing from conf.yml.')
    exit()

CONTROLLER_IP = getenv('NETWORK_CONTROLLER_IP', None)
if CONTROLLER_IP == None:
    print(' *** ERROR in settings: '
          'NETWORK:CONTROLLER_IP parameter missing from conf.yml.')
    exit()

try:
    ARP_REFRESH = float(getenv('NETWORK_ARP_REFRESH', None))
except:
    print(' *** WARNING in settings: '
          'NETWORK:ARP_REFRESH parameter missing from conf.yml. '
          'Defaulting to 1 minute.')
    ARP_REFRESH = 60

IP_POOL = getenv('NETWORK_IP_POOL', '')
if not IP_POOL:
    print(' *** WARNING in settings: '
          'NETWORK:IP_POOL parameter missing from conf.yml. '
          'Defaulting to empty IP address pool.')

try:
    MONITOR_PERIOD = float(getenv('MONITOR_PERIOD', None))
except:
    print(' *** WARNING in settings: '
          'MONITOR:PERIOD parameter invalid or missing from conf.yml. '
          'Defaulting to 2 seconds.')
    MONITOR_PERIOD = 2

OS_URL = getenv('OPENSTACK_URL', '')
if not OS_URL:
    print(' *** WARNING in settings: '
          'OPENSTACK:URL parameter missing from conf.yml.')

OS_AUTH_PORT = getenv('OPENSTACK_AUTH_PORT', '')
if not OS_AUTH_PORT:
    print(' *** WARNING in settings: '
          'OPENSTACK:AUTH_PORT parameter missing from conf.yml.')

OS_GNOCCHI_PORT = getenv('OPENSTACK_GNOCCHI_PORT', '')
if not OS_GNOCCHI_PORT:
    print(' *** WARNING in settings: '
          'OPENSTACK:GNOCCHI_PORT parameter missing from conf.yml.')

OS_USERNAME = getenv('OPENSTACK_USERNAME', '')
if not OS_USERNAME:
    print(' *** WARNING in settings: '
          'OPENSTACK:USERNAME parameter missing from conf.yml.')

OS_PASSWORD = getenv('OPENSTACK_PASSWORD', '')
if not OS_PASSWORD:
    print(' *** WARNING in settings: '
          'OPENSTACK:PASSWORD parameter missing from conf.yml.')

OS_USER_DOMAIN_ID = getenv('OPENSTACK_USER_DOMAIN_ID', '')
if not OS_USER_DOMAIN_ID:
    print(' *** WARNING in settings: '
          'OPENSTACK:USER_DOMAIN_ID parameter missing from conf.yml.')

OS_USER_ID = getenv('OPENSTACK_USER_ID', '')
if not OS_USER_ID:
    print(' *** WARNING in settings: '
          'OPENSTACK:USER_ID parameter missing from conf.yml.')

OS_PROJECT_ID = getenv('OPENSTACK_PROJECT_ID', '')
if not OS_PROJECT_ID:
    print(' *** WARNING in settings: '
          'OPENSTACK:PROJECT_ID parameter missing from conf.yml.')

OS_ARCHIVE_POLICY = getenv('OPENSTACK_ARCHIVE_POLICY', '')
