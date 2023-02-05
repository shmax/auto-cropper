import imageio.v3 as iio
from cropper import crop

if __name__ == '__main__':
    iio.imwrite("./cropped.png", crop(
        './figure.png',
        tolerance=0.95,
        draw_ellipses=0.1,
        draw_lines=True,
        step=10,
        ellipse_size=0.1,
        fade_gutters=True,
        fade_color=[0,255,255],
        gutter=0.06
    ))
    print("done")
