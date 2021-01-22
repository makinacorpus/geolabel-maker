# Encoding: UTF-8
# File: functional.py
# Creation: Wednesday December 30th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from collections import defaultdict
from skimage import measure
import geopandas as gpd
from shapely.geometry import Polygon
from PIL import Image
from pathlib import Path

# Geolabel Maker
from geolabel_maker.vectors import Category


__all__ = [
    "retrieve_masks",
    "find_polygons",
    "extract_categories"
]


def retrieve_masks(label_image, categories):
    """Create sub masks from a label image and their colors.

    Args:
        image (PIL.Image): Mask RGB image of shape :math:`(3, X, Y)`.
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
    # Get all colors / categories of geometries
    colors = [tuple(category.color) for category in categories]

    width, height = label_image.size
    # Initialize a dictionary of sub-masks indexed by RGB colors
    masks = {}
    for x in range(width):
        for y in range(height):
            # get the RGB values of the pixel
            pixel = label_image.getpixel((x, y))
            # if the pixel has a color used in a category
            if pixel in colors:
                # check to see if we've created a sub-mask...
                mask = masks.get(pixel)
                if mask is None:
                    # Create a sub-mask (one bit per pixel)
                    # and add to the dictionary
                    # NOTE: mode="1" i.e. 1-bit pixels, black and white, stored with one pixel per byte
                    masks[pixel] = Image.new("1", (width, height))
                # set the pixel value to 1 (default is 0),
                # accounting for padding
                masks[pixel].putpixel((x, y), 1)

    return masks


def find_polygons(mask_image, preserve_topology=False):
    """Retrieve the polygons from a black and white raster image.

    Args:
        mask_image (PIL.Image): Black and white mask image of shape :math:`(3, X, Y)`, 
            usually generated with the function ``retrieve_masks()``.
        preserve_topology (bool): If ``True``, preserve the topology of the polygon.

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
    # NOTE: we add 1 pixel of padding in each direction
    # because the contours module doesn't handle cases
    # where pixels bleed to the edge of the image    # Find contours (boundary lines) around each sub-mask.
    width, height = mask_image.size
    padded_mask = Image.new(mask_image.mode, (width + 2, height + 2))
    padded_mask.paste(mask_image, (1, 1))

    # NOTE: There could be multiple contours if the object
    # is partially occluded. (e.g. an elephant behind a tree)
    contours = measure.find_contours(padded_mask, level=0.5, positive_orientation="low")
    polygons = []
    for contour in contours:
        # Flip from (row, col) representation to (x, y)
        # and subtract the padding pixel
        contour[:, [0, 1]] = contour[:, [1, 0]]
        # Remove the padding
        contour = contour - 1
        # Make a polygon and simplify it
        polygon = Polygon(contour)
        polygon = polygon.simplify(1.0, preserve_topology=preserve_topology)
        # Add the simplified polygon
        if not polygon.is_empty:
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
        >>> categories = read_categories("categories.json")
        >>> categories = extract_categories("tiles/labels/13/345/374.png", categories)
        >>> categories
            (Category(name='vegetation', data=34, color=(0, 150, 0), 
            Category(name='buildings', data=267, color=(255, 255, 255)))
            
    Examples:
        >>> dataset = Dataset.open("data")
    """
    color2id = {tuple(category.color): i for i, category in enumerate(categories)}
    categories_extracted = []

    # Read label image
    tile_label = Image.open(label_file)
    tile_label = tile_label.convert("RGB")

    # Find all masks / categories
    masks = retrieve_masks(tile_label, categories)
    for color, mask in masks.items():
        category_data = defaultdict(list)

        # Find all polygons within a category
        polygons = find_polygons(mask, **kwargs)
        category_id = int(color2id[color])
        for polygon in polygons:
            category_data["geometry"].append(polygon)

        # Build the `Category` object
        name = categories[category_id].name
        color = categories[category_id].color
        data = gpd.GeoDataFrame(category_data)
        category = Category(name, data, color)
        categories_extracted.append(category)

    return categories_extracted


# // def extract_categories(dir_labels, categories, pattern="*.*", **kwargs):
# //     r"""Retrieve the polygons for all tile labels.
# //     This method must be used once the tiles are generated (see ``generate_tiles`` method).

# //     Args:
# //         zoom (int, optional): Zoom level where the polygons will be extracted. Defaults to 16.
# //         **kwargs (optional): See ``geolabel_maker.functional.find_polygons`` method arguments.

# //     Returns:
# //         tuple: Categories containing geometries (e.g. all buildings from the images at ``zoom`` level).

# //     Examples:
# //         >>> dataset = Dataset.open("data/")
# //         >>> dataset.generate_labels()
# //         >>> dataset.generate_tiles(zoom="14-16")
# //         >>> categories = extract_categories(dataset.dir_labels, dataset.categories)
# //         >>> categories
# //             (Category(name='vegetation', data=34, color=(0, 150, 0), Category(name='buildings', data=267, color=(255, 255, 255)))
# //     """
# //     color2id = {tuple(category.color): i for i, category in enumerate(categories)}
# //     categories_dict = defaultdict(list)

# //     # Load all label (tile) images
# //     dir_path = Path(dir_labels)
# //     # Make sure the tiles exist
# //     if not dir_path.is_dir():
# //         raise RuntimeError(f"The labels were not found in '{dir_path}'. "
# //                            f"Please try to generate them with `generate_tiles()` method. ")

# //     for tile_index, tile_file in enumerate(dir_path.rglob(pattern)):
# //         # Read label image
# //         tile_label = Image.open(tile_file)
# //         tile_label = tile_label.convert("RGB")
# //         # Find all masks / categories
# //         masks = retrieve_masks(tile_label, categories)
# //         for color, mask in masks.items():
# //             # Find all polygons within a category
# //             polygons = find_polygons(mask, **kwargs)
# //             for polygon in polygons:
# //                 category_id = int(color2id[color])
# //                 categories_dict[category_id].append({
# //                     "image_id": int(tile_index),
# //                     "image_name": str(tile_file),
# //                     "geometry": polygon,
# //                 })

# //     # Group by categories
# //     categories_sorted = []
# //     # Sort the generated categories to match the `dataset.categories` order
# //     for category_id, category_data in sorted(categories_dict.items()):
# //         name = categories[category_id].name
# //         color = categories[category_id].color
# //         data = gpd.GeoDataFrame(category_data)
# //         category = Category(name, data, color)
# //         categories_sorted.append(category)

# //     return categories_sorted
