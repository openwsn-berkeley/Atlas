# logging (do first)
import LoggingConfig
import logging.config
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)

# built-in
import argparse
import subprocess
import pkg_resources
# third-party
# local
import SimUI
import RunOneSim
from   atlas.config import AtlasConfig

#============================ main ============================================

def main(configFile, cleps, simUI):
    configFileName = configFile
    config = AtlasConfig(configFile).atlas
    #config = config.atlas
    
    # create a list of settings, one per simulation run
    simSettings  = []
    seedCounter = 0
    for numRobots in config.numRobots:
        for floorplan in config.floorplan:
            for initialPosition in config.initialPosition:
                for navigationAlgorithm in config.navigationAlgorithm:
                    for relayAlgorithm in config.relayAlgorithm:
                        for lowerPdrThreshold in config.lowerPdrThreshold:
                            for upperPdrThreshold in config.upperPdrThreshold:
                                for propagationModel in config.propagationModel:
                                    for run in range(config.numberOfRuns):
                                        seedCounter += 1
                                        simSettings  += [{
                                            'configFileName':       configFileName,
                                            'seed':                 seedCounter,
                                            'numRobots':            numRobots,
                                            'floorplan':            pkg_resources.resource_string(
                                                'atlas.resources.maps',
                                                floorplan).decode('utf-8'),
                                            'initialPosition':       initialPosition,
                                            'navigationAlgorithm':   navigationAlgorithm,
                                            'relayAlgorithm':        relayAlgorithm,
                                            'lowerPdrThreshold':     lowerPdrThreshold,
                                            'upperPdrThreshold':     upperPdrThreshold,
                                            'propagationModel':      propagationModel,

                                        }]

    # create the UI
    simUI          = SimUI.SimUI() if not simUI else None

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
    parser.add_argument("--noUI"      , help="deactivate UI")

    args = parser.parse_args()

    main(args.configfile, args.cleps, args.noUI)
