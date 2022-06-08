# built-in
import argparse
import subprocess
import pkg_resources
import itertools
import toml
import json
# third-party
# local
import AtlasUI
import RunOneSim

# setup logging
import logging.config
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)
log = logging.getLogger('RunSim')

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

def main(configfile, cleps, noui):
    # log
    log.info(f'RunSim starting ...')

    # create a list of simSettings, one per simulation run
    simSettings = allSimSettings(
    toml.load(pkg_resources.resource_filename(__name__, f"configs/{configfile}.toml"))['atlas'])

    # run simulations, one run per simSetting
    for (idx,simSetting) in enumerate(simSettings):
        simSetting['floorplan']      = pkg_resources.resource_string('floorplans', simSetting['floorplan']).decode('utf-8')
        simSetting['uname']          = "{}_{}".format(configfile, simSetting['seed'])

    # create the UI
    atlasUI = None if noui else AtlasUI.AtlasUI()

    for simSetting in simSettings:
        if cleps:
            simSetting = json.dumps(simSetting)
            subprocess.Popen(["sbatch", "../RunOneSim.sbatch", simSetting])
        else:
            RunOneSim.runOneSim(simSetting, atlasUI)

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--configfile", type=str, default="default", help="TOML configuration file")
    parser.add_argument("--cleps",                                   help="running on the Inria CLEPS cluster")
    parser.add_argument("--noui",                                    help="deactivate UI")

    args = parser.parse_args()

    main(args.configfile, args.cleps, args.noui)
