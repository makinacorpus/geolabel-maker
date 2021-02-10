# Encoding: UTF-8
# File: utils.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
import numpy as np


def rgb2gray(rgb_img):
    """Convert an RGB image to grayscale.

    Args:
        rgb_img (numpy.ndarray): RGB image of size :math:`(X, Y, 3)`.

    Returns:
        numpy.ndarray: Gray image of size :math:`(X, Y)`.
    """
    gray_coef = [0.2989, 0.5870, 0.1140]

    r = rgb_img[0] / 255
    g = rgb_img[1] / 255
    b = rgb_img[2] / 255

    gray_img = gray_coef[0] * r + gray_coef[1] * g + gray_coef[2] * b

    return gray_img * 255


def gray2bw(gray_img):
    """Convert a grayscale image to a black & white image

    Args:
        gray_img (numpy.ndarray): Gray image of size :math:`(X, Y)`.

    Returns:
         numpy.ndarray: Black and White image of size :math:`(X, Y)`.
    """
    gray_img[gray_img > 0] = 255
    return gray_img


def rgb2color(rgb_img, color):
    """Convert an RGB image to a black and color image.
    All colored pixels in the input image are set to a unique color ``color``
    and the rest is left in black. Note that black pixels in the input image 
    are not modified i.e. are kept black in the output image.

    .. warning::
        The ``color`` must be different than black. 
        The color black is used to represent no data.

    Args:
        rgb_img (numpy.ndarray): Image to convert in a single color, of size :math:`(X, Y, 3)`.
        color (tuple): RGB color, in the format :math:`(R, G, B)`.

    Returns:
        numpy.ndarray: The black and single-color image.
    """
    color_img = rgb_img.copy()
    # find non black pixels
    mask = np.any((color_img != [0, 0, 0]), axis=-1)
    # apply the mask to overwrite the pixels with the chosen color
    color_img[mask] = np.array(color)
    return color_img