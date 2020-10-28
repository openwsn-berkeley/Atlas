# built-in
import random
import math
import itertools
import time
import threading
# third-party
# local
import SimEngine
import Wireless
import Utils as u


class DotBot(object):
    '''
    A single DotBot.
    '''

    def __init__(self, dotBotId, floorplan):

        # store params
        self.dotBotId = dotBotId
        self.floorplan = floorplan

        # local variables
        self.simEngine = SimEngine.SimEngine()
        self.wireless = Wireless.Wireless()
        self.x = None  # the "real" position, sometimes in the past. Set to None to ensure single initialization
        self.y = None
        self.posTs = 0  # timestamp, in s, of when was at position (at current calculated position it was this time)
        self.lastCommandIdReceived = None  # set to None as not a valid command Id
        self.headingRequested = 0  # the heading, a float between 0 and 360 degrees (0 indicates North) as requested by the orchestrator
        self.headingInaccuracy = 0  # innaccuracy, in degrees of the heading. Actual error computed as uniform(-,+)
        self.headingActual = 0  # actual heading, taking into account inaccuracy
        self.speedRequested = 0  # speed, in m/s, as requested by the orchestrator
        self.speedInaccuracy = 0  # innaccuracy, in m/s of the speed. Actual error computed as uniform(-,+)
        self.speedActual = 0  # actual speed, taking into account inaccuracy
        self.next_bump_x = None  # coordinate the DotBot will bump into next
        self.next_bump_y = None
        self.next_bump_ts = 0  # time at which DotBot will bump
        self.packetReceived = False  # packet received or not
        self.movingTime = 0  # time at which robot starts moving after bump
        self.period = 1

    # ======================== public ==========================================

    def setInitialPosition(self, x, y):
        '''
        Call exactly once at start of simulation to exactly place the DotBot at its initial position.
        '''
        assert self.x == None
        assert self.y == None
        self.x = x
        self.y = y
        self.posTs = self.simEngine.currentTime()

    def fromOrchestrator(self, packet):
        '''
        Received a packet from the orchestrator
        '''

        # extract portion of orchestrator message which is for me (shorthand)
        myMsg = packet[self.dotBotId]

        # disregard duplicate command
        if myMsg['commandId'] == self.lastCommandIdReceived:
            return

        self.packetReceived = True
        # movingTime = self.simEngine.currentTime()
        print('packet received at', self.simEngine.currentTime())

        # remember what I was asked
        self.lastCommandIdReceived = myMsg['commandId']
        self.headingRequested = myMsg['heading']
        self.speedRequested = myMsg['speed']

        # apply heading and speed from packet
        self._setHeading(myMsg['heading'])
        self._setSpeed(myMsg['speed'])

        # compute when/where next bump will happen
        (bump_x, bump_y, bump_ts) = self._computeNextBump()

        # remember
        self.next_bump_x = bump_x
        self.next_bump_y = bump_y
        self.next_bump_ts = bump_ts

        # schedule
        self.simEngine.schedule(self.next_bump_ts, self._bump)

    def getAttitude(self):
        '''
        "Backdoor" functions used by the simulation engine to compute where the DotBot is now.

        \post updates attributes position and posTs
        '''

        # gather state
        now = self.simEngine.currentTime()
        x = self.x
        y = self.y
        posTs = self.posTs
        headingActual = self.headingActual
        speedActual = self.speedActual

        # update position
        newX = x + (now - posTs) * math.cos(math.radians(headingActual - 90)) * speedActual
        newY = y + (now - posTs) * math.sin(math.radians(headingActual - 90)) * speedActual

        # do NOT write back any results to the DotBot's state as race condition possible

        return {
            'x': newX,
            'y': newY,
            'heading': self.headingActual,
            'speed': self.speedActual,
            'next_bump_x': self.next_bump_x,
            'next_bump_y': self.next_bump_y,
        }

    # ======================== private =========================================

    def _checkPacket(self):

        if self.packetReceived:
            pass
        else:
            while not self.packetReceived:
                print('packet lost at', self.simEngine.currentTime())
                self._transmit()

        self.packetReceived = False

    def _transmit(self):
        print('bumpTs', self.next_bump_ts, 'movingTime', self.movingTime)
        self.wireless.toOrchestrator({
            'dotBotId': self.dotBotId,
            'bumpTs': self.next_bump_ts,
            'movingTime': self.movingTime,

        })

    def _bump(self):
        '''
        Bump sensor triggered
        '''
        # update my position
        self.x = self.next_bump_x
        self.y = self.next_bump_y
        self.posTs = self.next_bump_ts

        # stop moving
        self.speedActual = 0
        self._transmit()
        self._checkPacket()

        # assert self.simEngine.currentTime() == self.next_bump_ts

        # report bump to orchestrator
        # self.wireless.toOrchestrator({
        #     'dotBotId':     self.dotBotId,
        #     'bumpTs':       self.posTs,
        #     'movingTime':   self.movingTime,
        #
        # })

    def _setHeading(self, heading):
        '''
        Change the heading of the DotBot.
        Actual heading affected by self.headingInaccuracy
        Assumes applying new heading is infinitely fast.
        '''
        assert heading >= 0
        assert heading < 360
        if self.headingInaccuracy:  # cut computation in two cases for efficiency
            self.headingActual = heading + (-1 + (2 * random.random())) * self.headingInaccuracy
        else:
            self.headingActual = heading

    def _setSpeed(self, speed):
        '''
        Change the speed of the DotBot.
        Actual speed affected by self.speedInaccuracy
        Assumes applying new speed is infinitely fast.
        '''
        if self.speedInaccuracy:  # cut computation in two cases for efficiency
            self.speedActual = speed + (-1 + (2 * random.random())) * self.speedInaccuracy
        else:
            self.speedActual = speed

    def _computeNextBump(self):

        # compute when/where next bump will happen with frame
        (bump_x_frame, bump_y_frame, bump_ts_frame) = self._computeNextBumpFrame()

        # start by considering you will bump into the frame
        bump_x = bump_x_frame
        bump_y = bump_y_frame
        bump_ts = bump_ts_frame

        # loop through obstables, lookign for closer bump coordinates
        for obstacle in self.floorplan.obstacles:

            # coordinates of obstacble upper left and lower right corner
            ax = obstacle['x']
            ay = obstacle['y']
            bx = ax + obstacle['width']
            by = ay + obstacle['height']

            # compute bump coordinate for this obstacle (if exist)
            # Note: return (None,None,None) if no bump
            (bump_xo, bump_yo, bump_tso) = self._computeNextBumpObstacle(self.x, self.y, bump_x_frame, bump_y_frame, ax,
                                                                         ay, bx, by)

            # update bump coordinates if closer
            if (bump_xo != None) and (bump_tso <= bump_ts):
                (bump_x, bump_y, bump_ts) = (bump_xo, bump_yo, bump_tso)

        # FIXME: remove this
        bump_x = self.x + (bump_ts - self.posTs) * math.cos(math.radians(self.headingActual - 90)) * self.speedActual
        bump_y = self.y + (bump_ts - self.posTs) * math.sin(math.radians(self.headingActual - 90)) * self.speedActual
        bump_x = round(bump_x, 3)
        bump_y = round(bump_y, 3)

        self.movingTime = self.simEngine.currentTime()
        # return where and when robot will bump
        return (bump_x, bump_y, bump_ts)

    def _computeNextBumpFrame(self):

        if self.headingActual in [90, 270]:
            # horizontal edge case

            north_x = None  # doesn't cross
            south_x = None  # doesn't cross
            west_y = self.y
            east_y = self.y

        elif self.headingActual in [0, 180]:
            # vertical edge case

            north_x = self.x
            south_x = self.x
            west_y = None  # doesn't cross
            east_y = None  # doesn't cross

        else:
            # general case

            # find equation of trajectory as y = a*x + b
            a = math.tan(math.radians(self.headingActual - 90))
            b = self.y - (a * self.x)

            # compute intersection points with 4 walls
            north_x = (0 - b) / a  # intersection with North wall (y=0)
            south_x = (self.floorplan.height - b) / a  # intersection with South wall (y=self.floorplan.height)
            west_y = 0 * a + b  # intersection with West wall (x=0)
            east_y = self.floorplan.width * a + b  # intersection with West wall (x=self.floorplan.width)

            # round
            north_x = round(north_x, 3)
            south_x = round(south_x, 3)
            west_y = round(west_y, 3)
            east_y = round(east_y, 3)

        # pick the two intersection points on the floorplan perimeter
        valid_intersections = []
        if (north_x != None and 0 <= north_x and north_x <= self.floorplan.width):
            valid_intersections += [(north_x, 0)]
        if (south_x != None and 0 <= south_x and south_x <= self.floorplan.width):
            valid_intersections += [(south_x, self.floorplan.height)]
        if (west_y != None and 0 <= west_y and west_y <= self.floorplan.height):
            valid_intersections += [(0, west_y)]
        if (east_y != None and 0 <= east_y and east_y <= self.floorplan.height):
            valid_intersections += [(self.floorplan.width, east_y)]

        # if more than 2 valid points, pick the pair that is furthest apart
        if len(valid_intersections) > 2:
            distances = [(u.distance(a, b), a, b) for (a, b) in
                         itertools.product(valid_intersections, valid_intersections)]
            distances = sorted(distances, key=lambda e: e[0])
            valid_intersections = [distances[-1][1], distances[-1][2]]

        assert len(valid_intersections) == 2

        # pick the correct intersection point given the heading of the robot
        (x_int0, y_int0) = valid_intersections[0]
        (x_int1, y_int1) = valid_intersections[1]
        if self.headingActual == 0:
            # going up

            # pick top-most intersection
            if y_int0 < y_int1:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)
        elif (0 < self.headingActual and self.headingActual < 180):
            # going right

            # pick right-most intersection
            if x_int1 < x_int0:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)
        elif self.headingActual == 180:
            # going down

            # pick bottom-most intersection
            if y_int1 < y_int0:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)
        else:
            # going left

            # pick right-most intersection
            if x_int0 < x_int1:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)

        # compute time to bump
        timetobump = u.distance((self.x, self.y), (bump_x, bump_y)) / self.speedActual
        bump_ts = self.posTs + timetobump

        # round
        bump_x = round(bump_x, 3)
        bump_y = round(bump_y, 3)

        return (bump_x, bump_y, bump_ts)

    def _computeNextBumpObstacle(self, rx, ry, x2, y2, ax, ay, bx, by):
        '''
        \param rx current robot coordinate x
        \param ry
        \param x2 second point on segment robot if traveling on
        \param y2
        \param ax upper-left corner of obstacle
        \param ay
        \param bx lower-right corner of obstacle
        \param by
        \return (bump_x, bump_y,bump_ts) if robot bumps into obstacle
        \return (  None,   None,   None) if robot does NOT bump into obstacle
        Function implements the Liang-Barsky algorithm algorithm
        - https://www.ques10.com/p/22053/explain-liang-barsky-line-clipping-algorithm-with-/
        - https://gist.github.com/ChickenProp/3194723
        '''

        # initial calculations (see algorithm)
        deltax = x2 - rx
        deltay = y2 - ry
        #                         left      right     bottom        top
        p = [-deltax, deltax, -deltay, deltay]
        q = [rx - ax, bx - rx, ry - ay, by - ry]

        # initialize u1 and u2
        u1 = -math.inf
        u2 = math.inf

        # iterating over the 4 boundaries of the obstacle in order to find the t value for each one.
        # if p = 0 then the trajectory is parallel to that boundary
        # if p = 0 and q<0 then line completly outside boundaries

        # update u1 and u2
        for i in range(4):

            # abort if line outside of boundary

            if p[i] == 0:
                # line is parallel to boundary i

                if q[i] < 0:
                    return (None, None, None)
                pass  # nothing to do
            else:
                t = q[i] / p[i]
                if (p[i] < 0 and u1 < t):
                    u1 = t
                elif (p[i] > 0 and u2 > t):
                    u2 = t

        # if I get here, u1 and u2 should be set
        assert u1 is not None
        assert u2 is not None

        # decide what to return
        if (u1 >= 0 and u1 <= u2 and u2 <= 1):

            bump_x = rx + u1 * deltax
            bump_y = ry + u1 * deltay

            timetobump = u.distance((rx, ry), (bump_x, bump_y)) / self.speedActual
            bump_ts = self.posTs + timetobump

            # round
            bump_x = round(bump_x, 3)
            bump_y = round(bump_y, 3)

            return (bump_x, bump_y, bump_ts)

        else:

            return (None, None, None)