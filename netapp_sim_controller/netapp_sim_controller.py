'''
    Main module of the NetAppSim controller. It can be launched through CLI or 
    used programmatically through the start(...) method. It launches the 
    RyuMain app using the 'ryu run' command (or 'ryu-manager' if not found) 
    with the --observe-links option. 
    
    --ofp-tcp-listen-port option can be specified by configuring the RYU:PORT 
    parameter in conf.yml.
'''


from os import getenv
from os.path import abspath, dirname, exists
from subprocess import run

import config


try:
    RYU_PORT = int(getenv('RYU_PORT', None))
except:
    print(' *** WARNING in server: RYU:PORT parameter invalid of missing from '
          'conf.yml. Defaulting to 6633.')
    RYU_PORT = 6633

try:
    RYU_API_PORT = int(getenv('RYU_API_PORT', None))
except:
    print(' *** WARNING in server: RYU:API_PORT parameter invalid of missing '
          'from conf.yml. Defaulting to 8080.')
    RYU_API_PORT = 8080

RYU_PATH = getenv('RYU_PATH', '')
RYU_BIN_PATH = RYU_PATH + '/bin/ryu'
RYU_MANAGER_PATH = RYU_PATH + '/bin/ryu-manager'
RYU_GUI_PATH = RYU_PATH + '/ryu/app/gui_topology/gui_topology.py'

RYU_MAIN_PATH = dirname(abspath(__file__)) + '/ryu_main.py'


def start():
    cmd = [RYU_BIN_PATH if exists(RYU_BIN_PATH) else 'ryu', 'run']
    if exists(RYU_GUI_PATH):
        cmd.append(RYU_GUI_PATH)
    else:
        print(' *** WARNING in server.serve:', RYU_GUI_PATH, 'not found. '
              'Make sure to configure RYU:PATH parameter in conf.yml')
    cmd.extend([RYU_MAIN_PATH, '--observe-links', '--ofp-tcp-listen-port',
                str(RYU_PORT), '--wsapi-port', str(RYU_API_PORT)])
    try:
        run(cmd)

    except FileNotFoundError:
        cmd[0] = (
            RYU_MANAGER_PATH if exists(RYU_MANAGER_PATH) else 'ryu-manager')
        del cmd[1]
        try:
            run(cmd)

        except FileNotFoundError:
            print(' *** ERROR in netapp_sim_controller.start: ryu and '
                  'ryu-manager not found. Make sure Ryu is installed and '
                  'added to system PATH. Or configure RYU:PATH parameter in '
                  'conf.yml if Ryu is installed from source.')

    except Exception as e:
        print(' *** ERROR in netapp_sim_controller.start:',
              e.__class__.__name__, e)


if __name__ == '__main__':
    start()
