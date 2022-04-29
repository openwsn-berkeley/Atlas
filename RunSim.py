# built-in
import argparse
import subprocess
import pkg_resources
import itertools
import toml
import json
import logging.config
# third-party
# local
import SimUI
import RunOneSim
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)

# setup logging
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
        simSetting['configfile']     =  configfile
        simSetting['floorplan']      = pkg_resources.resource_string('maps',
                                             simSetting['floorplan']).decode('utf-8')


    for simSetting in simSettings:
        if cleps:
            subprocess.Popen(["sbatch", "--partition=cpu_homogen", "../RunOneSim.sbatch", json.dumps(simSetting)],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            log.info('running on cleps ...')
        else:
            # create the UI
            simUI = None if noui else SimUI.SimUI()
            RunOneSim.runOneSim(simSetting, simUI)

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--configfile", type=str, default="default", help="TOML configuration file")
    parser.add_argument("--cleps",                                   help="running on the Inria CLEPS cluster")
    parser.add_argument("--noui",                                    help="deactivate UI")

    args = parser.parse_args()

    main(args.configfile, args.cleps, args.noui)
