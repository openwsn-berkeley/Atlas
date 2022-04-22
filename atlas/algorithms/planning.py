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

import SimEngine

import Logging


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

    def __init__(self, map=None, radius=10, start_x=None, start_y=None, settings={}, map_kwargs={}):
        self.map = map or Map(cell_class=self.Cell, **map_kwargs)
        self.assigned_relays = set()   # robots assigned to become relays
        self.targeted_relays = set()   # relay robots that have been given a target position
        self.relay_positions = set()   # all potential positions to be assigned to relays
        self.radius          = radius
        self.relay_settings  = settings
        self.last_num_explored_cells = 0
        self.simEngine     = SimEngine.SimEngine()
        self.logger        = Logging.PeriodicFileLogger()

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

        self.frontier_cells = [] # all frontier boundary cells

        self.not_frontiers = set()
        self.simEngine     = SimEngine.SimEngine()
        self.logger        = Logging.PeriodicFileLogger()

    def allocateTarget(self, dotbot_position):
        '''
        Allocates a target to a dotBot based on distance to robot and distance to starting point.
        '''

        alloc_target   = None
        alloc_frontier = None

        while not alloc_target:

            # end of mission if no frontier cells left

            self.updateFrontierBoundary(dotbot_position)
            random.shuffle(self.frontier_cells)
            if not self.frontier_cells:
                #self.simEngine.schedule(self.simEngine.currentTime()+120,self.simEngine.completeRun)
                return

            closest_frontiers_to_start = self.findDistanceToStart(dotbot_position, self.frontier_cells)

            if closest_frontiers_to_start:
                alloc_frontier = self.findClosestTargetsToRobot(dotbot_position, closest_frontiers_to_start)
            else:
                alloc_frontier = self.findClosestTargetsToRobot(dotbot_position, self.frontier_cells)

            assert alloc_frontier

            alloc_target = alloc_frontier.position(_local=False)

        #self.frontier_cells.remove(alloc_frontier)

        return alloc_target

    def updateFrontierBoundary(self, current_cell):
        for cell in self.map.neighbors(self.map.cell(*current_cell, local=False), explored_ok=False):
            if cell not in self.frontier_cells:
                self.frontier_cells.append(cell)

    def findDistanceToStart(self, dotbot_position, targets):
        '''
        take input and assign each cell and distance to start rank
        '''

        targetsAndDistances2start = []

        for t in targets:
            t_position = t.position(_local=False)
            if t_position != dotbot_position:
                targetsAndDistances2start += [(t, u.distance((self.ix,self.iy), t_position))]

        assert  targetsAndDistances2start
        min_target_distance = sorted(targetsAndDistances2start, key=lambda item: item[1])[0][1]
        closest_targets_to_start = [c for (c, d) in targetsAndDistances2start if d == min_target_distance]
        closest_targets = closest_targets_to_start

        return closest_targets

    def findClosestTargetsToRobot(self, dotbot_position, targets):
        '''
        find closest 5 targets to robot
        '''
        targetsAndDistances2db = []

        for t in targets:
            t_position = t.position(_local=False)
            if t_position != dotbot_position:
                targetsAndDistances2db += [(t, u.distance(dotbot_position, t_position))]

        assert targetsAndDistances2db
        min_target_distance = sorted(targetsAndDistances2db, key=lambda item: item[1])[0][1]
        closest_targets_to_dotbot = [c for (c, d) in targetsAndDistances2db if d == min_target_distance]
        closest_target = random.choice(closest_targets_to_dotbot)

        return closest_target


""" Relay Recovery Placement"""

class Recovery(RelayPlanner):
    '''
    Relay placement based on Recovery algorithm.
    '''

    def assignRelay(self, robots_data):

        relay = None
        for robot in robots_data:

            if robot['heartbeat'] > self.relay_settings['minPdrThreshold']:
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
            if value[0] >= self.relay_settings['bestPdrThreshold']:
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
        NUM_CELLS_PER_RELAY = 400   #(20x20m)^2 if we assume 20m the max range of acceptable communication
        num_cells_explored = len(self.map.explored) + len(self.map.obstacles)
        last_num_cells_explored = self.last_num_explored_cells

        if (num_cells_explored - last_num_cells_explored) >= NUM_CELLS_PER_RELAY:
            self.last_num_explored_cells = num_cells_explored
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
        self.next_relay_chain_positions = set()


    def assignRelay(self, robots_data):
        RANGE_DISTANCE   = 20   # FIXME: replace 20 with a variable and add logic behind it
        CRITICAL_PDR     = 0.2
        lost_bot         = None  # A robot that has lost connection, we want to build a relay chain to to restore connectivity
        available_relays = []
        for robot in robots_data:
            if robot['heartbeat'] <= CRITICAL_PDR:
                lost_bot = robot
                break

        if not lost_bot:
            return []

        assert available_relays
        available_relays = [r for r in robots_data if (r != lost_bot and r["ID"] not in self.assigned_relays)]

        relay = random.choice(available_relays)
        if relay["ID"] not in self.assigned_relays:
            self.assigned_relays.add(relay["ID"])

        if self.next_relay_chain_positions:
            return relay["ID"]

        start_to_lostBot_distance         = [(u.distance((lost_bot['x'], lost_bot['y']), (self.ix, self.iy)), (self.ix, self.iy))]
        if self.relay_positions:
            relays_to_lostBot_distances       = [(u.distance((lost_bot['x'], lost_bot['y']), robot_pos), robot_pos) for robot_pos in self.relay_positions]
            all_distances                     = start_to_lostBot_distance + relays_to_lostBot_distances
            min_distance                      = min([d for d, r in all_distances])
            closest_relay                     = [r for d, r in all_distances if d == min_distance][0]
            closest_relay                     = closest_relay
            closest_relay_to_lostBot_distance = u.distance(closest_relay,(lost_bot['x'], lost_bot['y']))
        else:
            closest_relay                     = (self.ix, self.iy)
            closest_relay_to_lostBot_distance = start_to_lostBot_distance[0][0]

        distances_ratio                   = RANGE_DISTANCE/closest_relay_to_lostBot_distance
        num_relays                        = int(closest_relay_to_lostBot_distance/RANGE_DISTANCE)

        if num_relays == 0:
            return []

        # equations bellow from https://math.stackexchange.com/a/1630886

        previous_relay_in_chain = closest_relay
        for idx in range(num_relays):
            x0, y0   = previous_relay_in_chain
            x1, y1   = (lost_bot['x'],lost_bot['y'])
            t        = distances_ratio
            next_pos = (int(((1-t)*x0 + t*x1)),int(((1-t)*y0+ t*y1)))
            self.next_relay_chain_positions.add(next_pos)
            previous_relay_in_chain = next_pos

        return relay["ID"]

    def positionRelay(self, relay):
        if self.next_relay_chain_positions:
            x, y = self.next_relay_chain_positions.pop()
        else:
            return None

        self.targeted_relays.add(relay['ID'])
        self.relay_positions.add((x, y))
        cell = self.map.cell(*(x, y), local=False)

        if cell.explored is True and cell.obstacle is False:
            return x, y

        open_cells = [cell]
        closed_cells = []

        for idx, c in enumerate(open_cells):
            open_cells.pop(0)
            for n in self.map.neighbors(self.map.cell(*c.position(_local=False), local=False), explored_ok=True):
                if n.explored is True and n.obstacle is False:
                    x, y = n.position(_local=False)
                    return x, y
                elif n not in closed_cells and n not in open_cells:
                    open_cells.append(n)
            closed_cells.append(c)
            assert idx < len(self.map.explored)

        return None



""" No Relay Placement"""
class NoRelays(RelayPlanner):
    '''
    No relays to be assigned.
    '''

    def assignRelay(self, robots_data):
        return

    def positionRelay(self, relay):
        return
