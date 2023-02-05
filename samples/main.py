import imageio.v3 as iio
from cropper import crop

croppedImg = crop(
    './figure.jpg',
    tolerance=0.95,
    drawEllipses=True,
    drawLines=True,
    step=10,
    fadeGutters=True,
    fadeColor=[0,255,255]
)

iio.imwrite("./cropped.png", croppedImg)
print("done")
