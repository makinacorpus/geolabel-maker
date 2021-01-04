# Encoding: UTF-8
# File: functional.py
# Creation: Wednesday December 30th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
import numpy as np
import rasterio
import rasterio.mask
from skimage import measure
from shapely.geometry import box, Polygon
from PIL import Image, ImageChops
from pathlib import Path

# Geolabel Maker
from geolabel_maker.rasters import utils


__all__ = [
    "retrieve_masks",
    "find_polygons",
    "generate_label",
]


def generate_label(raster, categories, dir_labels=""):
    """Convert geometries to a raster file which could be used as label.

    Args:
        categories (dict): Dictionary containing a name and a color as :math:`(R, G, B)` triplet
            for each category.
        dir_labels (str, optional): Path of the directory to save labels
            if it is empty, labels are registered within the origin raster directory.
            Default is empty.

    Returns:
        str: name of the created label image
    """
    img_list = []
    out_transform = None
    for category in categories:
        # Match the category to the raster extends
        category = category.crop_raster(raster)
        # Create a raster from the geometries
        out_image, out_transform = rasterio.mask.mask(
            raster.data,
            list(category.data.geometry),
            crop=False
        )
        # Format to (Bands, Width, Height)
        out_image = np.rollaxis(out_image, 0, 3)
        # Convert image in black & color
        bw_image = utils.rgb2color(out_image, category.color)
        # Create a PIL image
        img = Image.fromarray(bw_image.astype(rasterio.uint8))
        img_list.append(img)

    # Merge images
    label_image = img_list[0]
    if len(img_list) > 1:
        for img in img_list[1:]:
            label_image = ImageChops.add(label_image, img)
    # Transpose the axis so the image's shape is (BANDS, HEIGHT, WIDTH)
    label_array = np.rollaxis(np.array(label_image), -1, 0)

    # Update the profile before saving the tif
    # See the list of options and effects: https://gdal.org/drivers/raster/gtiff.html#creation-options
    # NOTE: the profile should be divided into windows 256x256, we keep it for the labels
    out_profile = raster.data.profile
    out_profile.update({
        "driver": "GTiff",
        "height": label_array.shape[1],  # numpy.array.shape[1] or PIL.Image.size[1],
        "width": label_array.shape[2],   # numpy.array.shape[2] or PIL.Image.size[0],
        "count": 3,
        "transform": out_transform,
        "photometric": "RGB"
    })

    # Generate filename "raster-label.tif"
    raster_path = Path(raster.filename)
    out_name = f"{raster_path.stem}-label.tif"
    # Create the directory if `dir_labels` does not exists
    if dir_labels:
        Path(dir_labels).mkdir(parents=True, exist_ok=True)
        out_path = Path(dir_labels) / out_name
    else:
        out_path = raster_path.parent / out_name

    # Write the `tif` image
    with rasterio.open(out_path, 'w', **out_profile) as dst:
        dst.write(label_array.astype("uint8"))

    return out_path


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
        mask_image (PIL.Image): Mask image of shape :math:`(3, X, Y)`, 
            usually generated with the function ``get_masks()``.
        preserve_topology (bool): If ``True``, preserve the topology of the polygon.

    Returns:
        list: List of ``shapely.geometry.Polygon`` vectorized from the input raster ``mask_image``.

    Examples:
        >>> from PIL import Image
        >>> # Open a tile label (generated with `generate_tiles()` or `gdal2tiles()`)
        >>> label_image = Image.open("42154.png")
        >>> colors = [(255, 255, 255), (0, 150, 0)]
        >>> masks = get_masks(label_image, colors)
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
