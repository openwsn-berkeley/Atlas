import requests
import Utils as u

class Connector():

    def __init__(self):

        self.scale                        = 3

        self.realDotBotsView              = dict([
            (
                i,
                {
                    # physical address
                    "address":             self.getActiveRealDotbots()[i-1]['address'],
                    # current position of DotBot
                    'x':                   self.getActiveRealDotbots()[i-1]['position_history'][-1]['x'],
                    'y':                   self.getActiveRealDotbots()[i-1]['position_history'][-1]['y'],
                    # next bump coordinates
                    'nextBumpX':           None,
                    'nextBumpY':           None,
                    # taget position coordinates
                    'targetX':             None,
                    'targetY':             None,
                }
            ) for i in range(1, len(self.getActiveRealDotbots())+1)
        ])

    def getActiveRealDotbots(self):
        # Set the base URL for the API
        base_url = "http://localhost:8000"

        # Set the endpoint for the API
        endpoint = "/controller/dotbots"

        response = requests.get(base_url + endpoint)

        return response.json()

    def computeRealCoordinates(self, virtualX, virtualY):
        return  ((virtualX)/self.scale, (virtualY)/self.scale)

    def computeVirtualCoordinates(self, realX, realY):
        print('real coordinates',realX, realY)
        return  (realX*self.scale, realY*self.scale)

    def getRealPositions(self):
        dotBots = self.getActiveRealDotbots()
        return [self.computeVirtualCoordinates(dotBot['position_history'][-1]['x'], dotBot['position_history'][-1]['y']) for dotBot in dotBots]


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

        # get real DotBot position
        (currentX, currentY)   = (self.realDotBotsView[dotBotId]['x'], self.realDotBotsView[dotBotId]['y'] )

        (nextX, nextY)         =  (self.realDotBotsView[dotBotId]['targetX'], self.realDotBotsView[dotBotId]['targetY'])
        if self.realDotBotsView[dotBotId]['nextBumpX']:

            # compute distance between current position and target position
            dotBotToTargetDistance = u.distance((currentX, currentY), (
            self.realDotBotsView[dotBotId]['targetX'], self.realDotBotsView[dotBotId]['targetY']))

            # compute distance between current position and next bump position
            dotBotToBumpDistance   = u.distance((currentX, currentY),(self.realDotBotsView[dotBotId]['nextBumpX'], self.realDotBotsView[dotBotId]['nextBumpY']))

            if dotBotToBumpDistance < dotBotToTargetDistance:
                (nextX, nextY)    = (self.realDotBotsView[dotBotId]['nextBumpX'], self.realDotBotsView[dotBotId]['nextBumpY'])


        # scale positions
        (scaledNextX, scaledNextY)     = self.computeRealCoordinates(nextX, nextY)

        print('target',nextX, nextY, 'scaled to reality is:', scaledNextX, scaledNextY)

        #send API
        while True:
            self.moveRawRealDotbot(self.realDotBotsView[dotBotId]['address'], scaledNextX, scaledNextY)
            (realX, realY) = self.getRealPositions()[dotBotId-1]
            print(realX, realY, nextX, nextY)
            print('here')
            if  (nextX-0.2 <= realX<= nextX+0.2) and (nextY-0.2 <= realY <= nextY+0.2):
                print('DotBot arrived')
                break





