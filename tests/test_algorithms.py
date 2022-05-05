
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


