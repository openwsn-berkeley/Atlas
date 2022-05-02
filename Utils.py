import numpy as np
import heapq
import logging
import os

def distance(pos1, pos2):
    return np.linalg.norm(np.array(pos2) - np.array(pos1))

def computeCurrentPosition(currentX,currentY,heading,speed,duration):
    newX = currentX + duration * np.cos(np.radians(heading - 90)) * speed
    newY = currentY + duration * np.sin(np.radians(heading - 90)) * speed
    newX = round(newX, 3)
    newY = round(newY, 3)
    return (newX,newY)

def lineSegentsIntersect(segment1,segment2):

    #shorthand
    (x1,y1)           = segment1[0], segment1[1]
    (x2,y2)           = segment1[2], segment1[3]
    (x3,y3)           = segment2[0], segment2[1]
    (x4,y4)           = segment2[2], segment2[3]

    if max(x1, x2) < min(x3, x4):
        return False  # There is no mutual abcisses

    # find m and b for line equation y = mx + b
    if x1 == x2:
        m1 = 0
    else:
        m1 = (y1-y2)/(x1-x2)

    if x3 == x4:
        m2 = 0
    else:
        m2 = (y3-y4)/(x3-x4)

    b1 = y1-m1*x1
    b2 = y3-m2*x3

    if (m1 == m2):
        return False  # Parallel segments

    # find intersection point
    xi = (b2-b1)/(m1-m2)
    yi = xi*m1 + b1

    # check if intersection point is within bounadry interval
    if ((xi < max(min(x1, x2), min(x3, x4))) or
            (xi > min(max(x1, x2), max(x3, x4))) or
            (yi < max(min(y1, y2), min(y3, y4))) or
            (yi > min(max(y1, y2), max(y3, y4)))
        ):

        return False

    else:

        return True

#============= Data Structures

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

