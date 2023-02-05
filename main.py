import numpy as np
import imageio.v3 as iio
import math
import logging
from PIL import Image as img, ImageDraw
from timer import timer, get_timer


# logging.basicConfig(level=logging.DEBUG)

class Extents:
    _left = None
    _right = None
    _top = None
    _bottom = None

    def __init__(self, width, height):
        self._left = width
        self._right = 0
        self._top = height
        self._bottom = 0

    def left(self):
        return self._left

    def right(self):
        return self._right

    def top(self):
        return self._top

    def bottom(self):
        return self._bottom

    def add(self, point):
        if point is None:
            return;

        if point[0] is not None:
            self._left = min(self._left, point[0])
            self._right = max(self._right, point[0])

        if point[1] is not None:
            self._top = min(self._top, point[1])
            self._bottom = max(self._bottom, point[1])

    def height(self):
        return self._bottom - self._top

    def width(self):
        return self._right - self._left


def imageLightnessAt(rgb):
    (r, g, b) = rgb
    m = min(r, g, b)
    n = max(r, g, b)
    lightness = (int(m) + n) / 510.0
    return lightness


def darkEnough(rgb, x, y, tolerance):
    if rgb[0] == 255 and rgb[1] == 255 and rgb[2] == 255:
        return False

    if imageLightnessAt(rgb) < tolerance:
        return True

    return False


def find_top_edge(img, left, top, right, bottom, step, tolerance):
    for y in range(top, bottom, step):
        for x in range(left, right, step):
            rgb = img.getpixel((x, y));
            if darkEnough(rgb, x, y, tolerance):
                if step > 1:
                    try:
                        return find_top_edge(
                            img,
                            left=max(left, x - step),
                            top=max(top, y - step),
                            right=x,
                            bottom=y,
                            step=1,
                            tolerance=tolerance
                        )
                    except Exception:
                        return [x, y]
                return [x, y]

    if step > 1:
        return find_top_edge(
            img,
            left,
            top,
            right,
            bottom,
            1,
            tolerance
        )

    raise Exception("Didn't find any non-white pixels")


def find_left_edge(img, left, top, right, bottom, step, tolerance):
    for x in range(left, right, step):
        for y in range(top, bottom, step):
            rgb = img.getpixel((x, y))
            if darkEnough(rgb, x, y, tolerance):
                if step > 1:
                    try:
                        return find_left_edge(
                            img,
                            left=max(left, x - step),
                            top=max(top, y - step),
                            right=x,
                            bottom=y,
                            step=1,
                            tolerance=tolerance
                        )
                    except Exception:
                        return [x, y]
                return [x, y]

    if step > 1:
        return find_left_edge(
            img,
            left,
            top,
            right,
            bottom,
            1,
            tolerance
        )

    raise Exception("Didn't find any non-white pixels")


def find_right_edge(img, left, top, right, bottom, step, tolerance):
    for x in range(right - 1, left, -step):
        for y in range(top, bottom, step):
            rgb = img.getpixel((x, y))
            if darkEnough(rgb, x, y, tolerance):
                if step > 1:
                    try:
                        return find_right_edge(
                            img,
                            left=left,
                            top=max(top, y - step),
                            right=min(x + step, right),
                            bottom=bottom,
                            step=1,
                            tolerance=tolerance
                        )
                    except Exception:
                        return [x, y]
                return [x, y]

    if step > 1:
        return find_right_edge(
            img,
            left,
            top,
            right,
            bottom,
            1,
            tolerance
        )

    raise Exception("Didn't find any non-white pixels")


def find_bottom_edge(img, left, top, right, bottom, step, tolerance):
    for y in range(bottom - 1, top, -step):
        for x in range(left, right, step):
            rgb = img.getpixel((x, y))
            if darkEnough(rgb, x, y, tolerance):
                if step > 1:
                    try:
                        return find_bottom_edge(
                            img,
                            left=max(left, x - step),
                            top=top,
                            right=x,
                            bottom=min(y + step, bottom),
                            step=1,
                            tolerance=tolerance
                        )
                    except Exception:
                        return [x, y]
                return [x, y]

    if step > 1:
        return find_bottom_edge(
            img,
            left,
            top,
            right,
            bottom,
            1,
            tolerance
        )

    raise Exception("Didn't find any non-white pixels")

@timer(unit='s')
def crop(filename, **options):
    step = options.get('step', 1)
    tolerance = options.get('tolerance', 0.95)
    fadeGutters = options.get('fadeGutters', True)
    drawLines = options.get('drawLines', False)
    drawEllipses = options.get('drawEllipses', False)
    fadeColor = options.get('fadeColor', [255,255,255]);
    image = img.open(filename)

    height, width = image.height, image.width

    extents = Extents(width, height)

    # discover top edge
    topEllipse = find_top_edge(
        image,
        left=0,
        top=0,
        right=width,
        bottom=height,
        step=step,
        tolerance=tolerance
    )
    extents.add([None, topEllipse[1]])

    # bottom edge
    bottomEllipse = find_bottom_edge(
        image,
        left=0,
        top=extents.top(),
        right=width,
        bottom=height,
        step=step,
        tolerance=tolerance
    )
    extents.add([None, bottomEllipse[1]])

    # left edge
    leftEllipse = find_left_edge(
        image,
        left=0,
        top=extents.top(),
        right=width,
        bottom=extents.bottom() + 1,
        step=step,
        tolerance=tolerance
    )
    extents.add([leftEllipse[0], None])

    # right edge
    rightEllipse = find_right_edge(
        image,
        left=extents.right(),
        top=extents.top(),
        right=width,
        bottom=extents.bottom() + 1,
        step=step,
        tolerance=tolerance
    )
    extents.add([rightEllipse[0], None])

    coreWidth = extents.width() + 1
    coreHeight = extents.height() + 1
    gutterWidth = int(math.ceil(coreWidth * 0.05))
    gutterHeight = int(math.ceil(coreHeight * 0.05))

    finalWidth = int(coreWidth + gutterWidth * 2)
    finalHeight = int(coreHeight + gutterHeight * 2)

    cropped = image.crop((extents.left(), extents.top(), width, height))

    res = img.new("RGB", (finalWidth, finalHeight), "white")
    res.paste(cropped, (gutterWidth, gutterHeight))
    draw = ImageDraw.Draw(res, 'RGBA')

    # adjust the values after the crop
    topEllipse[0] -= extents.left()
    bottomEllipse[0] -= extents.left()
    leftEllipse[1] -= extents.top()
    rightEllipse[1] -= extents.top()

    if fadeGutters:
        slope = gutterHeight / gutterWidth
        # fade out the top and bottom gutters
        for y in range(0, gutterHeight):
            scalar = 255 - int((y / gutterHeight) * 255)
            localBottom = finalHeight - y
            draw.line((
                y / slope,
                y,
                finalWidth - y / slope,
                y,
            ), fill=(fadeColor[0], fadeColor[1], fadeColor[2], scalar), width=1)
            draw.line((
                y / slope,
                localBottom,
                finalWidth - y / slope,
                localBottom,
            ), fill=(fadeColor[0], fadeColor[1], fadeColor[2], scalar), width=1)

        # fade out the left and right gutters
        for x in range(0, gutterWidth):
            scalar = 255 - int((x / gutterWidth) * 255)
            localRight = finalWidth - x
            draw.line((
                x,
                x * slope,
                x,
                finalHeight - x * slope,
            ), fill=(fadeColor[0], fadeColor[1], fadeColor[2], scalar), width=1)
            draw.line((
                localRight,
                x * slope,
                localRight,
                finalHeight - x * slope,
            ), fill=(fadeColor[0], fadeColor[1], fadeColor[2], scalar), width=1)

    if drawEllipses:
        radius = (finalHeight * 0.1) / 2
        # left ellipse
        if (leftEllipse is not None):
            drawCircle(
                draw,
                gutterWidth,
                leftEllipse[1] + gutterHeight,
                radius,
                "#ff0000",
                1
            )

        # top ellipse
        drawCircle(
            draw,
            topEllipse[0] + gutterWidth,
            gutterHeight,
            radius,
            '#00ff00',
            1
        )

        # right ellipse
        if (rightEllipse is not None):
            drawCircle(
                draw,
                finalWidth - gutterWidth - 1,
                rightEllipse[1] + gutterHeight,
                radius,
                "#0000ff",
                1
            )

        # bottom ellipse
        drawCircle(
            draw,
            bottomEllipse[0] + gutterWidth,
            finalHeight - gutterHeight - 1,
            radius,
            '#ff00ff',
            1

        )

    if drawLines:
        lineColor = (0,255,255,32)
        for y in range(0, gutterHeight):
            # top line
            draw.line((
                gutterWidth,
                gutterHeight,
                finalWidth - gutterWidth - 1,
                gutterHeight,
            ), fill=lineColor, width=1)

            # bottom line
            draw.line((
                gutterWidth,
                finalHeight - gutterHeight - 1,
                finalWidth - gutterWidth - 1,
                finalHeight - gutterHeight - 1,
            ), fill=lineColor, width=1)

            # left line
            draw.line((
                gutterWidth,
                gutterHeight,
                gutterWidth,
                finalHeight - gutterHeight - 1,
            ), fill=lineColor, width=1)

            # right line
            draw.line((
                gutterWidth + coreWidth - 1,
                gutterHeight,
                gutterWidth + coreWidth - 1,
                finalHeight - gutterHeight - 1,
            ), fill=lineColor, width=1)

    return res


def drawCircle(draw, centerX, centerY, radius, color, width):
    draw.ellipse((
        centerX - radius,
        centerY - radius,
        centerX + radius,
        centerY + radius
    ),
        outline=color,
        width=width
    )


croppedImg = crop(
    './samples/figure.jpg',
    tolerance=0.95,
    drawEllipses=True,
    drawLines=True,
    step=10,
    fadeGutters=True,
    fadeColor=[0,255,255]
)
# plt.imshow(croppedImg)
iio.imwrite("./samples/cropped.png", croppedImg)

print("done")
