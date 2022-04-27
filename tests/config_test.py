import pytest
import RunSim

#============================ fixtures ==============================

EXPECTEDINOUT = [
    {
        'in': {
            'param1':                      [11,12,13],
            'param2':                      [21,22,23],
        },
        'out': [
            {
                'param1':                  11,
                'param2':                  21,
            },
            {
                'param1':                  11,
                'param2':                  22,
            },
            {
                'param1':                  11,
                'param2':                  23,
            },
            {
                'param1':                  12,
                'param2':                  21,
            },
            {
                'param1':                  12,
                'param2':                  22,
            },
            {
                'param1':                  12,
                'param2':                  23,
            },
            {
                'param1':                  13,
                'param2':                  21,
            },
            {
                'param1':                  13,
                'param2':                  22,
            },
            {
                'param1':                  13,
                'param2':                  23,
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
            'numberOfRuns':                 1,

        },
        'out': [
            {

                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",

            },
            {

                'numRobots':               10,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",

            },
            {

                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Atlas",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",

            },
            {

                'numRobots':               20,
                'floorplan':               "small_empty.txt",
                'initialPosition':         (1,1),
                'navigationAlgorithm':     "Ballistic",
                'relayAlgorithm':          "Recovery",
                'lowerPdrThreshold':       0.7,
                'upperPdrThreshold':       0.8,
                'propagationModel':        "PisterHack",

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