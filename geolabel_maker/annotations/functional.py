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
import numpy as np
import cv2

# Geolabel Maker
from geolabel_maker.vectors import Category


__all__ = [
    "find_polygons",
    "extract_categories"
]



def find_polygons(mask_array, preserve_topology=False, simplify_level=1.0):
    """Retrieve the polygons from a black and white raster image.

    Args:
        mask_array (numpy.ndarray): Black and white mask image of shape :math:`(X, Y, 3)`.
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


def extract_categories(label=None, categories=None, **kwargs):
    r"""Retrieve the polygons for all tile labels.
    This method must be used once the tiles are generated (see ``generate_tiles`` method).

    Args:
        label (PIL.Image): PIL Image of the label.
        categories (list): List of categories.
        **kwargs (optional): See ``geolabel_maker.functional.find_polygons`` method arguments.

    Returns:
        tuple: Categories containing geometries (e.g. all buildings from the images at ``zoom`` level).

    Examples:
        >>> categories = [Category.open("buildings.json", color="white"), Category.open("vegetation.json", color="green")]
        >>> categories = extract_categories("tiles/labels/13/345/374.png", categories)
        >>> categories
            (Category(data=GeoDataFrame(34 rows, 1 column), name='vegetation', color=(0, 150, 0), 
             Category(data=GeoDataFrame(234 rows, 1 column), name='buildings', color=(255, 255, 255)))
    """
    assert label, "Label image must be provided"
    
    label_array = np.array(label.convert("RGB"))
    categories_extracted = []
    for category in categories:
        # Extract a mask of color `color` exactly
        color = tuple(category.color)
        mask_array = cv2.inRange(label_array, color, color)
        polygons = find_polygons(mask_array, **kwargs)
        data = gpd.GeoDataFrame({"geometry": polygons})
        categories_extracted.append(Category(data, category.name, color=color))
    return categories_extracted


def has_color(label, color):
    """Check if a label image has a specific color.

    Args:
        label (PIL.Image): PIL Image of the label.
        color (tuple): RGB color.

    Returns:
        bool: True if the label image has the specified color.
    """
    array = np.array(label.convert("RGB"))
    red, green, blue = tuple(color)
    return np.where((array[:,:,0] == red) & (array[:,:,1] == green) & (array[:,:,2] == blue), True, False).any()