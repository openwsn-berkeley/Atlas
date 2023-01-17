import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # path with diagonal cells includes
    {
        'in': {
            'startCell':             (0.00, 0.00),
            'targetCell':            (2.00, 2.00),
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

def test_computePathWithoutObstacles(expectedInOut):
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator         = Orchestrator.Orchestrator(
        numRobots        = 1,
        orchX            = 1,
        orchY            = 1,
        initialPositions = [(1,1)]
    )
    orchestrator.cellsExplored = [(0.50, 0.50), (1.00, 1.00), (1.50, 1.50), (2.00, 2.00), (0.50, 0.00),
                                  (1.00, 0.50), (1.50, 1.00), (2.00, 1.50)]
    assert orchestrator._computePath(*expectedInOut['in'].values()) == expectedInOut['out']['path']

def test_computePathWithObstacles():
    '''
    testing finding path between two cells using A* algorithm
    '''

    orchestrator         = Orchestrator.Orchestrator(
        numRobots        = 1,
        orchX            = 1,
        orchY            = 1,
        initialPositions = [(1,1)]
    )

    orchestrator.cellsExplored = [(0.00, 0.00), (0.50, 0.00), (1.00, 0.00), (1.50, 0.00), (2.00, 0.00),
                                  (0.00, 0.50), (0.50, 0.50), (1.00, 0.50), (1.50, 0.50), (2.00, 0.50),
                                  (0.00, 1.00), (0.10, 0.00), (1.00, 1.00), (1.50, 1.00), (2.00, 1.00),
                                  (0.00, 1.50), (0.10, 0.50), (1.00, 1.50), (1.50, 1.50), (2.00, 1.50),
                                  (0.00, 2.00), (0.10, 2.00), (1.00, 2.00), (1.50, 2.00), (2.00, 2.00)]

    # check shortest path before obstacle
    assert (1.50, 1.50) in orchestrator._computePath((0.00, 0.00), (2.00, 2.00))
    print(orchestrator._computePath((0.00, 0.00), (2.00, 2.00)))

    # check shortest path after adding obstacle
    orchestrator.cellsObstacle += [(1.50, 1.50)]

    assert not (1.50, 1.50) in orchestrator._computePath((0.00, 0.00), (2.00, 2.00))
