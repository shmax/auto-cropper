# auto-cropper

This is the tool used on shmax.com to automatically crop photographs of objects taken against a white background.

### Dependencies
* [libiio with python bindings](https://wiki.analog.com/resources/tools-software/linux-software/libiio)

### Basic usage

```py
import imageio.v3 as iio
from cropper import crop

iio.imwrite("./cropped.png", crop('./figure.png'))
```

There are a few config options to customize the result:

* `tolerance` - `0 < value < 1`. Default: `0.95`. The minimal lightness a pixel must exceed in order for it to be detected.
* `gutter` -  `0 < value < 1`. Default: `0.06`. Adds additional whitespace around the detected edges as a percentage of the area between the detected edges.
* `drawEllipses` - Boolean. Default: `False`. For debugging purposes. Renders a circle at the point each edge is detected.
* `drawLines` - Boolean. Default: `False`. For debugging purposes. Renders a line along the detected edge.
* `step` - Default: `10`. An optimization feature. When detecting edges, the cropping algorithm will skip every `step` pixels. Once a pixel is detected, the algorithm will rewind by `step` and go pixel-by-pixel. The `step` option is only recommended for photos; for fine pixel images or line art a value of `1` is recommended. 
* `fadeGutters` - Boolean. Default: `True`. Helpful for low tolerances and wide gutters; will gradually fade out any pixels in the gutters as they approach the outer edge of the generated image.
* `fadeColor` - Default: `[255,255,255]`. The color to fade to. This should generally be set to white, but it can be helpful to set it to a more visible color when debugging or troubleshooting.

```py
import imageio.v3 as iio
from cropper import crop

iio.imwrite("./cropped.png", crop(
    './figure.png',
    tolerance=0.95,
    drawEllipses=True,
    drawLines=True,
    step=10,
    fadeGutters=True,
    fadeColor=[0,255,255],
    gutter=0.06
))
```

![image](https://user-images.githubusercontent.com/773172/216800860-f503ecf0-6872-46db-9419-15e1c7dd3cb2.png)


