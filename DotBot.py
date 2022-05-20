# built-in
import math
import itertools
# third-party
# local
import SimEngine
import Wireless
import Utils as u

# setup logging
import logging.config
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)
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

        # drop frame if heading and speed are same as last frame
        if (frame['movements'][self.dotBotId]['heading'] == self.currentHeading and
            frame['movements'][self.dotBotId]['speed'] == self.currentSpeed):
            return

        # cancel scheduled bump when new packet is received
        self.simEngine.cancelEvent(tag=f'{self.dotBotId}_bumpSensorCb')

        # update my position
        (self.x, self.y) = self.computeCurrentPosition()

        # apply heading and speed from packet
        self._setHeading(frame['movements'][self.dotBotId]['heading'])
        self._setSpeed(frame['movements'][self.dotBotId]['speed'])
        log.debug(f'Dotbot {self.dotBotId} heading is {self.currentHeading} and speed is {self.currentSpeed}')

        # remember when I started moving, will be indicated in notification
        self.tsMovementStart      = self.simEngine.currentTime()
        self.tsMovementStop       = None
        log.debug(f'Dotbot {self.dotBotId} started new movement at {self.tsMovementStart}')

        # compute when/where next bump will happen
        (bump_x, bump_y, bump_ts) = self._computeNextBump(self.x, self.y, self.currentHeading, self.currentSpeed, self.floorplan.obstacles)
        log.debug(f'Dotbot {self.dotBotId} next bump at ({bump_x}, {bump_y}) at {bump_ts}')

        # remember
        self.next_bump_x          = bump_x
        self.next_bump_y          = bump_y
        self.next_bump_ts         = self.simEngine.currentTime() + bump_ts

        # schedule the bump event
        self.simEngine.schedule(self.next_bump_ts, self._bumpSensorCb, tag=f'{self.dotBotId}_bumpSensorCb')
        log.debug(f'next bump for {self.dotBotId} scheduled for {self.next_bump_ts}')

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

        return (self.next_bump_x, self.next_bump_y)

    # ======================== private =========================================

    #=== bump sensor interrupt handler
    
    def _bumpSensorCb(self):
        '''
        Bump sensor triggered
        '''

        assert self.simEngine.currentTime() == self.next_bump_ts

        # update my position
        (self.x, self.y) = self.computeCurrentPosition()
        log.debug(f'DotBot {self.dotBotId} stopped at ({self.x}, {self.y}) at {self.simEngine.currentTime()}')
        log.debug(f'DotBot {self.dotBotId} expected position at ({self.next_bump_x}, {self.next_bump_y}) at {self.next_bump_ts}')
        assert self.x == self.next_bump_x
        assert self.y == self.next_bump_y

        # stop moving
        self.currentSpeed        = 0

        # remember when I stop moving
        self.tsMovementStop      = self.simEngine.currentTime()

        # transmit
        self._transmit()

    def _transmit(self):
        '''
        frame formating a transmission
        '''

        # format frame to transmit
        frameToTx = {
            'frameType':          self.FRAMETYPE_NOTIFICATION,
            'source':             self.dotBotId,
            'movementDuration':   self.tsMovementStop - self.tsMovementStart
        }

        # hand over to wireless
        self.wireless.transmit(
            frame       = frameToTx,
            sender      = self,
        )

    #=== motor control
    
    def _setHeading(self, heading):
        assert heading >= 0
        assert heading < 360
        
        self.currentHeading = heading

    def _setSpeed(self, speed):
        
        self.currentSpeed = speed

    #=== internal bump computation
    
    def _computeNextBump(self, currentX, currentY, heading, speed, obstacles):

        bumpX         = None
        bumpY         = None
        timetobump    = None
        intersectPoints = []

        # find equation of trajectory as y = a*x + b
        if heading not in [0, 90, 180, 270]:
            a = math.tan(math.radians(heading-90))

        # find all valid intersections with obstacles
        for obstacle in obstacles:
            xmin = obstacle['x']
            ymin = obstacle['y']
            xmax = xmin + obstacle['width']
            ymax = ymin + obstacle['height']

            if heading in [90, 270]:
                # horizontal edge case

                if (
                    (heading == 90  and xmax <= currentX) or
                    (heading == 270 and currentX <= xmin)
                ):
                    continue

                x = xmin if heading == 90 else xmax
                y = currentY

                if xmin <= round(x, 10) <= xmax and ymin <= round(y, 10) <= ymax:
                    intersectPoints += [(x, y)]

            elif heading in [ 0, 180]:
                # vertical edge case

                if (
                    (heading == 0   and currentY <= ymin) or
                    (heading == 180 and ymax <= currentY)
                ):
                    continue

                x = currentX
                y = ymax if heading == 0 else ymin

                if xmin <= round(x, 10) <= xmax and ymin <= round(y, 10) <= ymax:
                    intersectPoints += [(x, y)]

            else:

                # general case
                if (
                    ((0   < heading < 90   and (xmax <= currentX or currentY <= ymin))) or
                    ((90  < heading < 180  and (xmax <= currentX or ymax <= currentY))) or
                    ((180 < heading < 270  and (currentX <= xmin or ymax <= currentY))) or
                    ((270 < heading < 360  and (currentX <= xmin or currentY <= ymin)))
                ):
                    continue

                # compute intersection points with 4 walls

                # top right quarter
                if 0 < heading < 90:
                    bottomX = ((ymax - currentY) / a) + currentX      # intersection with bottom obstacle border (y=ymax)
                    leftY   = (xmin - currentX)*a + currentY          # intersection with left obstacle border   (x=xmin)

                    if xmin <= round(bottomX, 10) <= xmax:
                        intersectPoints += [(bottomX, ymax)]
                    if ymin <= round(leftY, 10) <= ymax:
                        intersectPoints += [(xmin, leftY)]

                # bottom right quarter
                if 90 < heading < 180:
                    topX    = ((ymin - currentY) / a) + currentX       # intersection with top obstacle border    (y=ymin)
                    leftY   = (xmin - currentX)*a + currentY           # intersection with left obstacle border   (x=xmin)

                    if xmin <= round(topX, 10) <= xmax:
                        intersectPoints += [(topX, ymin)]
                    if ymin <= round(leftY, 10) <= ymax:
                        intersectPoints += [(xmin, leftY)]

                # bottom left quarter
                if 180 < heading < 270:
                    topX    = ((ymin - currentY) / a) + currentX        # intersection with top obstacle border    (y=ymin)
                    rightY  = (xmax - currentX)*a + currentY            # intersection with right obstacle border  (x=xmax)

                    if xmin <= round(topX, 10) <= xmax:
                        intersectPoints += [(topX, ymin)]
                    if ymin <= round(rightY, 10) <= ymax:
                        intersectPoints += [(xmax, rightY)]

                # top left quarter
                if 270 < heading < 360:
                    bottomX = ((ymax - currentY) / a) + currentX      # intersection with bottom obstacle border (y=ymax)
                    rightY  = (xmax - currentX)*a + currentY          # intersection with right obstacle border  (x=xmax)

                    if xmin <= round(bottomX, 10) <= xmax:
                        intersectPoints += [(bottomX, ymax)]
                    if ymin <= round(rightY, 10) <= ymax:
                        intersectPoints += [(xmax, rightY)]

        if intersectPoints:

            # find closest intersection point to current position
            distances      = [((x,y), u.distance((currentX, currentY), (x, y))) for (x, y) in intersectPoints]
            distances      = sorted(distances, key=lambda e: e[1])
            (bumpX, bumpY) = distances[0][0]

            # find bump time
            timetobump = u.distance((currentX, currentY), (bumpX, bumpY)) / speed if speed != 0 else 0

            assert bumpX >= 0 and bumpY >= 0

            bumpX = round(bumpX, 5)
            bumpY = round(bumpY, 5)
        else:
            log.debug("NO INTERSECT FOUND")

        # return where and when robot will bump
        return (bumpX, bumpY, timetobump)