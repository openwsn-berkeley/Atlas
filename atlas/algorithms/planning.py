"""
Algorithmic implementation of robot motion planning algorithms.
E.g., BFS, Djikstra's, A*, D* Lite, RRT

Created by: Felipe Campos, fmrcampos@berkeley.edu
Date: Mon, Oct 4, 2021
"""

import abc

import collections

import random

from functools import wraps

import time

import Utils as u

import numpy as np

from typing import Optional, Tuple, List, Any

from atlas.datastructures import PriorityQueue

'''
NOTES:
- Maybe include abstract graph representation (list of nodes or otherwise idk) that easily maps back to Atlas rep
- This allows for more general algorithmic implementation, but may not make sense if we're always doing 2D stuff
- It's likely that each implementation will define it's own graph structure (with or without costs etc.)
- So maybe we define a basic graph class and extend from there?
'''

def timeit(my_func):
    @wraps(my_func)
    def timed(*args, **kw):
        tstart = time.time()
        output = my_func(*args, **kw)
        tend = time.time()

        print('"{}" took {:.3f} ms to execute\n'.format(my_func.__name__, (tend - tstart) * 1000))
        return output

    return timed

""" Abstract Base Classes """

class Cell(abc.ABC):
    def __init__(self, x, y, map, explored=False, obstacle=False, unreachable=False):
        self.x = x
        self.y = y

        self.parent_map = map

        self.explored = explored
        self.obstacle = obstacle
        self.unreachable = unreachable

    def position(self, _np=False, _local=True):
        x, y = self.x, self.y
        if not _local:
            off = self.parent_map.offset
            x += off[0]
            y += off[1]
        return np.array([x, y]) if _np else (x, y)

    def distance(self, cell):
        return np.linalg.norm(cell.position(True) - self.position(True))

    @property
    def explored(self):
        return self.position(_local=False) in self.parent_map.explored

    @explored.setter
    def explored(self, value: bool):
        self.parent_map.explored.add(self.position(_local=False)) if value else self.parent_map.explored.discard(self.position(_local=False))

    @property
    def obstacle(self):
        return self.position(_local=False) in self.parent_map.obstacles

    @obstacle.setter
    def obstacle(self, value: bool):
        self.parent_map.obstacles.add(self.position(_local=False)) if value else self.parent_map.obstacles.discard(self.position(_local=False))

    @property
    def unreachable(self):
        return self.position(_local=False) in self.parent_map.unreachable

    @unreachable.setter
    def unreachable(self, value:bool):
        self.parent_map.unreachable.add(self.position(_local=False)) if value else self.parent_map.unreachable.discard(self.position(_local=False))

    def __repr__(self):
        return f"Global: {self.position(_local=False)} | Local: {self.position()} | Explored: {self.explored} | Obstacle {self.obstacle}"

class Map(abc.ABC):
    # TODO: create a function that maps coordinates here to global coordinates via a translation (and possible a rotation later on)

    def __init__(self, width=100, height=100, scale=0.5, cell_class=Cell, offset=(0, 0), factor=2):
        self.width = width
        self.height = height
        self.scale = scale

        self.offset = offset
        self.factor = factor

        self.explored = set()
        self.obstacles = set()
        self.unreachable = set()

        self.cell_class = cell_class
        self.cells = {
            (x, y) : self.create_cell(x, y) for (x, y) in
            self.all_coordinates(width, height, scale)
        }

        self.cell(0, 0).explored = True

    def create_cell(self, x, y):
        return self.cell_class(x, y, self)

    def cell(self, x, y, local=True, **kwargs):
        return self._cell(x, y, **kwargs) if local else self._cell(x - self.offset[0], y - self.offset[1], **kwargs)

    def xy2hCell(self, x, y):
        xsteps = int(round((x - 1) / 0.5, 0))
        cx = 1 + xsteps * 0.5
        ysteps = int(round((y - 1) / 0.5, 0))
        cy = 1 + ysteps * 0.5

        return (cx, cy)

    def _cell(self, x, y, expand=False):
        if (x, y) not in self.cells:
            if expand:
                self._expand()
            else:
                self.cells[(x, y)] = self.create_cell(x, y)
        return self.cells.get((x, y))

    @staticmethod
    def all_coordinates(width, height, scale=0.5):
        # FIXME: this won't work for scales that aren't 0.5, need to start from 0 and branch out
        width_bound, height_bound = width // 2, height // 2
        for x in np.arange(-width_bound, width_bound + scale, scale):
            for y in np.arange(-height_bound, height_bound + scale, scale):
                yield (x, y)

    def _expand(self): # NOTE: could optimize, but amortized so not a huge deal
        height, width = self.height * self.factor, self.width * self.factor
        for (x, y) in self.all_coordinates(width, height, self.scale):
            if abs(x) >= self.width // 2 or abs(y) >= self.height // 2:
                coords = (x, y)
                self.cells[coords] = self.create_cell(*coords)

        self.height, self.width = height, width

    def add_obstacle(self, x, y, local=False):
        self._add_obstacle(self.cell(x, y, local))

    def _add_obstacle(self, cell):
        cell.obstacle = True

    def remove_obstacle(self, x, y, local=False):
        self._remove_obstacle(self.cell(x, y, local))

    def _remove_obstacle(self, cell):
        cell.obstacle = False

    def add_unreachable(self, x, y, local=False):
        self._add_unreachable(self.cell(x, y, local))

    def _add_unreachable(self, cell):
        cell.unreachable = True

    def remove_unreachable(self, x, y, local=False):
        self._remove_unreachable(self.cell(x, y, local))

    def _remove_unreachable(self, cell):
        cell.unreachable = False

    def explore_cell(self, x, y, local=False):
        self._explore_cell(self.cell(x, y, local))

    def _explore_cell(self, cell):
        cell.explored = True

    def unexplore_cell(self, x, y, local=False):
        self._unexplore_cell(self.cell(x, y, local))

    def _unexplore_cell(self, cell):
        cell.explored = False

    def cell_neighbors(self, x, y):
        return self.neighbors(self.cell(x, y))

    def neighbors(self, cell, obstacle_ok=False, explored_ok=True):
        neighbors = []
        for dx in [-self.scale, 0, self.scale]:
            for dy in [-self.scale, 0, self.scale]:
                neighbor = self.cell(cell.x + dx, cell.y + dy)
                if neighbor and neighbor != cell and \
                        (obstacle_ok or not neighbor.obstacle) and (explored_ok or not neighbor.explored):
                    neighbors.append(neighbor)

        return neighbors

class TargetSelector(abc.ABC):
    class Cell(Cell):
        pass

    def __init__(self, map=None, map_kwargs={}):
        self.map = map or Map(cell_class=self.Cell, **map_kwargs)

    @abc.abstractmethod
    def allocateTarget(self, *args, **kwargs):
        ...

class PathPlanner(abc.ABC):
    class Cell(Cell):
        pass

    def __init__(self, map=None, map_kwargs={}):
        self.map = map or Map(cell_class=self.Cell, **map_kwargs)

    @abc.abstractmethod
    def computePath(self, *args, **kwargs) -> Optional[List[Any]]: # TODO: define the type of object that the path should be comprised of, likely a cell object or tuple
        ...

class RelayPlanner(abc.ABC):
    class Cell(Cell):
        pass

    def __init__(self, map=None, radius=10, start_x=None, start_y=None, map_kwargs={}):
        self.map = map or Map(cell_class=self.Cell, **map_kwargs)
        self.assigned_relays = set()   # robots assigned to become relays
        self.targeted_relays = set()   # relay robots that have been given a target position
        self.relay_positions = set()   # all potential positions to be assigned to relays
        self.radius          = radius

    @abc.abstractmethod
    def assignRelay(self, robots_data):
        ...

    @abc.abstractmethod
    def positionRelay(self, relay):
        ...

""" Implementations """

""" BFS """

class BFS(PathPlanner):

    def computePath(self, start_coords: Tuple[float, float], target_coords: Tuple[float, float]) -> Optional[List[Any]]: # TODO: have type definitions
        '''
        Path planning algorithm (BFS in this case) for finding path to target
        '''
        #print(f"{start_coords} to {target_coords} Searching........", end="\r")
        t0 = time.time()
        start = self.map.cell(*start_coords, local=False)
        target = self.map.cell(*target_coords, local=False)

        visited, toVisit = set(), collections.deque([start])

        if target.obstacle or not self.map.neighbors(target):
            return None

        # TODO: when it returns None, orchestrator should handle removing target on it's own side
        path = []
        while toVisit:
            node = toVisit.popleft()
            visited.add(node)

            if node == target:
                t1 = time.time()
                #print(f"{start_coords} to {target_coords} Done ............. Took {t1 - t0}s to search", end="\r")

                return path

            for neighbor in self.map.neighbors(node):
                if neighbor not in visited:
                    toVisit.append(neighbor)
            if node != start:
                path.append(node.position(_local=False))


""" A Star """

class AStar(PathPlanner):
    Q = True
    ID = 0

    def __init__(self, map=None, map_kwargs={}):
        super().__init__(map=map, map_kwargs=map_kwargs)


    class Cell(Cell):
        def __init__(self, x, y, map, g=0, h=0,
                     parent=None, **kwargs):
            super().__init__(x, y, map, **kwargs)
            self.parent_map.hcosts = {}
            self.parent_map.gcosts = {}
            self.parent_map.parents = {}
            self.set_costs(g, h)
            self.parent = parent


        def __lt__(self, other):
            return self.hCost < other.hCost

        def reset(self):
            self.parent_map.hcosts = {}
            self.parent_map.gcosts = {}
            self.parent_map.parents = {}

        def set_costs(self, g, h):
            # set key value of hcosts and gcosts in dictionary
            self.parent_map.hcosts[self.position()] = h
            self.parent_map.gcosts[self.position()] = g
            self.g = g
            self.h = h

        @property
        def parent(self):
            return self.parent_map.parents.get(self.position())

        @parent.setter
        def parent(self, value):
            self._parent = value
            self.parent_map.parents[self.position()] = value

        @property
        def hCost(self):
            h = self.parent_map.hcosts.get(self.position())
            return 0 if h is None else h

        @property
        def gCost(self):
            g = self.parent_map.gcosts.get(self.position())
            return 0 if g is None else g

        @property
        def fCost(self):
            return self.hCost + self.gCost

        def priority(self):
            return (self.fCost, self)

    def computePath(self, start_coords: Tuple[float, float], target_coords: Tuple[float, float]) -> Optional[List[Any]]: # TODO: have type definitions
        '''
        Path planning algorithm (A* in this case) for finding shortest path to target
        '''
        #print(f"from {start_coords} to {target_coords} Searching........", end="\r")
        t0 = time.time()
        start = self.map.cell(*start_coords, local=False)
        target = self.map.cell(*target_coords, local=False)

        openCells = PriorityQueue() if self.Q else []
        openCells.put(*start.priority()) if self.Q else openCells.append(start)
        closedCells = set()

        path_avaliable = False

        for cell in self.map.neighbors(self.map.cell(*target.position(_local=False), local=False), explored_ok=True):
            if cell.explored is True and cell.obstacle is False:
                path_avaliable = True
                break

        if not path_avaliable:
            self.map.add_unreachable(*target_coords)
            return None

        if target.obstacle or not self.map.neighbors(target):
            return None


        # TODO: when it returns None, orchestrator should handle removing target on it's own side
        path = None

        while not openCells.empty() if self.Q else openCells:
            openCells = openCells if self.Q else sorted(openCells, key=lambda item: item.fCost)  # find open cell with lowest F cost # TODO: this should be a min_heap / priority queue!!!
            currentCell = openCells.get() if self.Q else openCells.pop(0)

            if currentCell is None:
                print("NO PATH!")
                return

            closedCells.add(currentCell)

            # FIXME: debug start cell parent infinite loop
            if currentCell == target:  # we have reached target, backtrack direct path
                path = []

                while currentCell != start:
                    if currentCell == None:
                        return None

                    path.append(currentCell.position(_local=False))
                    currentCell = currentCell.parent

                path.reverse()
                currentCell.reset()
                break

            for child in self.map.neighbors(currentCell): # TODO: should we randomize? make a flag and test if there's any difference
                gCost = currentCell.gCost + 1
                hCost = target.distance(child)

                # don't consider cell if same cell with lower fcost is already in open or closed cells
                if ((child in closedCells or child in openCells) and child.fCost <= gCost + hCost):
                    continue

                child.set_costs(gCost, hCost)
                child.parent = currentCell
                openCells.put(*child.priority()) if self.Q else openCells.append(child)


        t1 = time.time()
        #print(f"From {start_coords} to {target_coords} Done ............. Took {t1 - t0}s to search", end="\r")
        return path

""" Atlas Target Selector """

class AtlasTargets(TargetSelector):

    def __init__(self, start_x, start_y, num_bots, *args, **kwargs):

        # initialize parent
        super().__init__(*args, **kwargs)

        self.ix = start_x
        self.iy = start_y

        self.numDotBots = num_bots

        self.frontier_cells = set() # all frontier boundary cells

        self.not_frontiers = set()


    def allocateTarget(self, dotbot_position):
        '''
        Allocates a target to a dotBot based on distance to robot and distance to starting point.
        '''

        alloc_target = None

        while not alloc_target:

            # end of mission if no frontier cells left

            self.updateFrontierBoundary(dotbot_position)

            if not self.frontier_cells and dotbot_position != (self.ix,self.iy):
                return

            closest_frontiers_to_robot = self.findClosestTargetsToRobot(dotbot_position)
            alloc_frontier = self.findDistanceToStart(closest_frontiers_to_robot)
            alloc_target = alloc_frontier.position(_local=False)

        self.frontier_cells.discard(alloc_frontier)

        return alloc_target

    def updateFrontierBoundary(self, current_cell):
        for cell in self.map.neighbors(self.map.cell(*current_cell, local=False), explored_ok=False):
            self.frontier_cells.add(cell)

    def findDistanceToStart(self, targets):
        '''
        take input and assign each cell and distance to start rank
        '''
        targetsAndDistances2start = []
        for t in targets:
            t_position = t.position(_local=False)
            targetsAndDistances2start += [(t, u.distance((self.ix,self.iy), t_position))]

        min_target_distance = sorted(targetsAndDistances2start, key=lambda item: item[1])[0][1]
        closest_targets_to_start = [c for (c, d) in targetsAndDistances2start if d == min_target_distance]
        closest_target = closest_targets_to_start[0]
        return closest_target

    def findClosestTargetsToRobot(self, dotbot_position):
        '''
        find closest 5 targets to robot
        '''
        targetsAndDistances2db = []
        for t in self.frontier_cells:
            t_position = t.position(_local=False)
            if t_position != dotbot_position:
                targetsAndDistances2db += [(t, u.distance(dotbot_position, t_position))]

        min_target_distance = sorted(targetsAndDistances2db, key=lambda item: item[1])[0][1]
        closest_targets_to_dotbot = [c for (c, d) in targetsAndDistances2db if d == min_target_distance]
        closest_targets = closest_targets_to_dotbot
        return closest_targets


""" Relay Recovery Placement"""

class Recovery(RelayPlanner):
    '''
    Relay placement based on Recovery algorithm.
    '''

    def assignRelay(self, robots_data):

        relay = None
        for robot in robots_data:

            if robot['heartbeat'] > 0.7:
                continue
            if robot['ID'] in self.targeted_relays:
                continue

            relay = robot['ID']
            break

        return relay

    def positionRelay(self, relay):
        x = None
        y = None

        pdrHistory = relay['pdrHistory']
        pdrHistoryReversed = pdrHistory[::-1]
        for value in pdrHistoryReversed:
            if value[0] >= 0.8:
                bestPDRposition = value[1]
                x = bestPDRposition[0]
                y = bestPDRposition[1]
                break

        if not x and not y:
            return None

        if (x, y) not in self.map.obstacles and (x, y) not in self.relay_positions:
            self.relay_positions.add((x, y))
            self.targeted_relays.add(relay['ID'])
            return (x, y)

""" Relay Naive Placement"""

class Naive(RelayPlanner):
    '''
    Relay Placement algorithms based on random selection.
    '''

    def assignRelay(self, robots_data):
        num_cells_explored = len(self.map.explored) + len(self.map.obstacles)
        # FIXME: add logic to number of cells that define when this happens
        if (num_cells_explored % 200 == 0) and (len(self.assigned_relays) < (num_cells_explored / 200)):
            relay = random.choice(robots_data)
            self.assigned_relays.add(relay["ID"])
            return relay["ID"]

    def positionRelay(self, relay):
        x = relay['x']
        y = relay['y']
        self.relay_positions.add((x, y))
        self.targeted_relays.add(relay['ID'])
        return (x, y)

""" Relay Self-Healing Placement"""

class SelfHealing(RelayPlanner):
    '''
    Relay placement based on self-healing algorithm.
    Builds chain between an RX with fixed distance between every 2 nodes.
    '''

    def __init__(self, start_x, start_y, *args, **kwargs):

        # initialize parent
        super().__init__(*args, **kwargs)

        self.ix = start_x
        self.iy = start_y
        self.lostBots_and_data = []

    def assignRelay(self, robots_data):

        distances  = []
        need_relay = False

        for robot in robots_data:
            start_to_robot_distance = u.distance((robot['x'], robot['y']), (self.ix, self.iy))
            # FIXME: replace 30 with a variable and add logic behind it
            if start_to_robot_distance >= 30:
                need_relay = True
            else:
                continue

            if self.relay_positions:
                distances += [u.distance((robot['x'], robot['y']), robot_pos) for robot_pos in self.relay_positions]
                for distance in distances:
                    if distance <= 30:
                        need_relay = False
                        break

            if need_relay == True:
                if self.lostBots_and_data and robot in [lb['targetBot'] for lb in self.lostBots_and_data]:
                    # FIXME: do this in a smarter way
                    bot_to_save = [lostBot for lostBot in self.lostBots_and_data if lostBot['targetBot'] == robot][0]
                    x = ((robot['x'] + bot_to_save['relayPositions'][-1][0]) / 2)
                    y = ((robot['y'] + bot_to_save['relayPositions'][-1][1]) / 2)

                    relay_position = (x, y)
                    bot_to_save['relayPositions'] += [relay_position]

                else:
                    x = ((robot['x'] + self.ix) / 2)
                    y = ((robot['y'] + self.iy) / 2)
                    self.lostBots_and_data += [{'targetBot': robot, 'relayPositions': [(x, y)]}]

                relay = random.choice([r for r in robots_data if (r != robot)])
                self.assigned_relays.add(relay["ID"])
                return relay["ID"]


    def positionRelay(self, relay):
        targetChosen = random.choice(self.lostBots_and_data)

        (xp, yp) = targetChosen['relayPositions'][-1]
        (x, y) = self.map.xy2hCell(xp, yp)
        if (x, y) not in self.relay_positions and (x, y) not in self.map.obstacles:
            self.relay_positions.add(targetChosen['relayPositions'][-1])
            self.targeted_relays.add(relay['ID'])
            return (x, y)


""" No Relay Placement"""
class NoRelays(RelayPlanner):
    '''
    No relays to be assigned.
    '''

    def assignRelay(self, robots_data):
        return

    def positionRelay(self, relay):
        return
