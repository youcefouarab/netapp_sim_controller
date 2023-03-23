from os import getenv

import config


# =====================
#     RYU APP NAMES
#  =====================


SIMPLE_ARP = 'simple_arp'
NETWORK_MONITOR = 'network_monitor'
NETWORK_DELAY_DETECTOR = 'network_delay_detector'
DELAY_MONITOR = 'delay_monitor'


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
