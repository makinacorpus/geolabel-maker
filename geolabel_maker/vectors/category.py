# Encoding: UTF-8
# File: category.py
# Creation: Thursday December 31st 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
This module handles loading geometries.
The class ``Category`` wraps the ``GeoDataFrame`` class from ``geopandas`` and add two more attributes: ``name`` and ``color``.

.. code-block:: python

    # Basic imports
    import geopandas as gpd
    # Geolabel Maker
    from geolabel_maker.vectors import Category
    
    # 1. Load directly from Geolabel Maker
    category = Category.open("categories/buildings.json", name="buildings", color=(255, 255, 255))
    
    # 2. Load from GeoPandas
    data = gpd.read_file("categories/buildings.json")
    category = Category("buildings", data, color=(255, 255, 255))
    
"""

# Basic imports
from shutil import ReadError
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box
import json

# Geolabel Maker
from geolabel_maker.rasters import to_raster
from .color import Color
from .download import OverpassAPI
from geolabel_maker.logger import logger


__all__ = [
    "Category",
    "CategoryCollection",
    "to_category"
]


def to_category(element, *args, **kwargs):
    r"""Convert an object to a ``Category``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``geopandas.GeoDataFrame`` etc...

    Returns:
        Category

    Examples:
        >>> category = to_category("buildings.json")
        >>> category = to_category(Path("buildings.json"))
        >>> category = to_category(gpd.read_file("buildings.json"))
    """
    if isinstance(element, (str, Path)):
        return Category.open(str(element), *args, **kwargs)
    elif isinstance(element, gpd.GeoDataFrame):
        return Category(element, *args, **kwargs)
    elif isinstance(element, Category):
        return element
    raise ValueError(f"Unknown element: Cannot load {type(element)} as `Category`.")


class Category:
    r"""
    A category is a set of vectors (or geometries) corresponding to the same geographic element.
    A category must have a name (e.g. ``"buildings"``) and a RGB color (e.g. ``(255, 255, 255)``),
    which will be used to draw the vectors on raster images (called labels).
    This class is used to extract polygons / geometries from satellite images, and then create the labels.

    * :attr:`name` (str): The name of the category corresponding to the elements.

    * :attr:`data` (geopandas.GeoDataFrame): A table of geometries.

    * :attr:`color` (tuple): RGB tuple of pixel values (from 0 to 255).

    """

    def __init__(self, name, data, color=None, filename=None):
        super().__init__()
        self.name = name
        self.data = data
        self.filename = filename
        # Convert color to RGB
        if not color:
            color = Color.random()
        else:
            color = Color.get(color)
        self.color = tuple(color)

    @classmethod
    def open(cls, filename, name=None, color=None):
        r"""Load the ``Category`` from a vector file. 
        The supported extensions are the one supported by ``geopandas``.

        Args:
            filename (str): The path to the vector file.
            name (str, optional): Name of the category. If ``None``, the name will be ``filename``. Defaults to None.
            color (tuple, optional): Color in the format :math:`(R, G, B)`. Defaults to None.

        Returns:
            Category

        Examples:
            >>> from geolabel_maker.vectors import Category
            >>> category = Category.open("categories/buildings.json", "buildings", (255, 255, 255))
        """
        data = gpd.read_file(str(filename))
        name = name or Path(filename).stem
        return Category(name, data, color=color, filename=str(filename))

    @classmethod
    def from_postgis(self, name, sql, conn, color=None, **kwargs):
        r"""Load a ``Category`` from a `PostGIS` database.
        This method wraps the ``read_postgis`` function from ``geopandas``.

        .. seealso::
            For more details, please visit ``geopandas`` 
            `documentation <https://geopandas.readthedocs.io/en/latest/reference/geopandas.read_postgis.html#geopandas.read_postgis>`__.

        Args:
            name (str, optional): Name of the category.
            sql (str): Query posted in the database.
            conn (DB connection object or SQLAlchemy engine): Connection to the database.
            color (tuple, optional): Color in the format :math:`(R, G, B)`. Defaults to None.
            kwargs (dict): Rest of the arguments from ``GeoDataFrame.from_postgis`` method.

        Returns:
            Category

        Examples:
            >>> from geolabel_maker.vectors import Category
            >>> from sqlalchemy import create_engine  
            >>> db_connection_url = "postgres://myusername:mypassword@myhost:5432/mydb"
            >>> con = create_engine(db_connection_url)  
            >>> sql = "SELECT geom FROM buildings"
            >>> category = Category.from_postgis("buildings", sql, con, color=(255, 255, 255))  
        """
        data = gpd.read_postgis(sql, conn, **kwargs)
        return Category(name, data, color=color)

    @classmethod
    def download(cls, bbox, *args, **kwargs):
        """Download a ``Category`` from the `Open Street Map` API.

        .. seealso::
            See ``OverpassAPI`` for further details.

        Args:
            bbox (tuple): The bounding box of the region of interest.

        Returns:
            Category

        Examples:
            >>> category = Category.download(bbox=(40, 50, 41, 51))
        """
        api = OverpassAPI()
        outfile = api.download(bbox, *args, **kwargs)
        return Category.open(outfile)

    def crop(self, bbox):
        r"""Get the geometries which are in a bounding box.

        Args:
            bbox (tuple): Bounding box used to crop the geometries.
                The format should follow (left, bottom, right, top).
                See `shapely.geometry.box` for further details.

        Returns:
            list: The geometries of the tif file's geographic extent.

        Examples:
            >>> from geolabel_maker.vectors import Category
            >>> category = Category.open("categories/buildings.json", name="buildings", color=(255, 255, 255))
            >>> category_cropped = category.crop((1843000, 5173000, 1845000, 5174000))
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

        Examples:
            >>> from geolabel_maker.rasters import Raster
            >>> from geolabel_maker.vectors import Category
            >>> raster = Raster.open("images/tile.tif")
            >>> category = Category.open("categories/buildings.json", name="buildings", color=(255, 255, 255))
            >>> category_cropped = category.crop_raster(raster)
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

    def __repr__(self):
        return f"Category(name='{self.name}', data=GeoDataFrame(..., length={len(self.data)}), color={self.color})"


class CategoryCollection:
    r"""
    Defines a collection of ``Category``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Category``.

    .. note::
        The ``Category`` within the ``CategoryCollection`` have unique colors.

    .. warning::
        If you initialize a ``CategoryCollection`` from categories with shared colors,
        the duplicate colors will be replaced with random ones.

    * :attr:`items` (list): List of categories.

    """

    def __init__(self, *categories):
        if not isinstance(categories, (list, tuple, CategoryCollection)):
            categories = [categories]
        elif isinstance(categories, (list, tuple)) and len(categories) == 1:
            categories = categories[0]
        if not categories:
            categories = []
        self.items = [to_category(category) for category in categories]
        self._make_unique_colors()

    def _make_unique_colors(self):
        """Make sure the categories have unique colors."""
        colors = [category.color for category in self.items]
        for i, color in enumerate(colors):
            other_colors = set(colors[:i] + colors[i + 1:])
            max_steps = 200  # Prevent infinite loops
            while color in other_colors and max_steps > 0:
                color = tuple(Color.random())
                max_steps -= 1
            self.items[i].color = color

    def append(self, category):
        r"""Add a ``Category`` to the collection.

        Args:
            category (Category): The category to add.

        Examples:
            >>> collection = CategoryCollection()
            >>> category = Category.open("buildings.json")
            >>> collection.append(category)
            >>> collection
                CategoryCollection(
                  (0): Category(name='buildings', filename='buildings.json', color=(234, 85, 40))
                )
        """
        category = to_category(category)
        self.items.append(category)
        self._make_unique_colors()

    def extend(self, categories):
        r"""Add a set of ``Category`` to the collection.

        Args:
            categories (list): List of categories to add.

        Examples:
            >>> collection = CategoryCollection()
            >>> categories = [Category.open("buildings.json"), Category.open("vegetation.json")]
            >>> collection.extend(categories)
            >>> collection
                CategoryCollection(
                  (0): Category(name='buildings', filename='buildings.json', color=(234, 85, 40))
                  (1): Category(name='vegetation', filename='vegetation.json', color=(35, 3, 220))
                )
        """
        categories = [to_category(category) for category in categories]
        self.items.extend(categories)
        self._make_unique_colors()

    def __setitem__(self, index, category):
        category = to_category(category)
        self.items[index] = category
        self._make_unique_colors()

    def __getitem__(self, index):
        return self.items[index]

    def __iter__(self):
        yield from self.items

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        rep = f"CategoryCollection("
        for i, category in enumerate(self):
            rep += f"\n  ({i}): {category}"
        rep += "\n)"
        return rep
