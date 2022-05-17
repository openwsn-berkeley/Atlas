# built-in
# third-party
# local

class Floorplan(object):
    '''
    The floorplan the DotBots move in.
    '''
    
    def __init__(self, drawing):
        assert self._isMapValid(drawing)
        self.width, self.height, self.obstacles = self._parseDrawing(drawing)

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
                    obstacles += [{'x': x, 'y':  y, 'width': 1, 'height': 1}] # TODO: could do line merging here to
        return width, height, obstacles

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

        # split drawing into matrix of characters
        matrixOfChars   = [line for line in drawing.splitlines() if line]
        charsChecked    = []     # character positions in map of which surrounding frontiers have been determined
        charsToCheck    = []     # character positions in map of which surrounding frontiers are to be determined

        # if there is no starting position character 's' map is invalid
        try:
            startPos    = [(lidx,line.index('s')) for (lidx,line) in enumerate(matrixOfChars) if 's' in line][0]
        except IndexError:
            startPos    = None
            returnVal   = False

        charsToCheck   += [startPos]

        # keep looping until there are no more froniters (all borders have been found)
        while charsToCheck and startPos:

            (charRow,charCol) = charsToCheck.pop(0)
            charsChecked     += [(charRow,charCol)]

            # set surrounding 8 character positions as frontiers to check next if they are not obstacles
            neighbourChars    = [
                (charRow+1,  charCol  ), (charRow-1,  charCol  ),
                (charRow,    charCol-1), (charRow,    charCol+1),
                (charRow-1,  charCol-1), (charRow+1,  charCol+1),
                (charRow-1,  charCol+1), (charRow+1,  charCol-1)
            ]

            for nx, ny in neighbourChars:

                try:
                    # if drawing contains characters that aren't '#,.,s' map is invalid
                    assert matrixOfChars[nx][ny] == '#' or matrixOfChars[nx][ny] == '.' or matrixOfChars[nx][ny] == 's'

                    # if next frontier position is not in matrix of characters map is invalid
                    if matrixOfChars[nx][ny] != '#' and (nx, ny) not in charsToCheck  and (nx, ny) not in charsChecked:
                        charsToCheck += [(nx, ny)]

                except IndexError:
                    returnVal = False

        return returnVal