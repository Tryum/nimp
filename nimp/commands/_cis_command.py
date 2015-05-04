# -*- coding: utf-8 -*-

from nimp.commands._command      import *
from nimp.utilities.perforce     import *

FARM_P4_PORT     = "192.168.1.2:1666"
FARM_P4_USER     = "CIS-CodeBuilder"
FARM_P4_PASSWORD = "CIS-CodeBuilder"

#-------------------------------------------------------------------------------
class CisCommand(Command):
    abstract = 1 # Vieux hackos pour que l'introspection n'instancie pas cette
                 # classe, on pourrait checker que le module ne commence pas par _

    #-------------------------------------------------------------------------
    def __init__(self, name, description):
        Command.__init__(self, name, description)

    #---------------------------------------------------------------------------
    def configure_arguments(self, env, parser):
        parser.add_argument('p4_client',
                            metavar = '<CLIENT_NAME>',
                            type    = str)

        parser.add_argument('--local',
                            help    = "Don't touch workspace or P4 settings.",
                            action  = "store_true",
                            default = False)

        parser.add_argument('--hard-clean',
                            help    = 'Remove all unversionned files',
                            action  = "store_true",
                            default = False)

        return self.cis_configure_arguments(env, parser)

    #---------------------------------------------------------------------------
    def cis_configure_arguments(self, env, parser):
        return False

    #---------------------------------------------------------------------------
    def run(self, env):
        if not env.local:
            if not p4_create_config_file(FARM_P4_PORT, FARM_P4_USER, FARM_P4_PASSWORD, env.p4_client):
                return False

            if not p4_clean_workspace():
                return False

        result = self._cis_run(env)

        if not env.local:
            p4_clean_workspace()

        return result

    def _cis_run(self, env):
        return False
