# Encoding: UTF-8
# File: functional.py
# Creation: Wednesday December 30th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


"""
This module defines functions used to process couple (image, label).
They are mainly used for :class:`~geolabel_maker.annotations.coco.COCO` annotations, 
as it requires to extract masks and generates segmentation maps.

.. code-block:: python

    from geolabel_maker.vectors import Category
    from geolabel_maker.annotations.functional import *
    
    categories = [Category.open("buildings.json", color="white"), 
                  Category.open("vegetation.json", color="green")]
    out_categories = find_categories("data/tiles/labels/18/2937/29373.png", categories)
"""


# Basic imports
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from PIL import Image
import numpy as np
import cv2

# Geolabel Maker
from geolabel_maker.vectors import Category, Color


__all__ = [
    "find_masks",
    "find_polygons",
    "find_categories"
]


def find_masks(label_file, colors=None):
    r"""Finds masks (binary images) from a label image.
    A mask is a binary image indicating the presence of an object.
    
    .. note::
        This method is used once the tiles are generated.
        
    .. seealso::
        See :func:`~geolabel_maker.dataset.Dataset.generate_mosaics` and
        :func:`~geolabel_maker.dataset.Dataset.generate_tiles` methods for further details.

    Args:
        label_file (str): Path to the label image.
        colors (list, optional): List of RGB colors.

    Returns:
        tuple: Categories containing geometries (e.g. all buildings from the images at ``zoom`` level).

    Examples:
        >>> from PIL import Image
        >>> label_image = Image.open("42154.png")

        Then, extract the masks associated to different colors:

        >>> masks = retrieve_masks(label_image)

        Select a specific mask by its color:

        >>> mask = mask[(0, 150, 0)]
    """
    label = Image.open(label_file).convert("RGB")
    width, height = label.size
    colors = colors or label.getcolors(width * height)
    colors = map(lambda color: Color.get(color), colors)
    label_array = np.array(label)
    masks = {}

    for color in colors:
        mask = cv2.inRange(label_array, np.array(color), np.array(color))
        masks[tuple(color)] = mask  # TODO: Transform to binary image
    return masks


def find_polygons(mask, preserve_topology=True, simplify_level=1.0):
    """Finds polygons from a binary mask.

    .. seealso::
        See :func:`~geolabel_maker.dataset.Dataset.find_masks` function for further details.

    Args:
        mask (numpy.array): Black and white mask image of shape :math:`(X, Y, 3)`.
        preserve_topology (bool): If ``True``, preserve the topology of the polygon. Default to ``False``.

    Returns:
        list: List of :class:`shapely.geometry.Polygon` vectorized from the input image ``mask``.

    Examples:
        Open a label generated with :func:`~geolabel_maker.dataset.Dataset.generate_mosaics` 
        or :func:`~geolabel_maker.dataset.Dataset.generate_tiles`.

        >>> from PIL import Image
        >>> label_image = Image.open("42154.png")

        Then, extract the masks associated to different colors:

        >>> masks = retrieve_masks(label_image)

        Select a specific mask by its color:

        >>> mask = mask[(0, 150, 0)]
        
        Once you have a mask (i.e. binary image)
    """
    polygons = []
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # If there are no contours
    if not contours:
        return polygons

    # Retrieve only outliers polygon (not the holes)
    contour_indices = np.where(hierarchy[0, :, 3] == -1)[0]
    for contour_idx in contour_indices:

        outer = contours[contour_idx].reshape(-1, 2)

        # A LinearRing must have at least 3 coordinate tuples (i.e. 3 * 2 values)
        if outer.size >= 6:
            # Retrieve inner polygons (holes)
            inner_indices = np.squeeze(np.where(hierarchy[0, :, 3] == contour_idx))
            inners = []
            if inner_indices.size > 0:
                inners = [contours[idx].reshape(-1, 2) for idx in np.nditer(inner_indices)]

            # Create a polygon with holes (inners)
            polygon = Polygon(outer, inners)
            polygon = polygon.simplify(simplify_level, preserve_topology=preserve_topology)

            # Only add polygons that are not empty
            if not polygon.is_empty:
                # Add multiple Polygon if the simplification resulted in a MultiPolygon
                if isinstance(polygon, MultiPolygon):
                    polygons.extend(polygon)
                # Add a single Polygon
                else:
                    polygons.append(polygon)
    return polygons


def find_categories(label_file, categories, **kwargs):
    r"""Finds the categories and associated polygons in a label image.
        
    .. seealso::
        See :func:`~geolabel_maker.annotations.functional.find_masks` and
        :func:`~geolabel_maker.annotations.functional.find_polygons` methods for further details.

    Args:
        label_file (str): Path to the label image.
        categories (list): List of categories.
        **kwargs (optional): Remaining arguments.

    Returns:
        tuple: Categories containing geometries (e.g. all buildings from the images at ``zoom`` level).

    Examples:
        >>> categories = [Category.open("buildings.json", color="white"), Category.open("vegetation.json", color="green")]
        >>> categories = extract_categories("tiles/labels/13/345/374.png", categories)
        >>> categories
            (Category(data=GeoDataFrame(34 rows, 1 column), name='vegetation', color=(0, 150, 0), 
             Category(data=GeoDataFrame(234 rows, 1 column), name='buildings', color=(255, 255, 255)))
    """
    masks = find_masks(label_file, colors=list(categories.colors()))
    categories_extracted = []
    for (color, mask), category in zip(masks.items(), categories):
        polygons = find_polygons(mask, **kwargs)
        data = gpd.GeoDataFrame({"geometry": polygons})
        categories_extracted.append(Category(data, category.name, color=color))
    return categories_extracted
