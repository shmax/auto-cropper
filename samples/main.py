import imageio.v3 as iio
from cropper import crop

if __name__ == '__main__':
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
    print("done")
