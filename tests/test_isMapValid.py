import Floorplan
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # full border
    {
        'in': {
            'drawing':
                '''
                ######
                #....#
                #s...#
                ######
                '''
        },
        'out': True
    },

    # incomplete border
    {
        'in': {
            'drawing':
                '''
                ######
                #....#
                #s....
                ######
                '''
        },
        'out': False
    },

    # border not exact square or rectangle
    {
        'in': {
            'drawing':
                '''
                ######...
                #....####
                #...s...#
                #########
                '''
        },
        'out': True
    },

    # missing starting position
    {
        'in': {
            'drawing':
                '''
                ######
                #....#
                #.....
                ######
                '''
        },
        'out': False
    },

    # invalid character b
    {
        'in': {
            'drawing':
                '''
                ######
                #....#
                #..b.#
                ######
                '''
        },
        'out': False
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_isMapValid(expectedInOut):
    '''
    testing if map given to floorplan is valid
    aka. has borders and valid characters (#,., s)
    '''

    defaultDrawing = '''
        ######
        #...s#
        ######
    '''
    floorplan = Floorplan.Floorplan(defaultDrawing)

    assert floorplan._isMapValid(*expectedInOut['in'].values()) == expectedInOut['out']


