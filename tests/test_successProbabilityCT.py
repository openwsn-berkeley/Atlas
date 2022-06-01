
import pytest
import random
import Wireless

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'nodePdrs':   {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'D'
        },

        'out': 0.9549
    },
    {
        'in': {
            'nodePdrs': {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'C'
        },

        'out': 0.9702
    },
    {
        'in': {
            'nodePdrs': {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'B'
        },

        'out': 0.9805
    },


]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

#============================ tests =================================

def test_successProbabilityCT(expectedInOut):
    '''
    testing success probability given nodes and node total PDRs
    '''

    wireless = Wireless.Wireless()

    assert wireless._computeSuccessProbabilityCT(*expectedInOut['in'].values()) == expectedInOut['out']

def test_updateTreeCT():
    '''
    testing that CT build the correct tree out of any nodes given
    '''

    # moving node is last node in nodes
    # root node is first node in nodes

    wireless = Wireless.Wireless()
    wireless.lastRelays = []
    wireless.rootNode   = 'A'
    tree = wireless._updateTree(
        relays     = [ 'B'],
        movingNode = 'C',
        lastTree   = []
        )

    assert sorted(tree) == sorted([['A', 'C'], ['A', 'B', 'C']])

    wireless.lastRelays = ['B']
    wireless.rootNode = 'A'
    tree = wireless._updateTree(
        relays     = ['B','D'],
        movingNode ='F',
        lastTree   = [['A','C'], ['A', 'B', 'C']]
        )

    assert  sorted(tree) == sorted([['A', 'F'], ['A', 'B', 'F'], ['A', 'D', 'F'], ['A', 'B', 'D', 'F'], ['A', 'D', 'B', 'F']])

    wireless.lastRelays = []
    wireless.rootNode = 'A'
    tree = wireless._updateTree(
        relays     = ['B','D'],
        movingNode = 'F',
        lastTree   = []
        )

    assert  sorted(tree) == sorted([['A', 'F'], ['A', 'B', 'F'], ['A', 'D', 'F'], ['A', 'B', 'D', 'F'], ['A', 'D', 'B', 'F']])

    wireless.lastRelays = []
    wireless.rootNode = 'A'
    tree = wireless._updateTree(
        relays     = ['B','C','D'],
        movingNode = 'X',
        lastTree   = []
        )

    assert sorted(tree) == sorted([
        ['A', 'B', 'C', 'D', 'X'], ['A', 'B', 'C', 'X'], ['A', 'B', 'D', 'C', 'X'], ['A', 'B', 'D', 'X'], ['A', 'B', 'X'],
        ['A', 'C', 'B', 'D', 'X'], ['A', 'C', 'B', 'X'], ['A', 'C', 'D', 'B', 'X'], ['A', 'C', 'D', 'X'], ['A', 'C', 'X'],
        ['A', 'D', 'B', 'C', 'X'], ['A', 'D', 'B', 'X'], ['A', 'D', 'C', 'B', 'X'], ['A', 'D', 'C', 'X'], ['A', 'D', 'X'],
        ['A', 'X']
    ])



