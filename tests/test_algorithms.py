import pytest

from atlas.algorithms.planning import Map, AStar

def _xy2hCell(x, y):
    xsteps = int(round((x - 1) / 0.5, 0))
    cx = 1 + xsteps * 0.5
    ysteps = int(round((y - 1) / 0.5, 0))
    cy = 1 + ysteps * 0.5

    return (cx, cy)

def markTraversedCells(startX, startY, stopX, stopY):  # TODO: unit test
    returnVal = []

    x_sign = 2 * int(startX < stopX) - 1
    y_sign = 2 * int(startY < stopX) - 1

    step_size = 0.5

    x = startX
    while True:
        x += x_sign * step_size
        if (x > stopX if x_sign == 1 else x < stopX):
            break

        y = startY + (((stopY - startY) * (x - startX)) / (stopX - startX))

        (cx, cy) = _xy2hCell(x, y)
        returnVal += [(cx, cy)]

    # scan vertically
    y = startY
    while True:
        y += y_sign * step_size
        if (y > stopY if y_sign == 1 else y < stopY):
            break

        x = startX + (((stopX - startX) * (y - startY)) / (stopY - startY))

        (cx, cy) = _xy2hCell(x, y)
        returnVal += [(cx, cy)]

    # filter duplicates
    returnVal = list(set(returnVal))

    return returnVal

def test_map_expand():
    map = Map(width=20, height=20, scale=0.5, factor=2)
    assert map.width == 20 and map.height == 20
    for (x, y) in map.all_coordinates(map.width, map.height, map.scale):
        assert abs(x) <= map.width // 2 and abs(y) <= map.height // 2 and map.cell(x, y) is not None

    assert map.width == 20 and map.height == 20
    assert map.cell(30, 30, expand=False) is None
    assert map.width == 20 and map.height == 20
    assert map.cell(30, 30) is not None
    assert map.width == 80 and map.height == 80
    assert map.cell(45, 27) is not None
    assert map.width == 160 and map.height == 160

    for (x, y) in map.all_coordinates(map.width, map.height, map.scale):
        assert abs(x) <= map.width // 2 and abs(y) <= map.height // 2 and map.cell(x, y) is not None

def test_empty_A_star():
    planner = AStar()
    path = planner.computePath((0, 0), (5, 0))

    assert len(path) == 10

def test_no_path_A_star():
    planner = AStar()
    planner.map.add_obstacle(5, 0)
    path = planner.computePath((0, 0), (5, 0))

    assert path is None

def test_no_target_neighbors_A_star():
    planner = AStar()
    for i in [-0.5, 0, 0.5]:
        for j in [-0.5, 0, 0.5]:
            if i == j == 0:
                continue
            planner.map.add_obstacle(5 + i, j)

    path = planner.computePath((0, 0), (5, 0))

    assert path is None

def test_some_obstacles_A_star():
    planner = AStar()
    for i in [-0.5, 0, 0.5]:
        for j in [-0.5, 0]:
            if i == j == 0:
                continue
            planner.map.add_obstacle(1 + i, j)

    planner.map.add_obstacle(0.5, 0.5)

    path = planner.computePath((0, 0), (1, 0))

    assert len(path) == 4

def test_some_obstacles_A_star_offset():
    planner = AStar(map_kwargs={"offset" : (30, 30)})
    for i in [-0.5, 0, 0.5]:
        for j in [-0.5, 0]:
            if i == j == 0:
                continue
            planner.map.add_obstacle(1 + i, j)

    planner.map.add_obstacle(0.5, 0.5)

    path = planner.computePath((0, 0), (1, 0))

    assert len(path) == 4
