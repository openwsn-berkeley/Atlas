import pytest
import RunSim

#============================ fixtures ==============================

EXPECTEDINOUT = [
    {
        'in': {
            'param1':                      [11,12,13],
            'param2':                      [21,22,23],
            'numberOfRuns':                1,              # required
        },
        'out': [
            {
                'seed':                    1,              # normal
                'param1':                  11,
                'param2':                  21,
                'numberOfRuns':            1,
            },
            {
                'seed':                    2,
                'param1':                  11,
                'param2':                  22,
                'numberOfRuns':            1,
            },
            {
                'seed':                    3,
                'param1':                  11,
                'param2':                  23,
                'numberOfRuns':            1,
            },
            {
                'seed':                    4,
                'param1':                  12,
                'param2':                  21,
                'numberOfRuns':            1,
            },
            {
                'seed':                    5,
                'param1':                  12,
                'param2':                  22,
                'numberOfRuns':            1,
            },
            {
                'seed':                    6,
                'param1':                  12,
                'param2':                  23,
                'numberOfRuns':            1,
            },
            {
                'seed':                    7,
                'param1':                  13,
                'param2':                  21,
                'numberOfRuns':            1,
            },
            {
                'seed':                    8,
                'param1':                  13,
                'param2':                  22,
                'numberOfRuns':            1,
            },
            {
                'seed':                    9,
                'param1':                  13,
                'param2':                  23,
                'numberOfRuns':            1,
            },
        ],
    },
    {
        'in': {
            'numRobots':                   [10,20],
            'floorplan':                   ["small_empty.txt"],
            'initialPosition':             [(1,1)],
            'navigationAlgorithm':         ["Atlas","Ballistic"],
            'relayAlgorithm':              ["Recovery"],
            'lowerPdrThreshold':           [0.7],
            'upperPdrThreshold':           [0.8],
            'propagationModel':            ["PisterHack"],
            'numberOfRuns':                1,                       # required

        },
        'out': [
            {
                'seed':                    1,                       # normal
                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    2,
                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    3,
                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    4,
                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
        ],
    },
    {
        'in': {
            'numRobots':                   [10,20],
            'floorplan':                   "small_empty.txt",
            'initialPosition':             (1,1),
            'navigationAlgorithm':         ["Atlas","Ballistic"],
            'relayAlgorithm':              "Recovery",
            'lowerPdrThreshold':           0.7,
            'upperPdrThreshold':           0.8,
            'propagationModel':            "PisterHack",
            'numberOfRuns':                1,                     # required

        },
        'out': [
            {
                'seed':                    1,                       # normal
                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    2,
                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    3,
                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
            {
                'seed':                    4,
                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",
                'numberOfRuns':            1,

            },
        ],
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

#============================ tests =================================

def test_allSimSettings(expectedInOut):
    assert RunSim.allSimSettings(expectedInOut['in'])==expectedInOut['out']