# Encoding: UTF-8
# File: utils.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
import numpy as np


def color_mask(mask, color):
    """Assigns a RGB color to a mask.
    All colored pixels in the input image are set to a unique color ``color``
    and the rest is left in black. Note that black pixels in the input image 
    are not modified i.e. are kept black in the output image.

    .. warning::
        The ``color`` must be different than black. 
        The color black is used to represent no data.

    Args:
        rgb_img (numpy.array): Image to convert in a single color, of size :math:`(H, W, 3)`.
        color (tuple): RGB color, in the format :math:`(R, G, B)`.

    Returns:
        numpy.array: The black and single-color image.
    """
    color_img = mask.copy()
    # Find non black pixels
    mask = np.any((color_img != [0, 0, 0]), axis=-1)
    # Apply the mask to overwrite the pixels with the chosen color
    color_img[mask] = np.array(color)
    return color_img


def merge_masks(masks):
    """Merges multiple colored masks (images with black background and a colored mask) together.

    Args:
        masks (list): List of 3D matrices of shape :math:`(H, W, 3)` with a black background
            and a colored mask (a mask has only one color).

    Returns:
        numpy.array: The merged masks, with the same shape as the input ones.
    """
    # Special cases
    if len(masks) == 0:
        return None
    elif len(masks) == 1:
        return masks[0]
    # Merge multiple masks
    merged_mask = masks[0]
    for mask in masks[1:]:
        mask_indices = np.any((mask != [0, 0, 0]), axis=-1)
        mask_values = mask[mask_indices]
        if mask_values.size > 0:
            color = mask_values[0]
            merged_mask[mask_indices] = mask_values
    return merged_mask.astype("uint8")
