# built-in
import heapq
import logging
import logging.config
import LoggingConfig
import time
import os
#third-party
import numpy as np
#local

def distance(pos1, pos2):
    return np.linalg.norm(np.array(pos2) - np.array(pos1))

def computeCurrentPosition(currentX,currentY,heading,speed,duration):
    newX = currentX + duration * np.cos(np.radians(heading - 90)) * speed
    newY = currentY + duration * np.sin(np.radians(heading - 90)) * speed
    newX = round(newX, 3)
    newY = round(newY, 3)
    return (newX,newY)

# ============= Data Structures

class PriorityQueue:
    def __init__(self):
        self.elements = []
        self.check = set()

    def __contains__(self, item):
        assert len(self.elements) >= len(self.check)
        return item in self.check

    def empty(self):
        assert len(self.elements) >= len(self.check)
        return len(self.elements) == 0

    def put(self, priority, item):
        if item not in self.check:
            heapq.heappush(self.elements, (priority, item))
            self.check.add(item)
        assert len(self.elements) >= len(self.check)

    def get(self):
        item = heapq.heappop(self.elements)[1]
        self.check.remove(item)
        return item

# ============== A* helpers
class AstarNode(object):

    def __init__(self, cellPos, parent):
        self.parent       = parent
        self.cellPos      = cellPos
        self.gCost        = 0
        self.hCost        = 0
        self.fCost        = 0

    def __lt__(self, other):
        return self.fCost < other.fCost

# ============== Logging Setup

def setLoggerUname(uname):
    os.makedirs('logs', exist_ok=True)
    LoggingConfig.LOGGINGCONFIG['handlers']['handler_file']['filename'] = os.path.join(
        'logs',
        '{}_{}.log'.format(uname, time.strftime("%y%m%d%H%M%S", time.localtime()))
    )
    logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)

