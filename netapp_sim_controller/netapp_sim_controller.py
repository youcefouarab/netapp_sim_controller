'''
    Main module of NetApp Sim controller. Can be launched through CLI or used 
    programmatically through start() method.

    Launches RyuMain app using 'ryu run' command (or 'ryu-manager' if not 
    found) with --observe-links option. --ofp-tcp-listen-port option can be 
    specified by configuring RYU:PORT parameter in conf.yml.
'''


from os import getenv
from os.path import abspath, dirname, exists
from subprocess import run

import config


try:
    RYU_PORT = int(getenv('RYU_PORT', None))
except:
    print(' *** WARNING in netapp_sim_controller: '
          'RYU:PORT paramter invalid of missing from conf.yml. '
          'Defaulting to 6633.')
    RYU_PORT = 6633
RYU_PATH = getenv('RYU_PATH', '')
RYU_BIN_PATH = RYU_PATH + '/bin/ryu'
RYU_MANAGER_PATH = RYU_PATH + '/bin/ryu-manager'
RYU_MAIN_PATH = dirname(abspath(__file__)) + '/ryu_main.py'


def start():
    cmd = [RYU_BIN_PATH if exists(RYU_BIN_PATH) else 'ryu', 'run',
           RYU_MAIN_PATH, '--observe-links']
    if RYU_PORT != None:
        cmd.extend(['--ofp-tcp-listen-port', str(RYU_PORT)])
    try:
        run(cmd)

    except FileNotFoundError:
        cmd[0] = (
            RYU_MANAGER_PATH if exists(RYU_MANAGER_PATH) else 'ryu-manager')
        del cmd[1]
        try:
            run(cmd)

        except FileNotFoundError:
            print(' *** ERROR in netapp_sim_controller.start: '
                  'ryu and ryu-manager not found. Make sure Ryu is installed '
                  'and added to system PATH. Or configure RYU:PATH parameter '
                  'in conf.yml if Ryu is installed from source.')

    except Exception as e:
        print(' *** ERROR in netapp_sim_controller.start:',
              e.__class__.__name__, e)


if __name__ == '__main__':
    start()
