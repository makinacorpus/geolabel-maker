# Encoding: UTF-8
# File: category.py
# Creation: Thursday December 31st 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from collections import namedtuple
import geopandas as gpd
from shapely.geometry import box
from pathlib import Path

# Geolabel Maker
from geolabel_maker.rasters import to_raster
from geolabel_maker.data import Data


# ! Deprecated
# Category = namedtuple("Category", "name, vector, color")


class Category(Data):
    r"""
    A category is a set of vectors (or geometries) corresponding to the same element (e.g. buildings).
    A category must have a name (e.g. ``"buildings"``) and a RGB color (e.g. ``(255, 255, 255)``),
    which will be used to draw the vectors on raster images.
    This class is used to extract polygons / geometries from satellite images, and then create the labels.
    
    * :attr:`name` (str): The name of the category corresponding to the elements.
    
    * :attr:`data` (geopandas.GeoDataFrame): A table of geometries.
    
    * :attr:`color` (tuple): RGB tuple of pixel values (from 0 to 255).
    
    """

    def __init__(self, name, data, color=None):
        super().__init__()
        self.name = name
        self.data = data
        self.color = color

    @classmethod
    def open(cls, filename, name=None, color=None):
        data = gpd.read_file(str(filename))
        name = name or Path(filename).stem
        return Category(name, data, color=color)

    def save(self, outname):
        raise NotImplementedError

    def from_psql(self, *args, **kwargs):
        raise NotImplementedError

    def crop(self, bbox):
        r"""Get the geometries which are in a bounding box.

        Args:
            bbox (tuple): Bounding box used to crop the geometries.
                The format should follow (left, bottom, right, top).
                See `shapely.geometry.box` for further details.

        Returns:
            list: The geometries of the tif file's geographic extent.
        """
        # Create a polygon from the bbox
        left, bottom, right, top = bbox
        crop_box = box(left, bottom, right, top)

        # Read vector file
        # Create a polygon from the raster bounds
        vector_box = box(*self.data.total_bounds)

        # Make sure the raster bbox is contained in the vector bbox
        if vector_box.contains(crop_box):
            # Select vector data within the raster bounds
            Xmin, Xmax = left, right
            Ymin, Ymax = bottom, top
            sub_data = self.data.cx[Xmin:Xmax, Ymin:Ymax]
        else:
            raise ValueError(f"The geographic extents are not consistent. "
                             f"The referenced bbox is {crop_box.bounds} whereas vector bbox is {vector_box.bounds}.")

        return Category(self.name, sub_data, color=self.color)

    def crop_raster(self, raster):
        """Get the geometries which are in the image's extent.

        Args:
            raster (Raster): Georeferenced raster used as a croping mask.

        Returns:
            list: The geometries of the tif file's geographic extent.
        """
        # Read raster file
        raster_data = to_raster(raster).data
        coordinate = raster_data.bounds
        # Create a polygon from the raster bounds
        raster_box = box(*coordinate)

        # Read vector file
        data = self.data.to_crs(raster_data.crs)
        category = Category(self.name, data, color=self.color)
        return category.crop(raster_box.bounds)

    def inner_repr(self):
        return f"name='{self.name}', data={len(self.data)}, color={self.color}"
