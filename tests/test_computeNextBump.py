import DotBot
import Floorplan
import pytest
import random

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # diagonally towards obstacle (left to right)
    {
        'in': {
            'currentX':   0.00,
            'currentY':   0.00,
            'heading':  135.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },


        'out': {
            'bumpX':      1.00,
            'bumpY':      1.00,
            'timetobump': 1.414213562373095
        }
    },

    # diagonally away from obstacle (left to right)
    {
        'in': {
            'currentX':   2.00,
            'currentY':   2.00,
            'heading':  135.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      None,
            'bumpY':      None,
            'timetobump': None
        }
    },

    # diagonally towards obstacle (right to left)
    {
        'in': {
            'currentX':   3.00,
            'currentY':   0.00,
            'heading':  225.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      2.00,
            'bumpY':      1.00,
            'timetobump': 1.4142135623730951
        }
    },

    # diagonally away from obstacle (right to left)
    {
        'in': {
            'currentX':   1.00,
            'currentY':   2.00,
            'heading':  255.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      None,
            'bumpY':      None,
            'timetobump': None
        }
    },

    # vertically towards obstacle
    {
        'in': {
            'currentX':   1.50,
            'currentY':   0.00,
            'heading':  180.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      1.50,
            'bumpY':      1.00,
            'timetobump': 1.00
        }
    },

    # vertically away from obstacle
    {
        'in': {
            'currentX':   1.50,
            'currentY':   2.00,
            'heading':  180.00,
            'speed':      1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      None,
            'bumpY':      None,
            'timetobump': None,
        }
    },

    # horizontally towards obstacle
    {
        'in': {
            'currentX':  0.00,
            'currentY':  1.50,
            'heading':  90.00,
            'speed':     1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      1.00,
            'bumpY':      1.50,
            'timetobump': 1.00,
        }
    },

    # current position on obstacle and moving towards obstacle
    {
        'in': {
            'currentX':  1.00,
            'currentY':  1.50,
            'heading':  90.00,
            'speed':     1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      1.00,
            'bumpY':      1.50,
            'timetobump': 0.00,
        }
    },

    # horizontally away from obstacle
    {
        'in': {
            'currentX':  2.00,
            'currentY':  1.50,
            'heading':  90.00,
            'speed':     1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        'out': {
            'bumpX':      None,
            'bumpY':      None,
            'timetobump': None,
        }
    },

    # horizontally towards 2 obstacles
    {
        'in': {
            'currentX':  0.00,
            'currentY':  1.50,
            'heading':  90.00,
            'speed':     1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                },
                {
                    'x':      1.00,
                    'y':      3.00,
                    'width':  1.00,
                    'height': 1.00,
                }

            ]
        },

        'out': {
            'bumpX':      1.00,
            'bumpY':      1.50,
            'timetobump': 1.00,
        }
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

RANDOMANGLES = [360 * random.random() for i in range(1000)]

@pytest.fixture(params=RANDOMANGLES)
def randomAngle(request):
    return request.param

# ============================ tests =================================

def test_computeNextBump(expectedInOut):
    '''
    testing computation of next bump with obstacle coordinates and time
    '''

    floorplan = '''
        ######
        #...s#
        ######
    '''
    dotBot = DotBot.DotBot(
        dotBotId  = 1,
        x         = 0,
        y         = 0,
        floorplan = floorplan
    )

    assert dotBot._computeNextBump(*expectedInOut['in'].values()) == tuple(expectedInOut['out'].values())

def test_intersectionPointsExist(randomAngle):
    floorplan  = '''
#####
#...#
#.s.#
#...#
#####
    '''
    floorplan  = Floorplan.Floorplan(floorplan)

    dotBot     = DotBot.DotBot(
        dotBotId  = 1,
        x         = 0,
        y         = 0,
        floorplan = floorplan
    )

    assert dotBot._computeNextBump(floorplan.initX, floorplan.initY, randomAngle, 1, floorplan.obstacles) != (None, None, None)
