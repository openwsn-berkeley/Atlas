import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'path':  [(1,1), (1.5, 0.5)],
            'x':       0.5,
            'y':       0.5,
        },
        'out': {
            'heading':  135,
            'speed':    1,
            'timeout':  1.06,
        }
    },
    {
        'in': {
            'path': [(1.5, 1), (2,1), (2.5, 1.5), (3,1)],
            'x':     1,
            'y':     1,
        },
        'out': {
            'heading': 101,
            'speed':   1,
            'timeout': 1.27,
        }
    },
    {
        'in': {
            'path':  [(3,1)],
            'x':       1,
            'y':       0,
        },
        'out': {
            'heading':  119,
            'speed':    1,
            'timeout':  2.57,
        }
    },
    {
        'in': {
            'path':   [(1, 1)],
            'x':        1.25,
            'y':        1,
        },
        'out': {
            'heading':  180,
            'speed':    1,
            'timeout':  0.25,
        }
    },


]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_computeHeadingSpeedTimeout(expectedInOut):

    orchestrator                     = Orchestrator.Orchestrator(1, 1, 1)
    inputs                           = expectedInOut['in']
    orchestrator.dotBotsView[1]['x'] = inputs['x']
    orchestrator.dotBotsView[1]['y'] = inputs['y']

    (heading, speed, timeout) = orchestrator._computeHeadingSpeedTimeout(dotBotId=1, path=inputs['path'])

    assert 0 <= heading <= 360
    assert round(heading, 0) == expectedInOut['out']['heading']
    assert round(timeout, 2) == expectedInOut['out']['timeout']
