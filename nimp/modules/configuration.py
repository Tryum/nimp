# -*- coding: utf-8 -*-

import argparse
import time

from    nimp.modules.module          import *

from    nimp.utilities.logging       import *
from    nimp.utilities.paths         import *

#-------------------------------------------------------------------------------
class ConfigurationModule(Module):
    #---------------------------------------------------------------------------
    def __init__(self):
        Module.__init__(self, "configuration", [])

    #---------------------------------------------------------------------------
    def configure_arguments(self, env, parser):
        log_group = parser.add_argument_group("Configuration")

        return True

    #---------------------------------------------------------------------------
    def load(self, env):
        parser      = argparse.ArgumentParser(formatter_class=argparse.HelpFormatter)
        return _load_settings(env) and _load_arguments(env, parser)

#---------------------------------------------------------------------------
def _load_settings(env):
    conf_dirs = []
    while os.path.abspath(os.sep) != os.getcwd():
        if os.path.exists(".nimp.conf"):
            break
        os.chdir("..")

    if not os.path.isfile(".nimp.conf"):
        log_error("Unable to find a .nimp.conf config file in current or parents directories.")
        return False

    if not env.load_config_file(".nimp.conf"):
        log_error("Error loading .nimp.conf.")
        return False

    return True

#---------------------------------------------------------------------------
def _load_config_dir(env, conf_dir):
    conf_files = list(glob.glob("%s/*.conf" % conf_dir))
    conf_files.sort()
    for file in conf_files:
        if not env.load_config_file(file):
            return False

def _load_arguments(env, parser):
    modules     = env.modules

    for module in modules:
        if hasattr(module, "configure_arguments"):
            if( not module.configure_arguments(env, parser)):
                return False

    (arguments, unknown_args) = parser.parse_known_args()
    setattr(env, "unknown_args", unknown_args)

    for key, value in vars(arguments).items():
        setattr(env, key, value)

    env.standardize_names()
    return True
