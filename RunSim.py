# logging (do first)
import os
import argparse

import pkg_resources
import AtlasLogging
import logging.config
logging.config.dictConfig(AtlasLogging.LOGGING_CONFIG)

# built-in
# third-party
# local
import SimUI
import time
import random
import subprocess, os, glob
import RunOneSim

from atlas.config import AtlasConfig

#============================ main ============================================


def main(config, mode):
    # ============================ defines =========================================

    SIMSETTINGS = []

    nav_config   = config.orchestrator.navigation
    seed_counter = 0

    # TODO: SimSettings should handle lack of certain parameters given a different configuration and maintains parameter cross product functionality
    # TODO: Have a validate configuration script that does an import dry run of all the configuration settings
    for idx, floorplan in enumerate(config.world.floorplans):
        for numrobot in config.world.robots.counts:
            for init_pos in config.world.robots.initial_positions:
                for wireless in config.wireless.models:
                    for propagation in config.wireless.propagation.models:
                        for nav in nav_config.models:
                            for relay in nav_config.relay.algorithms:
                                for path_planner in nav_config.path_planning.algorithms:
                                    for target_selector in nav_config.target_selector.algorithms:
                                        for lower_threshold in config.relays.thresholds.min_pdr_threshold:
                                            for upper_threshold in config.relays.thresholds.best_pdr_threshold:
                                                seed_counter += 1
                                                SIMSETTINGS.append(
                                                    {
                                                        'seed': seed_counter,
                                                        'config ID': config.experiment.configID ,
                                                        'numDotBots': numrobot,
                                                        'floorplanType': idx,
                                                        'floorplanDrawing': pkg_resources.resource_string('atlas.resources.maps',
                                                                                                       floorplan).decode('utf-8'),
                                                        'initialPosition': tuple(init_pos),
                                                        'navAlgorithm': nav,
                                                        'pathPlanner': path_planner,
                                                        'targetSelector': target_selector,
                                                        'wirelessModel': wireless,
                                                        'propagationModel': propagation,
                                                        'relaySettings': {'relayAlg': relay,
                                                                          'minPdrThreshold': lower_threshold,
                                                                          'bestPdrThreshold': upper_threshold}
                                                    },
                                                )
    

    print(SIMSETTINGS)
    # create the UI
    simUI          = SimUI.SimUI() if config.ui else None

    # run a number of simulations
    for (runNum, simSetting) in enumerate(SIMSETTINGS):
        if mode == "sequential processing":
            RunOneSim.main(simSetting, simUI)
        elif mode == "parallel processing":
            cmd = f'sbatch --cpus-per-task=1 --ntasks=1 st.py atlas_submit_RunOneSim.sh {simSetting} {simUI}'
            args = cmd.split(' ')
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=str, default="default", help="Atlas configuration file name to use (must be TOML)")
    parser.add_argument("--mode"  , type=str, default="sequential processing", help="sequential processing for single node or parallel processing for cluster")

    args = parser.parse_args()

    config = AtlasConfig(args.config)
    mode   = args.mode

    main(config.atlas, mode)
