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

def main(config, cleps):
    
    # create a list of settings, one per simulation run
    simSettings  = []
    seedCounter = 0
    for run in range(config.numberOfRuns):
        for idx, floorplanBlueprint in config.floorplanBlueprints:
            for communicationProtocol in config.communicationProtocols:
                for communicationModel in config.communicationModels:
                    for pathPlanningAlgorithm in config.pathPlanningAlgorithms:
                        for navigationAlgorithm in config.navigationAlgorithms:
                            for relayAlgorithm in config.relayAlgorithms:
                                for lowerPdrThreshold in config.lowerPdrThresholds:
                                    for upperPdrThreshold in config.upperPdrThresholds:
                                        for swarmSize in config.swarmSizes:
                                            for initialPosition in config.initialPositions:
                                                seedCounter += 1
                                                simSettings  += [{
                                                    'seed':                seedCounter,
                                                    'config ID':           config.configId ,
                                                    'floorplanBlueprint':  pkg_resources.resource_string(
                                                        'atlas.resources.maps',
                                                        floorplanBlueprint).decode('utf-8'),
                                                    'communicationProtocol': communicationProtocol,
                                                    'communicationModel': communicationModel,
                                                    'pathPlanningAlgorithm': pathPlanningAlgorithm,
                                                    'explorationAlgorithm': explorationAlgorithm,
                                                    'relayAlgorithm': relayAlgorithm,
                                                    'lowerPdrThreshold': lowerPdrThreshold,
                                                    'upperPdrThreshold': upperPdrThreshold,
                                                    'swarmSize': swarmSize,
                                                    'initialPosition': initialPosition,
                                                }]

    # create the UI
    simUI          = SimUI.SimUI() if config.ui else None

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

    args = parser.parse_args()

    config = AtlasConfig(args.configfile)

    main(config.atlas, args.cleps)
