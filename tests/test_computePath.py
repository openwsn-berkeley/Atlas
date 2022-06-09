import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # path with diagonal cells includes
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

    # path with diagonal cells excluded
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

def test_computePathWithoutObstacles(expectedInOut):
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator  = Orchestrator.Orchestrator(
        numRobots = 1,
        initX     = 1,
        initY     = 1
    )

    assert orchestrator._computePath(*expectedInOut['in'].values()) == expectedInOut['out']['path']

def test_computePathWithObstacles():
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator  = Orchestrator.Orchestrator(
        numRobots = 1,
        initX     = 1,
        initY     = 1
    )

    # check shortest path before obstacle
    assert (1.50, 1.50) in orchestrator._computePath((0.00, 0.00), (2.00, 2.00))

    # check shortest path after adding obstacle
    orchestrator.cellsObstacle += [(1.50, 1.50)]
    assert not (1.50, 1.50) in orchestrator._computePath((0.00, 0.00), (2.00, 2.00))