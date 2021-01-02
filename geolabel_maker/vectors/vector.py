# Encoding: UTF-8
# File: vector.py
# Creation: Tuesday December 29th 2020
# Author: arthurdjn
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
import geopandas as gpd
from shapely.geometry import box

# Geolabel Maker
from geolabel_maker.rasters import to_raster
from geolabel_maker.data import Data


# ! This module will be deprecated and replaced by the `category` module


def to_vector(element, *args, **kwargs):
    r"""Convert an object to a ``Vector``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``geopandas.GeoDataFrame`` etc...

    Returns:
        Vector

    Examples:
        >>> vector = to_vector("buildings.json")
        >>> vector = to_vector(Path("buildings.json"))
        >>> vector = to_vector(geopandas.GeoDataFrame.read_file("buildings.json"))
    """
    if isinstance(element, str):
        return Vector.open(element, *args, **kwargs)
    elif isinstance(element, gpd.geodataframe.GeoDataFrame):
        return Vector(element, *args, **kwargs)
    elif isinstance(element, Vector):
        return element
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Vector`.")


class Vector(Data):

    def __init__(self, data):
        super().__init__()
        self.data = data

    @property
    def geometries(self):
        return list(self.data["geometry"])

    @classmethod
    def open(cls, filename):
        data = gpd.read_file(filename)
        return Vector(data)

    def save(self, outname):
        raise NotImplementedError

    def from_psql(self, *args, **kwargs):
        raise NotImplementedError

    def crop(self, bbox):
        """Get the geometries which are in a bounding box.

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
            subset = self.data.cx[Xmin:Xmax, Ymin:Ymax]
        else:
            raise ValueError(f"The geographic extents are not consistent. "
                             f"The referenced bbox is {crop_box.bounds} whereas vector bbox is {vector_box.bounds}.")

        return Vector(subset)

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
        vector_data = self.data.to_crs(raster_data.crs)
        vector = Vector(vector_data)
        return vector.crop(raster_box.bounds)

    def inner_repr(self):
        return f"geometries={len(self.geometries)}"
