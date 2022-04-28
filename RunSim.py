# logging (do first)
import LoggingConfig
import logging.config
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)

# built-in
import argparse
import subprocess
import pkg_resources
import  itertools
import toml

# third-party
# local
import SimUI
import RunOneSim
from   Config import AtlasConfig

#============================ main ============================================
def allSimSettings(config):
    simSettings = []
    configItems = []
    seedCounter = 0
    configKeys = list(config.keys())

    for key in configKeys:
        configItems += [config[key] if type(config[key]) is list else [config[key]]]

    for run in range(config['numberOfRuns']):
        for configProduct in itertools.product(*configItems):
            simSetting   = {}
            seedCounter += 1
            simSetting['seed'] = seedCounter
            for idx,c in enumerate(configProduct):
                simSetting[configKeys[idx]] = c

            simSettings += [simSetting]

    return  simSettings

def main(configFile, cleps, noUI):
    configFileName = configFile

    config = AtlasConfig(configFile).atlas
    # create a list of settings, one per simulation run

    simSettings = allSimSettings(config)
    for idx,setting in enumerate(simSettings):
        simSettings[idx]['configFileName'] =  configFileName
        simSettings[idx]['floorplan']      = pkg_resources.resource_string('maps',
                                             simSettings[idx]['floorplan']).decode('utf-8')

    # create the UI
    simUI          = None if noUI else SimUI.SimUI()

    # run simulations, one run per simSetting
    for (runNum, simSetting) in enumerate(simSettings):
        if cleps:
            cmd    = ["sbatch", "--partition=cpu_homogen", "../scripts/atlas_submit_RunOneSim.sbatch", str(simSetting)]
            p      = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            RunOneSim.main(simSetting, simUI)

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--configfile", type=str, default="default", help="TOML configuration file")
    parser.add_argument("--cleps"     , help="running on the Inria CLEPS cluster")
    parser.add_argument("--noui"      , help="deactivate UI")

    args = parser.parse_args()

    main(args.configfile, args.cleps, args.noui)
