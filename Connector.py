import requests
import Utils as u

class Connector():

    def __init__(self):

        self.realDotBotsView              = dict([
            (
                i,
                {
                    # physical address
                    "address":             self.getActiveRealDotbots()[i-1]['address'],
                    # current position of DotBot
                    'x':                   self.getActiveRealDotbots()[i-1]['lh2_position']['x'],
                    'y':                   self.getActiveRealDotbots()[i-1]['lh2_position']['y'],
                    # current heading and speed
                    'leftWheelSpeed':      0,
                    'rightWheelSpeed':     0,
                    # next bump coordinates
                    'nextBumpX':           None,
                    'nextBumpY':           None,
                    # taget position coordinates
                    'targetX':             None,
                    'targetY':             None,
                }
            ) for i in range(1, len(self.getActiveRealDotbots())+1)
        ])

        print(self.realDotBotsView)

    def getActiveRealDotbots(self):
        # Set the base URL for the API
        base_url = "http://localhost:8000"

        # Set the endpoint for the API
        endpoint = "/controller/dotbots"

        response = requests.get(base_url + endpoint)

        print(response.json())

        return response.json()

    def getRealCoordinates(self, virtualX, virtualY):
        return  ((0.2*virtualX)/0.5, (0.2*virtualY)/0.5)

    def getVirtualCoordinates(self, realX, realY):
        return  ((0.5*realX)/0.2, (0.5*realY)/0.2)

    def getRealInitialPositions(self):
        dotBots = self.getActiveRealDotbots()
        print(dotBots)
        return [self.getVirtualCoordinates(dotBot['lh2_position']['x'], dotBot['lh2_position']['y']) for dotBot in dotBots]


    def moveRawRealDotbot(self, address, x, y):
        "Control physical DotBot"

        # Set the base URL for the API
        base_url = "http://localhost:8000"

        # Set the endpoint for the API
        endpoint = '/controller/dotbots/{address}/0/waypoints'.format(address = address)

        # Set the data for the new user
        data = [{
            "x": x,
            "y": y,
            "z": 0,
        }]

        try:
            # Make the POST request to the endpoint
            response = requests.put(base_url + endpoint, json=data)

            # Check the status code of the response
            if response.status_code == 200:
                # Print the response data
                print(response.json())
            else:
                print("An error occurred:", response.status_code)
        except:
            pass


    def updateNextBumpCoordinates(self, dotBotId, nextBumpX, nextBumpY):
        self.realDotBotsView[dotBotId]['nextBumpX'] = nextBumpX
        self.realDotBotsView[dotBotId]['nextBumpY'] = nextBumpY

    def updateTargetCoordinates(self, dotBotId, targetCell):
        self.realDotBotsView[dotBotId]['targetX']   = targetCell[0]
        self.realDotBotsView[dotBotId]['targetY']   = targetCell[1]

    def setNextRealDotBotMovement(self, dotBotId):

        if not self.realDotBotsView[dotBotId]['targetX']:
            return

        # get real DotBot position
        (currentX, currentY)   = (self.realDotBotsView[dotBotId]['x'], self.realDotBotsView[dotBotId]['y'] )

        # compute distance between current position and target position
        dotBotToTargetDistance = u.distance((currentX, currentY),(self.realDotBotsView[dotBotId]['targetX'], self.realDotBotsView[dotBotId]['targetY']))

        # compute distance between current position and next bump position
        dotBotToBumpDistance   = u.distance((currentX, currentY),(self.realDotBotsView[dotBotId]['nextBumpX'], self.realDotBotsView[dotBotId]['nextBumpY']))

        # compute which point is closer
        (nextX, nextY)         = min([dotBotToTargetDistance, dotBotToBumpDistance])

        # scale positions
        (scaledX, scaledY)     = self.getRealCoordinates(nextX, nextY)

        # send API
        self.moveRawRealDotbot(self.realDotBotsView[dotBotId]['address'], scaledX, scaledY)
