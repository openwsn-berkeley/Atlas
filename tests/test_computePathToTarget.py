import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'startCell':   (0.00, 0.00),
            'targetCell':  (2.00, 2.00),
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

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_computePathToTargetNoObstacles(expectedInOut):
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    orchestrator.MINFEATURESIZE = 1

    assert orchestrator._computePathToTarget(*expectedInOut['in'].values()) == expectedInOut['out']['path']

def test_computePathToTargetWithObstacles():
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    orchestrator.MINFEATURESIZE = 1

    # check shortest path before obstacle
    assert (1.50, 1.50) in orchestrator._computePathToTarget((0.00, 0.00),(2.00, 2.00))

    # check shortest path after adding obstacle
    orchestrator.cellsObstacle += [(1.50, 1.50)]
    assert not (1.50, 1.50) in orchestrator._computePathToTarget((0.00, 0.00),(2.00, 2.00))