'''
    Loads conf.yml parameters as environment variables.
'''


from os import environ
from os.path import dirname, abspath
from yaml import safe_load


ROOT_PATH = dirname(dirname(abspath(__file__)))
CONF = ROOT_PATH + '/conf.yml'


try:
    with open(CONF, 'r') as f:
        config = safe_load(f)
        for sect in config:
            for param in config[sect]:
                if config[sect][param] != None:
                    environ[sect + '_' + param] = str(config[sect][param])
except Exception as e:
    print(' *** ERROR in config:', e.__class__.__name__, e)
    exit()
