import numpy as np
from pathlib import Path


def rgb2gray(rgb_img):
    """
    Parameters
    ----------
    rgb_img : numpy array with shape as (3, X, Y)
        image to convert in gray

    Returns
    -------
    gray_img , the grayscale image
    """
    gray_coef = [0.2989, 0.5870, 0.1140]

    r = rgb_img[0] / 255
    g = rgb_img[1] / 255
    b = rgb_img[2] / 255

    gray_img = gray_coef[0] * r + gray_coef[1] * g + gray_coef[2] * b

    return gray_img * 255


def gray2bw(gray_img):
    """
    Convert a grayscale image to a black & white image
    Parameters
    ----------
    gray_img : numpy 2D-array
        Gray image to convert in black and white

    Returns
    -------
     the converted image
    """
    gray_img[gray_img > 0] = 255

    return gray_img


def rgb2color(rgb_img, color):
    """
    Convert an rgb image to a black and color image

    Parameters
    ----------
    rgb_img : numpy array with shape as (3, X, Y)
        image to convert in gray
    color : tuple
        a color as (r, g, b) values
    Returns
    -------
    the black and color image
    """
    color_img = rgb_img.copy()

    # find non black pixels
    mask = np.any((color_img != [0, 0, 0]), axis=-1)

    # apply the mask to overwrite the pixels with the chosen color
    color_img[mask] = color

    return color_img


def rm_tree(pth: Path):
    """
    Remove recursively all files and folders in a directory path

    Parameters
    ----------
    pth : Path
        directory path
    """
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)

    pth.rmdir()
