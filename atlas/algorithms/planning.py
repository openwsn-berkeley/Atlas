"""
Algorithmic implementation of robot motion planning algorithms.
E.g., BFS, Djikstra's, A*, D* Lite, RRT

Created by: Felipe Campos, fmrcampos@berkeley.edu
Date: Mon, Oct 4, 2021
"""

import abc
import heapq

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

""" Abstract Base Classes """

class Cell(abc.ABC):
    def __init__(self, x, y, map, explored=False, obstacle=False):
        self.x = x
        self.y = y

        self.parent_map = map

        self.explored = explored
        self.obstacle = obstacle

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

class Map(abc.ABC):
    # TODO: create a function that maps coordinates here to global coordinates via a translation (and possible a rotation later on)

    def __init__(self, width=50, height=50, scale=0.5, cell_class=Cell, offset=(0, 0), factor=2):
        self.width = width
        self.height = height
        self.scale = scale

        self.offset = offset
        self.factor = factor

        self.explored = set()
        self.obstacles = set()

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

    def _cell(self, x, y, expand=True):
        while expand and (x, y) not in self.cells:
            self._expand()
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

    def neighbors(self, cell, obstacle_ok=False):
        neighbors = []
        for dx in [-self.scale, 0, self.scale]:
            for dy in [-self.scale, 0, self.scale]:
                neighbor = self.cell(cell.x + dx, cell.y + dy)
                if neighbor and neighbor != cell and (obstacle_ok or not neighbor.obstacle):
                    neighbors.append(neighbor)

        return neighbors

class TargetSelector(abc.ABC):
    pass

class PathPlanner(abc.ABC):
    class Cell(Cell):
        pass

    def __init__(self, map=None, map_kwargs={}):
        self.map = map or Map(cell_class=self.Cell, **map_kwargs)

    @abc.abstractmethod
    def computePath(self, *args, **kwargs) -> Optional[List[Any]]: # TODO: define the type of object that the path should be comprised of, likely a cell object or tuple
        ...

""" Implementations """

""" A Star """

class AStar(PathPlanner):
    Q = False

    class Cell(Cell):
        def __init__(self, x, y, map, g=0, h=0, parent=None, **kwargs):
            super().__init__(x, y, map, **kwargs)
            self.set_costs(g, h)
            self.parent = parent

        def set_costs(self, g, h):
            self.gCost = g
            self.hCost = h

        @property
        def fCost(self):
            return self.hCost + self.gCost

        def priority(self):
            return (self.fCost, self)

    def computePath(self, start_coords: Tuple[float, float], target_coords: Tuple[float, float]) -> Optional[List[Any]]: # TODO: have type definitions
        '''
        Path planning algorithm (A* in this case) for finding shortest path to target
        '''
        start = self.map.cell(*start_coords, local=False)
        target = self.map.cell(*target_coords, local=False)

        openCells = PriorityQueue() if self.Q else []
        openCells.put(start.priority()) if self.Q else openCells.append(start)
        closedCells = set()

        if target.obstacle or not self.map.neighbors(target):
            return None

        # TODO: when it returns None, orchestrator should handle removing target on it's own side

        while openCells:
            openCells = openCells if self.Q else sorted(openCells, key=lambda item: item.fCost)  # find open cell with lowest F cost # TODO: this should be a min_heap / priority queue!!!
            currentCell = openCells.get() if self.Q else openCells.pop(0)
            closedCells.add(currentCell)

            if currentCell == target:  # we have reached target, backtrack direct path
                path = []

                while currentCell != start:
                    path.append(currentCell.position(_local=False))
                    currentCell = currentCell.parent

                path.reverse()
                return path

            for child in self.map.neighbors(currentCell): # TODO: should we randomize? make a flag and test if there's any difference
                gCost = currentCell.gCost + 1
                hCost = target.distance(child)

                # don't consider cell if same cell with lower fcost is already in open or closed cells
                if ((child in closedCells or child in openCells) and child.fCost < gCost + hCost):
                    continue

                child.set_costs(gCost, hCost)
                child.parent = currentCell
                openCells.put(*child.priority()) if self.Q else openCells.append(child)