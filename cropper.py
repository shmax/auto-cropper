import math
from PIL import Image, ImageDraw


class EdgeNotFoundException(Exception):
    """Raised when no edge pixel is found"""
    pass


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
            return

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


def image_lightness_at(rgb):
    (r, g, b) = rgb
    m = min(r, g, b)
    n = max(r, g, b)
    lightness = (int(m) + n) / 510.0
    return lightness


def dark_enough(rgb, tolerance):
    if rgb[0] == 255 and rgb[1] == 255 and rgb[2] == 255:
        return False

    if image_lightness_at(rgb) < tolerance:
        return True

    return False


def find_top_edge(img, left, top, right, bottom, step, tolerance):
    for y in range(top, bottom, step):
        for x in range(left, right, step):
            rgb = img.getpixel((x, y))
            if dark_enough(rgb, tolerance):
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
                    except EdgeNotFoundException:
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

    raise EdgeNotFoundException("Didn't find any non-white pixels")


def find_left_edge(img, left, top, right, bottom, step, tolerance):
    for x in range(left, right, step):
        for y in range(top, bottom, step):
            rgb = img.getpixel((x, y))
            if dark_enough(rgb, tolerance):
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
                    except EdgeNotFoundException:
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

    raise EdgeNotFoundException("Didn't find any non-white pixels")


def find_right_edge(img, left, top, right, bottom, step, tolerance):
    for x in range(right - 1, left, -step):
        for y in range(top, bottom, step):
            rgb = img.getpixel((x, y))
            if dark_enough(rgb, tolerance):
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
                    except EdgeNotFoundException:
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

    raise EdgeNotFoundException("Didn't find any non-white pixels")


def find_bottom_edge(img, left, top, right, bottom, step, tolerance):
    for y in range(bottom - 1, top, -step):
        for x in range(left, right, step):
            rgb = img.getpixel((x, y))
            if dark_enough(rgb, tolerance):
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
                    except EdgeNotFoundException:
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

    raise EdgeNotFoundException("Didn't find any non-white pixels")


def crop(filename, **options):
    step = options.get('step', 1)
    tolerance = options.get('tolerance', 0.95)
    fade_gutters = options.get('fade_gutters', True)
    draw_lines = options.get('draw_lines', False)
    draw_ellipses = options.get('draw_ellipses', False)
    gutter = options.get('gutter', 0.05)
    fade_color = options.get('fade_color', [255, 255, 255])
    image = Image.open(filename)

    height, width = image.height, image.width

    extents = Extents(width, height)

    # discover top edge
    top_ellipse = find_top_edge(
        image,
        left=0,
        top=0,
        right=width,
        bottom=height,
        step=step,
        tolerance=tolerance
    )
    extents.add([None, top_ellipse[1]])

    # bottom edge
    bottom_ellipse = find_bottom_edge(
        image,
        left=0,
        top=extents.top(),
        right=width,
        bottom=height,
        step=step,
        tolerance=tolerance
    )
    extents.add([None, bottom_ellipse[1]])

    # left edge
    left_ellipse = find_left_edge(
        image,
        left=0,
        top=extents.top(),
        right=width,
        bottom=extents.bottom() + 1,
        step=step,
        tolerance=tolerance
    )
    extents.add([left_ellipse[0], None])

    # right edge
    right_ellipse = find_right_edge(
        image,
        left=extents.right(),
        top=extents.top(),
        right=width,
        bottom=extents.bottom() + 1,
        step=step,
        tolerance=tolerance
    )
    extents.add([right_ellipse[0], None])

    core_width = extents.width() + 1
    core_height = extents.height() + 1
    gutter_width = int(math.ceil(core_width * gutter))
    gutter_height = int(math.ceil(core_height * gutter))

    final_width = int(core_width + gutter_width * 2)
    final_height = int(core_height + gutter_height * 2)

    cropped = image.crop((extents.left(), extents.top(), width, height))

    res = Image.new("RGB", (final_width, final_height), "white")
    res.paste(cropped, (gutter_width, gutter_height))
    draw = ImageDraw.Draw(res, 'RGBA')

    # adjust the values after the crop
    top_ellipse[0] -= extents.left()
    bottom_ellipse[0] -= extents.left()
    left_ellipse[1] -= extents.top()
    right_ellipse[1] -= extents.top()

    if fade_gutters:
        slope = gutter_height / gutter_width
        # fade out the top and bottom gutters
        for y in range(0, gutter_height):
            scalar = 255 - int((y / gutter_height) * 255)
            local_bottom = final_height - y
            draw.line((
                y / slope,
                y,
                final_width - y / slope,
                y,
            ), fill=(fade_color[0], fade_color[1], fade_color[2], scalar), width=1)
            draw.line((
                y / slope,
                local_bottom,
                final_width - y / slope,
                local_bottom,
            ), fill=(fade_color[0], fade_color[1], fade_color[2], scalar), width=1)

        # fade out the left and right gutters
        for x in range(0, gutter_width):
            scalar = 255 - int((x / gutter_width) * 255)
            local_right = final_width - x
            draw.line((
                x,
                x * slope,
                x,
                final_height - x * slope,
            ), fill=(fade_color[0], fade_color[1], fade_color[2], scalar), width=1)
            draw.line((
                local_right,
                x * slope,
                local_right,
                final_height - x * slope,
            ), fill=(fade_color[0], fade_color[1], fade_color[2], scalar), width=1)

    if draw_ellipses:
        radius = (final_height * 0.1) / 2
        # left ellipse
        if left_ellipse is not None:
            draw_circle(
                draw,
                gutter_width,
                left_ellipse[1] + gutter_height,
                radius,
                "#ff0000",
                1
            )

        # top ellipse
        draw_circle(
            draw,
            top_ellipse[0] + gutter_width,
            gutter_height,
            radius,
            '#00ff00',
            1
        )

        # right ellipse
        if right_ellipse is not None:
            draw_circle(
                draw,
                final_width - gutter_width - 1,
                right_ellipse[1] + gutter_height,
                radius,
                "#0000ff",
                1
            )

        # bottom ellipse
        draw_circle(
            draw,
            bottom_ellipse[0] + gutter_width,
            final_height - gutter_height - 1,
            radius,
            '#ff00ff',
            1

        )

    if draw_lines:
        line_color = (0, 255, 255, 32)
        for y in range(0, gutter_height):
            # top line
            draw.line((
                gutter_width,
                gutter_height,
                final_width - gutter_width - 1,
                gutter_height,
            ), fill=line_color, width=1)

            # bottom line
            draw.line((
                gutter_width,
                final_height - gutter_height - 1,
                final_width - gutter_width - 1,
                final_height - gutter_height - 1,
            ), fill=line_color, width=1)

            # left line
            draw.line((
                gutter_width,
                gutter_height,
                gutter_width,
                final_height - gutter_height - 1,
            ), fill=line_color, width=1)

            # right line
            draw.line((
                gutter_width + core_width - 1,
                gutter_height,
                gutter_width + core_width - 1,
                final_height - gutter_height - 1,
            ), fill=line_color, width=1)

    return res


def draw_circle(draw, center_x, center_y, radius, color, width):
    draw.ellipse((
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius
    ),
        outline=color,
        width=width
    )
