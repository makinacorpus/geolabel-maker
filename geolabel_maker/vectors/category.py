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


__all__ = [
    "read_categories",
    "Category"
]


def read_categories(categories_path, overwrite=False):
    """Read a 'categories' file. This file is used to map geometries to categories attributes,
    such as ``color``, ``name``.
    This file must follow the structure:

    .. code-block:: python

        {
            "vegetation": {                         # The name of your category
                "file": "path/to/vegetation.json",  # Path to the geometries (vector file)
                "color": [0, 150, 0]                # (Optional) Color of the category
            },
            "buildings": {                          # The name of your category
                "file": "path/to/vegetation.json",  # Path to the geometries (vector file)
                "color": "white"                    # (Optional) Color of the category
            },
            # etc...
        }

    Args:
        categories_path (str): Path to the categories file to load.
        overwrite (bool, optional): If ``True``, will overwrite the loaded file with generated missing colors (if any).

    Returns:
        tuple: A tuple of all the loaded ``Category`` objects.

    Examples:
        >>> categories = read_categories("data/categories.json")
    """
    if not Path(categories_path).is_file():
        raise ReadError(f"The file '{categories_path}' was not found. "
                        "Please create one following the 'categories.json' template.")

    # Load the JSON categories
    with open(categories_path, "r", encoding="utf-8") as f:
        categories_dict = json.load(f)

    # Create instances of `Category`
    categories = []
    for name, category_info in categories_dict.items():
        color = category_info.get("color")
        filename = category_info.get("file")
        categories.append(Category.open(filename, name=name, color=color))

    # Check for unique RGB colors. If there are duplicate,
    # it will overwrite the associated category's color with a random one
    colors = [category.color for category in categories]
    for i, color in enumerate(colors):
        other_colors = set(colors[:i] + colors[i + 1:])
        while color in other_colors:
            color = tuple(Color.random())
        categories[i].color = color
        # Update the `categories_dict` data, in case the user wants to save the modifications
        category_name = categories[i].name
        categories_dict[category_name]["color"] = color

    # Save the `categories` JSON file, with the generated colors
    if overwrite:
        try:
            with open(categories_path, "w") as f:
                json.dump(categories_dict, f, indent=4)
        except Exception as error:
            pass

    return tuple(categories)


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
    
    __slots__ = ["name", "data", "color"]

    def __init__(self, name, data, color=None):
        super().__init__()
        self.name = name
        self.data = data
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
        return Category(name, data, color=color)

    @classmethod
    def from_postgis(self, name, sql, conn, color=None, **kwargs):
        r"""Load a ``Category`` from a `PostGIS` database.
        This method wraps the ``read_postgis`` function from ``geopandas``.
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

    def save(self, outname):
        raise NotImplementedError

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
