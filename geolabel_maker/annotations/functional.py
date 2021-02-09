# Encoding: UTF-8
# File: functional.py
# Creation: Wednesday December 30th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


"""
This module defines functions used to process couple (image, label).
They are mainly used for `COCO` annotations, as it requires to extract masks and create segmentation maps.

.. code-block:: python

    from geolabel_maker.vectors import Category
    from geolabel_maker.annotations.functional import *
    
    categories = [Category.open("buildings.json", color="white"), 
                  Category.open("vegetation.json", color="green")]
    extracted_categories = extract_categories("data/tiles/labels/18/2937/29373.png", categories)
"""


# Basic imports
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from PIL import Image
import numpy as np
import cv2

# Geolabel Maker
from geolabel_maker.vectors import Category


__all__ = [
    "retrieve_masks",
    "find_polygons",
    "extract_categories"
]


#! deprecated
def retrieve_masks(label_image, colors):
    """Create sub masks from a label image and their colors.

    Args:
        image (PIL.Image): Mask as a RGB image of shape :math:`(X, Y, 3)`.
        colors (list): List of RGB colors used to map the different categories.

    Returns:
        dict: A dictionary of masks indexed by RGB colors.

    Examples:
        >>> from PIL import Image
        >>> # Open a tile label (generated with `generate_tiles()` or `gdal2tiles()`)
        >>> label_image = Image.open("42154.png")
        >>> colors = [(255, 255, 255), (0, 150, 0)]
        >>> masks = retrieve_masks(label_image, colors)
        >>> type(masks[(255, 255, 255)])
            PIL.Image
    """
    label_array = np.array(label_image)
    # Initialize a dictionary of sub-masks indexed by RGB colors
    masks = {}
    for color in colors:
        color_array = np.array(color)
        mask_array = np.all(label_array == color_array, axis=-1)
        masks[color] = Image.fromarray(mask_array)
    return masks


def find_polygons(mask_array, preserve_topology=False, simplify_level=1.0):
    """Retrieve the polygons from a black and white raster image.

    Args:
        mask_image (PIL.Image): Black and white mask image of shape :math:`(X, Y, 3)`, 
            usually generated with the function ``retrieve_masks()``.
        preserve_topology (bool): If ``True``, preserve the topology of the polygon. Default to ``False``.

    Returns:
        list: List of ``shapely.geometry.Polygon`` vectorized from the input raster ``mask_image``.

    Examples:
        >>> from PIL import Image
        >>> # Open a tile label (generated with `generate_tiles()` or `gdal2tiles()`)
        >>> label_image = Image.open("42154.png")
        >>> colors = [(255, 255, 255), (0, 150, 0)]
        >>> masks = retrieve_masks(label_image, colors)
        >>> mask = mask[(0, 150, 0)]
        >>> # Get all polygons in the mask
        >>> polygons = find_polygons(mask)
        >>> type(polygons[0])
            shapely.geometry.Polygon
    """
    polygons = []
    contours, hierarchy = cv2.findContours(mask_array, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        segmentation = contour.flatten()
        # A LinearRing must have at least 3 coordinate tuples (i.e. 3 * 2 values)
        if len(segmentation) >= 6:
            x = segmentation[::2]
            y = segmentation[1::2]
            polygon = Polygon(np.column_stack((x, y)))
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


def extract_categories(label_file, categories, **kwargs):
    r"""Retrieve the polygons for all tile labels.
    This method must be used once the tiles are generated (see ``generate_tiles`` method).

    .. note::
        You can use the ``categories`` from the ``Dataset``, or simply load them
        with ``read_categories`` function.

    Args:
        label_file (str): Path to the label image.
        categories (list): List of ``Category``.
        **kwargs (optional): See ``geolabel_maker.functional.find_polygons`` method arguments.

    Returns:
        tuple: Categories containing geometries (e.g. all buildings from the images at ``zoom`` level).

    Examples:
        >>> categories = [Category.open("buildings.json", color="white"), Category.open("vegetation.json", color="green")]
        >>> categories = extract_categories("tiles/labels/13/345/374.png", categories)
        >>> categories
            (Category(data=GeoDataFrame(34 rows, 1 column), name='vegetation', color=(0, 150, 0), 
            Category(data=GeoDataFrame(234 rows, 1 column), name='buildings', color=(255, 255, 255)))

    Examples:
        >>> dataset = Dataset.open("data")
    """
    image_array = cv2.imread(str(label_file))
    color2name = {tuple(category.color): category.name for category in categories}
    colors = color2name.keys()
    categories_extracted = []
    for color in colors:
        # Extract a mask of color `color` exactly
        mask_array = cv2.inRange(image_array, color, color)
        polygons = find_polygons(mask_array, **kwargs)
        data = gpd.GeoDataFrame({"geometry": polygons})
        name = color2name[color]
        categories_extracted.append(Category(data, name, color=color))
    return categories_extracted
