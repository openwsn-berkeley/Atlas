import DotBot
import Floorplan
import pytest
import random

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # diagonally towards obstacle (left to right)
    {
        'in': {
            'currentX': 0.00,
            'currentY': 0.00,
            'heading':  135.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (1.00, 1.00,  1.414213562373095)
    },

    # diagonally away from obstacle (left to right)
    {
        'in': {
            'currentX': 2.00,
            'currentY': 2.00,
            'heading':  135.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (None, None, None)
    },

    # diagonally towards obstacle (right to left)
    {
        'in': {
            'currentX': 3.00,
            'currentY': 0.00,
            'heading':  225.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (2.00, 1.00,   1.4142135623730951)
    },

    # diagonally away from obstacle (right to left)
    {
        'in': {
            'currentX': 1.00,
            'currentY': 2.00,
            'heading':  255.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (None, None, None)
    },

    # vertically towards obstacle
    {
        'in': {
            'currentX': 1.50,
            'currentY': 0.00,
            'heading':  180.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (1.50, 1.00, 1.00)
    },

    # vertically away from obstacle
    {
        'in': {
            'currentX': 1.50,
            'currentY': 2.00,
            'heading':  180.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (None, None, None)
    },

    # horizontally towards obstacle
    {
        'in': {
            'currentX': 0.00,
            'currentY': 1.50,
            'heading':  90.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (1.00, 1.50, 1.00)
    },

    # current position on obstacle and moving towards obstacle
    {
        'in': {
            'currentX': 1.00,
            'currentY': 1.50,
            'heading':  90.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x': 1.00,
                    'y': 1.00,
                    'width': 1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (1.00, 1.50, 0)
    },

    # horizontally away from obstacle
    {
        'in': {
            'currentX': 2.00,
            'currentY': 1.50,
            'heading':  90.00,
            'speed':    1.00,
            'obstacles': [
                {
                    'x':      1.00,
                    'y':      1.00,
                    'width':  1.00,
                    'height': 1.00,
                }
            ]
        },

        # (bumpX, bumpY, bumpTime)
        'out': (None, None, None)
    },

    # horizontally towards 2 obstacles
    {
        'in': {
            'currentX': 0.00,
            'currentY': 1.50,
            'heading':  90.00,
            'speed':    1.00,
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

        # (bumpX, bumpY, bumpTime)
        'out': (1.00, 1.50, 1.00)
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
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
    dotBot = DotBot.DotBot(1,0,0, floorplan)
    assert dotBot._computeNextBump(*expectedInOut['in'].values()) == expectedInOut['out']

def test_intersectionPointsExist():
    floorplan = '''
#####
#...#
#.s.#
#...#
#####
    '''
    floorplan = Floorplan.Floorplan(floorplan)
    dotBot = DotBot.DotBot(1,0,0, floorplan)
    for i in range(100):
        assert dotBot._computeNextBump(floorplan.initX, floorplan.initY, (360 * random.random()), 1, floorplan.obstacles) != (None, None, None)
