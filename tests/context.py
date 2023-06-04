from sys import path
from os.path import abspath, join, dirname


path.insert(0, abspath(join(dirname(__file__), '..')))


import netapp_sim_controller.config as config