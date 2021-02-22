# built-in
import math
import itertools
import time
import logging
# third-party
# local
import SimEngine
import Orchestrator
import Wireless
import Utils as u

# logging
log = logging.getLogger('DotBot')

class DotBot(Wireless.WirelessDevice):
    '''
    A single DotBot.
    '''

    def __init__(self, dotBotId, x, y, floorplan):

        # store params
        self.dotBotId             = dotBotId
        self.x                    = x
        self.y                    = y
        self.floorplan            = floorplan

        #=== local variables
        # singletons
        self.simEngine            = SimEngine.SimEngine()
        self.wireless             = Wireless.Wireless()
        # sequence numbers (to filter out duplicate commands and notifications)
        self.seqNumMovement       = None
        self.seqNumNotification   = 0
        # current heading and speed
        self.currentHeading       = 0
        self.currentSpeed         = 0
        # timestamps of when movement starts/stops
        self.tsMovementStart      = None
        self.tsMovementStop       = None
        # state maintained by internal bump computation
        self.next_bump_x          = None  # coordinate the DotBot will bump into next
        self.next_bump_y          = None
        self.next_bump_ts         = None  # time at which DotBot will bump

    # ======================== public ==========================================

    def receive(self, frame):
        '''
        Received a frame from the orchestrator
        '''
        assert frame['frameType'] in self.FRAMETYPE_ALL

        # drop any frame that is NOT a FRAMETYPE_COMMAND
        if frame['frameType']!=self.FRAMETYPE_COMMAND:
            return
        
        # parse frame, extract myMovement
        myMovement = frame['movements'][self.dotBotId]

        now      = self.simEngine.currentTime()
        if myMovement['timer']:
            stopTime = now + myMovement['timer']
        else:
            stopTime = math.inf

        # log
        log.debug('[%10.3f]    --> RX command %s',now,myMovement['seqNumMovement'])
        
        # filter out duplicates
        if myMovement['seqNumMovement'] == self.seqNumMovement:
            return
        
        self.seqNumMovement       = myMovement['seqNumMovement']

        # if I get here I have received a NEW movement

        # cancel notification retransmission
        self.simEngine.cancelEvent(tag = "retransmission_DotBot_{}".format(self.dotBotId))

        # apply heading and speed from packet
        self._setHeading(myMovement['heading'])
        self._setSpeed(myMovement['speed'])
        
        # remember when I started moving, will be indicated in notification
        self.tsMovementStart      = now
        self.tsMovementStop       = None

        # compute when/where next bump will happen
        (bump_x, bump_y, bump_ts) = self._computeNextBump()
        
        # remember
        self.next_bump_x          = bump_x
        self.next_bump_y          = bump_y
        self.next_bump_ts         = bump_ts

        if stopTime <= self.next_bump_ts:
            # schedule timeout event
            self.simEngine.schedule(stopTime, self._timeout)
        else:
            # schedule the bump event
            self.simEngine.schedule(self.next_bump_ts, self._bump)

    def computeCurrentPosition(self):
        '''
        Compute the current position based on previous position and movement.
        '''

        # shorthand
        now = self.simEngine.currentTime()
        
        # compute current position based on where it was and where it's going
        if self.currentSpeed==0:
            (newX,newY) = (self.x,self.y)
        else:
            (newX,newY) = u.computeCurrentPosition(
                currentX = self.x,
                currentY = self.y,
                heading  = self.currentHeading,
                speed    = self.currentSpeed,
                duration = now - self.tsMovementStart,
            )
        
        # do NOT write back any results to the DotBot's state as race condition possible
        return (newX,newY)
    
    def getNextBumpPosition(self):
        '''
        Retrieve the position of this DotBot's next bump.
        '''

        return (self.next_bump_x,self.next_bump_y)

    # ======================== private =========================================

    #=== bump sensor interrupt handler
    
    def _bump(self):
        '''
        Bump sensor triggered
        '''

        self.bump = True
        # log
        log.debug('[%10.3f] ================== bump',self.simEngine.currentTime())
        
        self._stopAndTransmit()

    def _timeout(self):
        '''
        movement allocated timer ran out
        '''

        self.bump = False
        self._stopAndTransmit()

    def _stopAndTransmit(self):
        '''
        transmit a packet to the orchestrator to request a new heading and to notify of obstacle
        '''

        # update my position
        (self.x,self.y)      = self.computeCurrentPosition()

        if self.bump == True:
            assert self.x == self.next_bump_x
            assert self.y == self.next_bump_y

        # stop moving
        self.currentSpeed        = 0
        
        # remember when I stop moving
        self.tsMovementStop      = self.simEngine.currentTime()

        # update notification ID
        self.seqNumNotification += 1

        # transmit
        self._transmit()

    def _transmit(self):
        '''
        frame formating a transmission
        '''

        # format frame to transmit
        frameToTx = {
            'frameType':          self.FRAMETYPE_NOTIFICATION,
            'dotBotId':           self.dotBotId,
            'seqNumNotification': self.seqNumNotification,
            'tsMovementStart':    self.tsMovementStart,
            'tsMovementStop':     self.tsMovementStop,
            'bump':               self.bump
        }

        # log
        log.debug('[%10.3f]    <-- TX notif %s',self.simEngine.currentTime(),self.seqNumNotification)
        
        # hand over to wireless
        self.wireless.transmit(
            frame       = frameToTx,
            sender      = self,
        )

        # schedule re-transmit
        self.simEngine.schedule(
            ts  = self.simEngine.currentTime() + Orchestrator.Orchestrator.COMM_DOWNSTREAM_PERIOD_S,
            cb  = self._transmit,
            tag = "retransmission_DotBot_{}".format(self.dotBotId),
        )

    #=== motor control
    
    def _setHeading(self, heading):
        assert heading >= 0
        assert heading < 360
        
        self.currentHeading = heading

    def _setSpeed(self, speed):
        
        self.currentSpeed = speed

    #=== internal bump computation
    
    def _computeNextBump(self):

        # compute when/where next bump will happen with frame
        (bump_x_frame, bump_y_frame, bump_ts_frame) = self._computeNextBumpFrame()

        # start by considering you will bump into the frame
        bump_x     = bump_x_frame
        bump_y     = bump_y_frame
        bump_ts    = bump_ts_frame

        # loop through obstables, looking for closer bump coordinates
        for obstacle in self.floorplan.obstacles:

            # coordinates of obstacle's upper-left and lower-right corner
            ax     = obstacle['x']
            ay     = obstacle['y']
            bx     = ax + obstacle['width']
            by     = ay + obstacle['height']

            # compute bump coordinate for this obstacle (if exist)
            # Note: return (None,None,None) if no bump
            (bump_xo, bump_yo, bump_tso) = self._computeNextBumpObstacle(
                self.x,
                self.y,
                bump_x_frame,
                bump_y_frame,
                ax,
                ay,
                bx,
                by,
            )

            # update bump coordinates if closer
            if (bump_xo != None) and (bump_tso <= bump_ts):
                (bump_x, bump_y, bump_ts) = (bump_xo, bump_yo, bump_tso)

        # FIXME: remove this
        bump_x = self.x + (bump_ts - self.tsMovementStart) * math.cos(math.radians(self.currentHeading - 90)) * self.currentSpeed
        bump_y = self.y + (bump_ts - self.tsMovementStart) * math.sin(math.radians(self.currentHeading - 90)) * self.currentSpeed
        bump_x = round(bump_x, 3)
        bump_y = round(bump_y, 3)
        
        # return where and when robot will bump
        return (bump_x, bump_y, bump_ts)

    def _computeNextBumpFrame(self):

        if   self.currentHeading in [90, 270]:
            # horizontal edge case

            north_x     = None  # doesn't cross
            south_x     = None  # doesn't cross
            west_y      = self.y
            east_y      = self.y

        elif self.currentHeading in [ 0, 180]:
            # vertical edge case

            north_x     = self.x
            south_x     = self.x
            west_y      = None  # doesn't cross
            east_y      = None  # doesn't cross

        else:
            # general case

            # find equation of trajectory as y = a*x + b
            a           = math.tan(math.radians(self.currentHeading - 90))
            b           = self.y - (a * self.x)

            # compute intersection points with 4 walls
            north_x     = (0 - b) / a                      # intersection with North wall (y=0)
            south_x     = (self.floorplan.height - b) / a  # intersection with South wall (y=self.floorplan.height)
            west_y      = 0 * a + b                        # intersection with West  wall (x=0)
            east_y      = self.floorplan.width * a + b     # intersection with East  wall (x=self.floorplan.width)

            # round
            north_x     = round(north_x, 3)
            south_x     = round(south_x, 3)
            west_y      = round(west_y,  3)
            east_y      = round(east_y,  3)

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
            distances = [
                (u.distance(a, b), a, b)
                    for (a, b) in
                        itertools.product(valid_intersections, valid_intersections)
            ]
            distances = sorted(distances, key=lambda e: e[0])
            valid_intersections = [distances[-1][1], distances[-1][2]]

        assert len(valid_intersections) == 2

        # pick the correct intersection point given the heading of the robot
        (x_int0, y_int0) = valid_intersections[0]
        (x_int1, y_int1) = valid_intersections[1]
        if self.currentHeading == 0:
            # going up

            # pick top-most intersection
            if y_int0 < y_int1:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)
        elif (0 < self.currentHeading and self.currentHeading < 180):
            # going right

            # pick right-most intersection
            if x_int1 < x_int0:
                (bump_x, bump_y) = (x_int0, y_int0)
            else:
                (bump_x, bump_y) = (x_int1, y_int1)
        elif self.currentHeading == 180:
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
        timetobump = u.distance((self.x, self.y), (bump_x, bump_y)) / self.currentSpeed
        bump_ts    = self.tsMovementStart + timetobump

        # round
        bump_x     = round(bump_x, 3)
        bump_y     = round(bump_y, 3)

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
        deltax     = x2 - rx
        deltay     = y2 - ry
        #                left    right   bottom      top
        p          = [-deltax,  deltax, -deltay,  deltay]
        q          = [rx - ax, bx - rx, ry - ay, by - ry]

        # initialize u1 and u2
        u1         = -math.inf
        u2         =  math.inf

        # iterating over the 4 boundaries of the obstacle in order to find the t value for each one.
        #     if p = 0 then the trajectory is parallel to that boundary
        #     if p = 0 and q<0 then line completly outside boundaries

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

            bump_x      = rx + u1 * deltax
            bump_y      = ry + u1 * deltay
            
            timetobump  = u.distance((rx, ry), (bump_x, bump_y)) / self.currentSpeed
            bump_ts     = self.tsMovementStart + timetobump
            
            # round
            bump_x      = round(bump_x, 3)
            bump_y      = round(bump_y, 3)

            return (bump_x, bump_y, bump_ts)

        else:

            return (None, None, None)
