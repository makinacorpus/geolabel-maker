# Encoding: UTF-8
# File: utils.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from PIL import Image, ImageChops
import numpy as np


def color_mask(mask, color):
    """Assign a RGB color to a mask.
    All colored pixels in the input image are set to a unique color ``color``
    and the rest is left in black. Note that black pixels in the input image 
    are not modified i.e. are kept black in the output image.

    .. warning::
        The ``color`` must be different than black. 
        The color black is used to represent no data.

    Args:
        rgb_img (numpy.ndarray): Image to convert in a single color, of size :math:`(H, W, 3)`.
        color (tuple): RGB color, in the format :math:`(R, G, B)`.

    Returns:
        numpy.ndarray: The black and single-color image.
    """
    color_img = mask.copy()
    # Find non black pixels
    mask = np.any((color_img != [0, 0, 0]), axis=-1)
    # Apply the mask to overwrite the pixels with the chosen color
    color_img[mask] = np.array(color)
    return color_img


#! Update this function as currently ImageChop.add only add color together and do not overwrite them 
#! i.e. blue + yellow = green instead of blue + yellow = yellow (overwrite with top color)
#! This result in the creation of new colors if categories are overlaping
def merge_masks(masks):
    """Merge multiple colored masks (images with black background and a colored mask) together.

    Args:
        masks (list): List of 3D matrices of shape :math:`(H, W, 3)` with a black background
            and a colored mask (a mask has only one color).

    Returns:
        numpy.ndarray: The merged masks, with the same shape as the input ones.
    """
    out_image = Image.fromarray(masks[0].astype("uint8"))
    if len(masks) > 1:
        for mask in masks[1:]:
            mask_image = Image.fromarray(mask.astype("uint8"))
            out_image = ImageChops.add(out_image, mask_image)
    return np.array(out_image)
