# built-in
# third-party
# local

class Floorplan(object):
    '''
    The floorplan the DotBots move in.
    '''
    
    def __init__(self,drawing):
        pass
    
    #======================== public ==========================================
    
    def getJSON(self):
        return {
            'width':     50, # meters
            'height':    20, # meters
            'walls':     [
                [( 0, 0),(25, 1)],
                [(25,10),(26,20)],
            ],
        }
    
    #======================== private =========================================