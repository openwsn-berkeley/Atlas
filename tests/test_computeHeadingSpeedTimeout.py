import Orchestrator
import pytest
import random
# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'startCell':             (0.00, 0.00),
            'targetCell':            (2.00, 2.00),
            'excludeDiagonalCells' : False
        },
        'out': {
            'path': [
                (0.50, 0.50),
                (1.00, 1.00),
                (1.50, 1.50),
                (2.00, 2.00)
            ],
        },
    },
    {
        'in': {
            'startCell':            (0.00, 0.00),
            'targetCell':           (2.00, 2.00),
            'excludeDiagonalCells': True
        },
        'out': {
            'path': [
                (0.50, 0.00),
                (0.50, 0.50),
                (1.00, 0.50),
                (1.00, 1.00),
                (1.50, 1.00),
                (1.50, 1.50),
                (2.00, 1.50),
                (2.00, 2.00)
            ],
        },
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_headingCalculationObstacles():

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    orchestrator.MINFEATURESIZE = 1

    path = [(1,1), (1.5, 0.5)]

    orchestrator.dotBotsView[1]['x'] = 0.5
    orchestrator.dotBotsView[1]['y'] = 0.5

    (heading, speed, timeout) = orchestrator._computeHeadingSpeedTimeout(path, 1)

    assert 0 <= heading <= 360
    assert round(heading, 2) == 135
    assert round(timeout, 2) == 1.06

def test_headingCalculationWithTurn():

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    orchestrator.MINFEATURESIZE = 1

    path = [(1.5, 1), (2,1), (2.5, 1.5), (3,1)]

    orchestrator.dotBotsView[1]['x'] = 1
    orchestrator.dotBotsView[1]['y'] = 1

    (heading, speed, timeout) = orchestrator._computeHeadingSpeedTimeout(path, 1)

    assert 0 <= heading <= 360
    assert round(heading, 2) == 101.31
    assert round(timeout, 2) == 1.27

def test_headingCalculationOneCellPath():

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    orchestrator.MINFEATURESIZE = 1

    path = [(3,1)]

    orchestrator.dotBotsView[1]['x'] = 1
    orchestrator.dotBotsView[1]['y'] = 0

    (heading, speed, timeout) = orchestrator._computeHeadingSpeedTimeout(path, 1)

    assert 0 <= heading <= 360
    assert round(heading, 0) == 119
    assert round(timeout, 2) == 2.57