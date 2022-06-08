# built-in
import pkg_resources
# third-party
# local

class Floorplan(object):
    '''
    The floorplan the DotBots move in.
    '''
    
    def __init__(self, drawing, alias=None):

        if alias:
            drawing = pkg_resources.resource_string('floorplans', f'{alias}.txt').decode('utf-8')

        assert self._isMapValid(drawing)

        (self.width, self.height, self.obstacles, self.initX, self.initY) = self._parseDrawing(drawing)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            drawing = f.read()

        return cls(drawing)
    
    #======================== public ==========================================
    
    def getJSON(self):
        return {
            'width':     self.width,
            'height':    self.height,
            'obstacles': self.obstacles,
        }

    def getInitialPosition(self):
        return (self.initX, self.initY)

    #======================== static =========================================

    @staticmethod
    def _parseDrawing(drawing):
        lines     = [line for line in drawing.splitlines() if line]
        width     = max([len(line) for line in lines])
        height    = len(lines)
        obstacles = []
        for (y, line) in enumerate(lines):
            for (x, c) in enumerate(line):
                if c == '#':
                    obstacles += [{'x': x, 'y':  y, 'width': 1, 'height': 1}]
                if c == 's':
                    (initX, initY) = (x,y)
        return (width, height, obstacles, initX, initY)

    def _isMapValid(self, drawing):
        '''
        checks if map given to floorplan is valid
        aka. has borders and valid characters (#,., s)
        example input - output :
            {
            'in': {
                'drawing':
                    \'''
                    ########
                    #...s..#
                    ########
                    \'''
            },
            'out': False
        },
        '''

        returnVal       = True

        # split drawing into matrix of character positions (cells) indexed by row, column indices
        matrixOfCells   = [line for line in drawing.splitlines()]
        cellsChecked    = []     # cells in map of which surrounding frontiers have been determined
        cellsToCheck    = []     # cells in map of which surrounding frontiers are to be determined

        # if there is no starting position character 's' map is invalid
        try:
            startPos    = [(lidx,line.index('s')) for (lidx,line) in enumerate(matrixOfCells) if 's' in line][0]
        except IndexError:
            startPos    = None
            returnVal   = False

        cellsToCheck   += [startPos]

        # keep looping until there are no more froniters (all borders have been found)
        while cellsToCheck and startPos:

            (cellRow,cellCol) = cellsToCheck.pop(0)
            cellsChecked     += [(cellRow,cellCol)]

            # set surrounding 8 cells as frontiers to check next if they are not obstacles
            neighbourCells    = [
                (cellRow+1,  cellCol  ), (cellRow-1,  cellCol  ),
                (cellRow,    cellCol-1), (cellRow,    cellCol+1),
                (cellRow-1,  cellCol-1), (cellRow+1,  cellCol+1),
                (cellRow-1,  cellCol+1), (cellRow+1,  cellCol-1)
            ]

            for nx, ny in neighbourCells:
                
                try:
                    # if drawing contains characters that aren't '#,.,s' map is invalid
                    assert matrixOfCells[nx][ny] == '#' or matrixOfCells[nx][ny] == '.' or matrixOfCells[nx][ny] == 's'

                    # if next frontier position is not in matrix of characters map is invalid
                    if matrixOfCells[nx][ny] != '#' and (nx, ny) not in cellsToCheck and (nx, ny) not in cellsChecked:
                        cellsToCheck += [(nx, ny)]

                except IndexError:
                    returnVal = False

        return returnVal
