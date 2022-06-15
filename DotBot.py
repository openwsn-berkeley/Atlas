# built-in
import math
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

    RETRY_TIMEOUT_S               = 1

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
        # sequence numbers (to filter out duplicate commands and notifications)
        self.seqNumCommand        = None
        self.seqNumNotification   = 0
        # state maintained by internal bump computation
        self.nextBumpX            = None   # coordinate the DotBot will bump into next
        self.nextBumpY            = None
        self.nextBumpTime         = None   # time at which DotBot will bump
        # is DotBot a relay
        self.isRelay              = False
        # if DotBot has bumped
        self.hasJustBumped        = False  # needed as variable as retransmits are called by simEngine
        # estimated PDR is number of packets received over number of packets expected
        self.estimatedPdr         = 1      # packets received per second
        # how frequent estimated PDR is sent to orchestrator
        self.estimatedPdrPeriod   = 10     # in seconds
        self.numPacketReceived    = 0

        # schedule next estimated PDR call back
        #self.simEngine.schedule(self.simEngine.currentTime() + self.estimatedPdrPeriod, self._estimatedPdrCb)

    # ======================== public ==========================================

    def receive(self, frame):
        '''
        Received a frame from the orchestrator
        '''
        assert frame['frameType'] in self.FRAMETYPE_ALL

        # drop any frame that is NOT a FRAMETYPE_COMMAND
        if frame['frameType']!=self.FRAMETYPE_COMMAND:
            return

        # new command packet received
        self.numPacketReceived += 1

        # filter out duplicates
        if frame['movements'][self.dotBotId]['seqNumCommand'] == self.seqNumCommand:
            return

        # set stop time based on movementTimeout if given
        movementTimeout          = frame['movements'][self.dotBotId]['movementTimeout']
        stopTime                 = movementTimeout + self.simEngine.currentTime() if movementTimeout else math.inf

        self.seqNumCommand       = frame['movements'][self.dotBotId]['seqNumCommand']

        # set relay status
        self.isRelay             = frame['movements'][self.dotBotId]['isRelay']

        # cancel scheduled movement movementTimeout
        self.simEngine.cancelEvent(tag=f'{self.dotBotId}_movementTimeout')

        # cancel scheduled bump when new packet is received
        self.simEngine.cancelEvent(tag=f'{self.dotBotId}_bumpSensorCb')

        # cancel notification retransmission
        self.simEngine.cancelEvent(tag="retransmission_DotBot_{}".format(self.dotBotId))

        # update my position
        (self.x, self.y) = self.computeCurrentPosition()

        # apply heading and speed from packet
        self._setHeading(frame['movements'][self.dotBotId]['heading'])
        self._setSpeed(frame['movements'][self.dotBotId]['speed'])
        log.debug(f'Dotbot {self.dotBotId} heading is {self.currentHeading} and speed is {self.currentSpeed}')

        # remember when I started moving, will be indicated in notification
        self.tsMovementStart       = self.simEngine.currentTime()
        self.tsMovementStop        = None
        log.debug(f'Dotbot {self.dotBotId} started new movement at {self.tsMovementStart}')

        # compute when/where next bump will happen if DotBot is moving
        if self.currentSpeed == 0:
            (bumpX, bumpY, timetobump) = (None, None, math.inf)
        else:
            (bumpX, bumpY, timetobump) = self._computeNextBump(self.x, self.y, self.currentHeading, self.currentSpeed, self.floorplan.obstacles)

        # remember
        self.nextBumpX             = bumpX
        self.nextBumpY             = bumpY
        self.nextBumpTime          = self.simEngine.currentTime() + timetobump
        log.debug(f'Dotbot {self.dotBotId} next bump at ({bumpX}, {bumpY}) at {self.nextBumpTime}')

        if stopTime < self.nextBumpTime:
            # schedule movement timeout
            self.simEngine.schedule(stopTime, self._movementTimeoutCb, tag=f'{self.dotBotId}_movementTimeout')
            log.debug(f'next stop for {self.dotBotId} scheduled for {self.simEngine.currentTime() + stopTime}')
        else:
            # schedule the bump event
            self.simEngine.schedule(self.nextBumpTime, self._bumpSensorCb, tag=f'{self.dotBotId}_bumpSensorCb')
            log.debug(f'next bump for {self.dotBotId} scheduled for {self.nextBumpTime}')

    def computeCurrentPosition(self):
        '''
        Compute the current position based on previous position and movement.
        '''

        # shorthand
        now = self.simEngine.currentTime()
        
        # compute current position based on where it was and where it's going
        if self.currentSpeed==0:
            (newX,newY)  = (self.x,self.y)
        else:
            (newX,newY)  = u.computeCurrentPosition(
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

        return (self.nextBumpX, self.nextBumpY)

    # ======================== private =========================================

    #=== bump sensor interrupt handler
    
    def _bumpSensorCb(self):
        '''
        Bump sensor triggered
        '''

        assert self.simEngine.currentTime() == self.nextBumpTime

        # update my position
        (self.x, self.y) = self.computeCurrentPosition()
        log.debug(f'DotBot {self.dotBotId} stopped at ({self.x}, {self.y}) at {self.simEngine.currentTime()}')
        log.debug(
            f'DotBot {self.dotBotId} expected position at ({self.nextBumpX}, {self.nextBumpY}) at {self.nextBumpTime}'
        )

        # DotBot bumped
        self.hasJustBumped = True

        # stop movement and send notification
        self._stopAndTransmit()

    def _movementTimeoutCb(self):
        '''
        DotBot reached target before next bump
        '''

        # update my position
        (self.x, self.y)        = self.computeCurrentPosition()

        # DotBot did not bump
        self.hasJustBumped      = False

        # stop movement and send notification
        self._stopAndTransmit()

    def _estimatedPdrCb(self):
        '''
        send estimated PDR to orchestrator to update on PDR status
        '''

        self.simEngine.schedule(self.simEngine.currentTime() + self.estimatedPdrPeriod, self._estimatedPdrCb)

        # number of packets received to number of packets expected, to give an estimate of PDR
        self.estimatedPdr         = self.numPacketReceived / self.estimatedPdrPeriod

        # reset packet count
        self.numPacketReceived = 0

        # send notification with updates estimated PDR
        self._transmit()

    def _stopAndTransmit(self):

        # update notification ID
        self.seqNumNotification += 1

        # stop moving
        self.currentSpeed        = 0

        # remember how long DotBot moved for
        self.movementDuration      = self.simEngine.currentTime() - self.tsMovementStart

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
            'movementDuration':   self.movementDuration,
            'seqNumNotification': self.seqNumNotification,
            'hasJustBumped':      self.hasJustBumped,
            'estimatedPdr':       self.estimatedPdr,
        }

        # hand over to wireless
        self.wireless.transmit(
            frame     = frameToTx,
            sender    = self,
        )

        # schedule retransmission
        self.simEngine.schedule(
            ts        = self.simEngine.currentTime() + self.RETRY_TIMEOUT_S,
            cb        = self._transmit,
            tag       = "retransmission_DotBot_{}".format(self.dotBotId),
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
        '''
        computes when/where dotbot bumps into obstacle next
        '''

        assert speed != 0

        bumpX           = None
        bumpY           = None
        timetobump      = None
        intersectPoints = []


        # find slope of movement trajectory
        if heading not in [0, 90, 180, 270]:
            slope = math.tan(math.radians(heading-90))

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
                    # line is heading away from obstacle horizontally
                    # skip this obstacle
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
                    # line is heading away from obstacle vertically
                    # skip this obstacle
                    continue

                x = currentX
                y = ymax if heading == 0 else ymin

                if xmin <= round(x, 10) <= xmax and ymin <= round(y, 10) <= ymax:
                    intersectPoints += [(x, y)]

            else:
                # general case

                (topX, bottomX, leftY, rightY) = (None, None, None, None)

                if (
                    # line moving right upwards and starts to the right or top of obstacle
                    ((0   < heading < 90   and (xmax <= currentX or currentY <= ymin))) or
                    # line moving right downwards and starts to the right or bottom of obstacle
                    ((90  < heading < 180  and (xmax <= currentX or ymax <= currentY))) or
                    # line moving left downwards and starts to the left or bottom of obstacle
                    ((180 < heading < 270  and (currentX <= xmin or ymax <= currentY))) or
                    # line moving left upwards and starts to the left or top of obstacle
                    ((270 < heading < 360  and (currentX <= xmin or currentY <= ymin)))
                ):
                    # skip this obstacle
                    continue

                # compute intersection points with obstacles

                if 0 < heading < 90:
                    # top right quadrant

                    bottomX = ((ymax - currentY) / slope) + currentX      # intersection with bottom obstacle border (y=ymax)
                    leftY   = (xmin - currentX)*slope + currentY          # intersection with left obstacle border   (x=xmin)

                if 90 < heading < 180:
                    # bottom right quadrant

                    topX    = ((ymin - currentY) / slope) + currentX       # intersection with top obstacle border    (y=ymin)
                    leftY   = (xmin - currentX)*slope + currentY           # intersection with left obstacle border   (x=xmin)

                if 180 < heading < 270:
                    # bottom left quadrant

                    topX    = ((ymin - currentY) / slope) + currentX        # intersection with top obstacle border    (y=ymin)
                    rightY  = (xmax - currentX)*slope + currentY            # intersection with right obstacle border  (x=xmax)

                if 270 < heading < 360:
                    # top left quadrant
                    bottomX = ((ymax - currentY) / slope) + currentX       # intersection with bottom obstacle border (y=ymax)
                    rightY  = (xmax - currentX)*slope + currentY           # intersection with right obstacle border  (x=xmax)

                # check if intersection points are on obstacle
                if topX and xmin <= round(topX, 10) <= xmax:
                    intersectPoints += [(topX, ymin)]
                if bottomX and xmin <= round(bottomX, 10) <= xmax:
                    intersectPoints += [(bottomX, ymax)]
                if leftY and ymin <= round(leftY, 10) <= ymax:
                    intersectPoints += [(xmin, leftY)]
                if rightY and ymin <= round(rightY, 10) <= ymax:
                    intersectPoints += [(xmax, rightY)]

        if intersectPoints:

            # find closest intersection point to current position
            distances      = [((x,y), u.distance((currentX, currentY), (x, y))) for (x, y) in intersectPoints]
            distances      = sorted(distances, key=lambda e: e[1])
            (bumpX, bumpY) = distances[0][0]

            # find bump time
            timetobump     = u.distance((currentX, currentY), (bumpX, bumpY)) / speed

            assert bumpX  >= 0 and bumpY >= 0

            # round
            bumpX          = round(bumpX, 3)
            bumpY          = round(bumpY, 3)
        else:
            log.error("NO INTERSECT FOUND")

        # return where and when robot will bump
        return (bumpX, bumpY, timetobump)
