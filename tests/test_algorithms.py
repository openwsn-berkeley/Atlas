import Planning

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


def test_empty_A_star():
    planner = Planning.AStar()
    planner.map.explore_cell(0,0)
    planner.map.explore_cell(0, 0.5)
    path = planner.computePath((0, 0), (0, 1))
    assert path == [(0,0.5),(0,1)]

def test_no_path_A_star():
    planner = Planning.AStar()
    planner.map.add_obstacle(5, 0)
    path = planner.computePath((0, 0), (5, 0))

    assert path is None

def test_no_target_neighbors_A_star():
    planner = Planning.AStar()
    for i in [-0.5, 0, 0.5]:
        for j in [-0.5, 0, 0.5]:
            if i == j == 0:
                continue
            planner.map.add_obstacle(5 + i, j)

    path = planner.computePath((0, 0), (5, 0))

    assert path is None

def test_some_obstacles_A_star():
    planner = Planning.AStar()
    planner.map.explore_cell(0, 0)
    planner.map.explore_cell(0.5, 0)
    planner.map.explore_cell(0.5, 0.5)
    planner.map.explore_cell(0.5, 1)
    planner.map.add_obstacle(0, 0.5)
    planner.map.add_obstacle(-0.5, 0.5)
    path = planner.computePath((0, 0), (0, 1))
    assert path == [(0.5,0.5), (0.0, 1.0)]

