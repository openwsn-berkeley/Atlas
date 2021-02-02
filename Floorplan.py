# built-in
# third-party
# local

class Floorplan(object):
    '''
    The floorplan the DotBots move in.
    '''
    
    def __init__(self,drawing):
    
        # local variables
        (self.width,self.height,self.obstacles) = self._parseDrawing(drawing)
        (self.overlayWidth, self.overlayHeight, self.overlayCells) = self._generateOverlay(drawing)
    
    #======================== public ==========================================
    
    def getJSON(self):
        return {
            'width':     self.width,
            'height':    self.height,
            'obstacles': self.obstacles,
        }
    
    #======================== private =========================================
    
    def _parseDrawing(self,drawing):
        lines     = [line for line in drawing.splitlines() if line]
        width     = max([len(line) for line in lines])
        height    = len(lines)
        obstacles = []
        for (y,line) in enumerate(lines):
            for (x,c) in enumerate(line):
                if c=='#':
                    obstacles += [{'x': x, 'y':  y, 'width': 1, 'height': 1}]
        return (width,height,obstacles)

    def _generateOverlay(self, drawing):
        '''
        create overlay grid of 0.5 x 0.5 m^2 for frontier navigation algorithms
        '''
        width = self.width
        height = self.height
        cell_width = 0.5
        cell_height = 0.5
        #print('w',width,'h',height)
        cells = []
        for y in [y*0.5 for y in range(0, height*2)]:
            for x in [x*0.5 for x in range(0, width*2)]:
                cells += [(x,y)]
        #-----------------------debug prints - remove later--------------------------
        #print(len(cells))
        #print(cells)
        return (cell_width,cell_height,cells)





