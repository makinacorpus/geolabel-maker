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
    category = Category(data, "buildings", color=(255, 255, 255))
    
"""

# Basic imports
import warnings
from pathlib import Path
from pyproj.crs import CRS
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from geolabel_maker.data import GeoData, GeoCollection, BoundingBox
from geolabel_maker.vectors.color import Color
from geolabel_maker.vectors.overpass import OverpassAPI
from geolabel_maker.logger import logger


__all__ = [
    "Category",
    "CategoryCollection",
]


def _check_geopandas(element, **kwargs):
    r"""Convert an object to a ``GeoDataFrame``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``Category`` etc...

    Returns:
        geopandas.GeoDataFrame

    Examples:
        >>> _check_geopandas("buildings.json")
            ValueError("Element of class 'str' is not a 'geopandas.GeoDataFrame'.")
        >>> _check_geopandas(Path("buildings.json"))
            ValueError("Element of class 'Path' is not a 'geopandas.GeoDataFrame'.")
        >>> _check_geopandas(gpd.read_file("buildings.json"))
            True
    """
    if not isinstance(element, gpd.GeoDataFrame):
        ValueError(f"Element of class '{type(element).__name__}' is not a 'geopandas.GeoDataFrame'.")
    return True


def _check_category(element):
    r"""Check if an object is a ``Category``.

    Args:
        element (any): Element to verify. 

    Raises:
        ValueError: If the element is not a ``Category``.

    Returns:
        bool: ``True`` if the element is a ``Category``.

    Examples:
        >>> _check_category("buildings.json")
            ValueError("Element of class 'str' is not a 'Category'.")
        >>> _check_category(Category.open("buildings.json"))
            True
    """
    if not isinstance(element, Category):
        raise ValueError(f"Element of class '{type(element).__name__}' is not a 'Category'.")
    return True


class Category(GeoData):
    r"""
    A category is a set of vectors (or geometries) corresponding to the same geographic element.
    A category must have a name (e.g. ``"buildings"``) and a RGB color (e.g. ``(255, 255, 255)``),
    which will be used to draw the vectors on raster images (called labels).
    This class is used to extract polygons / geometries from satellite images, and then create the labels.

    * :attr:`data` (geopandas.GeoDataFrame): A table of geometries.

    * :attr:`name` (str): The name of the category corresponding to the elements.

    * :attr:`color` (tuple): RGB tuple of pixel values (from 0 to 255).

    * :attr:`filename` (str): Name of the category's file.

    """

    def __init__(self, data, name, color=None, filename=None):
        _check_geopandas(data)
        super().__init__(data, filename=filename)
        self.name = name
        self._color = Color.get(color) if color else Color.random()

    @property
    def crs(self):
        try:
            return CRS(self.data.crs)
        except:
            error_msg = f"There are no CRS for the category {self.name}. " \
                        f"Maybe its in geographic coordinates, or try using `to_crs()` method."
            warnings.warn(error_msg, RuntimeWarning)
            logger.warning(error_msg)
            return None

    @property
    def bounds(self):
        return BoundingBox(*self.data.total_bounds)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = Color.get(value)

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
        return Category(data, name, color=color, filename=str(filename))

    @classmethod
    def download(cls, bbox, **kwargs):
        """Download a geometry using the `Open Street Map` API.

        Args:
            bbox (tuple): Bounding box used to retrieve geometries, 
                in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            kwargs (dict): Arguments used in the ``OverpassAPI`` download method.

        Returns:
            Category
        """
        api = OverpassAPI()
        color = kwargs.pop("color", None)
        name = kwargs.pop("name", None)
        filename = api.download(bbox, **kwargs)
        return Category.open(filename, name=name, color=color)

    @classmethod
    def from_postgis(cls, name, sql, conn, color=None, **kwargs):
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
        return Category(data, name, color=color)

    def save(self, out_file):
        """Save the category in `JSON` format.

        Args:
            out_file (str): Name of the output file.
        """
        self.data.to_file(out_file, driver="GeoJSON")

    def to_crs(self, crs, **kwargs):
        r"""Project the category from its initial `CRS` to another one.

        .. note::
            This method will create an in-memory category.

        Args:
            crs (str, pyproj.crs.CRS): The destination `CRS`.

        Returns:
            Category
        """
        data = self.data.to_crs(crs, **kwargs)
        out_category = Category(data, self.name, self.color)
        return out_category

    def crop(self, bbox):
        r"""Get the geometries which are in a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the geometries.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            list: The geometries of the tif file's geographic extent.

        Examples:
            >>> from geolabel_maker.vectors import Category
            >>> category = Category.open("categories/buildings.json", name="buildings", color=(255, 255, 255))
            >>> category_cropped = category.crop((1843000, 5173000, 1845000, 5174000))
        """
        # Create a polygon from the bbox
        Xmin, Ymin, Xmax, Ymax = bbox

        # Create a polygon from the raster bounds
        XCmin, YCmin, XCmax, YCmax = self.data.total_bounds

        # Make sure the raster bbox is contained in the vector bbox
        Xmin = max(Xmin, XCmin)
        Xmax = min(Xmax, XCmax)
        Ymin = max(Ymin, YCmin)
        Ymax = min(Ymax, YCmax)
        sub_data = self.data.cx[Xmin:Xmax, Ymin:Ymax]

        return Category(sub_data, self.name, color=self.color, filename=self.filename)

    def plot(self, axes=None, figsize=None, **kwargs):
        """Plot a category.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show the category. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        color = self.color.to_hex()
        axes = self.data.plot(ax=axes, figsize=figsize, color=color, **kwargs)
        handle = mpatches.Patch(facecolor=self.color.to_hex(), label=self.name)
        axes.legend(loc=1, handles=[handle], frameon=True)
        plt.title(f"Bounds of the {self.__class__.__name__}")
        return axes

    def inner_repr(self):
        rows, cols = self.data.shape
        return f"data=GeoDataFrame({rows} rows, {cols} columns), name='{self.name}', color={tuple(self.color)}"


class CategoryCollection(GeoCollection):
    r"""
    Defines a collection of ``Category``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Category``.

    .. note::
        The ``Category`` within the ``CategoryCollection`` have unique colors.

    .. warning::
        If you initialize a ``CategoryCollection`` from categories with shared colors,
        the duplicated colors will be replaced with random ones.

    """

    def __init__(self, *categories):
        super().__init__(*categories)

    @classmethod
    def open(cls, *filenames, **kwargs):
        r"""Open multiple categories.

        Returns:
            CategoryCollection

        Examples:
            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
        """
        categories = []
        for filename in filenames:
            categories.append(Category.open(filename, **kwargs))
        return CategoryCollection(*categories)

    def save(self):
        raise NotImplementedError

    def _make_unique_colors(self):
        """Make sure the categories have unique colors."""
        colors = [category.color for category in self._items]
        for i, color in enumerate(colors):
            other_colors = set(colors[:i] + colors[i + 1:])
            max_steps = 200  # Prevent infinite loops
            while color in other_colors and max_steps > 0:
                color = Color.random()
                max_steps -= 1
            self._items[i].color = color

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
                  (0): Category(filename='buildings.json', name='buildings', color=(234, 85, 40))
                )
        """
        _check_category(category)
        self._items.append(category)
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
                  (0): Category(filename='buildings.json', name='buildings', color=(234, 85, 40))
                  (1): Category(filename='vegetation.json', name='vegetation',  color=(35, 3, 220))
                )
        """
        categories = [category for category in categories if _check_category(category)]
        self._items.extend(categories)
        self._make_unique_colors()

    def insert(self, index, category):
        """Insert a ``Category`` at the desired index.

        Args:
            index (int): Index.
            category (Category): Category to insert.
        """
        _check_category(category)
        self._items[index] = category
        self._make_unique_colors()

    def colors(self):
        """Iterate on all colors.

        Yields:
            tuple: RGB color.
        """
        for category in self:
            yield category.color

    def names(self):
        """Iterate on all names.

        Yields:
            str: Name of the categories.
        """
        for category in self:
            yield category.name

    def crop(self, bbox):
        """Crop all categories from a bounding box.

        .. seealso::
            See ``Category.crop()`` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.                

        Returns:
            CategoryCollection
        """
        categories = CategoryCollection()
        for category in self:
            try:
                category_cropped = category.crop(bbox)
                if category_cropped and not category_cropped.data.empty:
                    categories.append(category.crop(bbox))
            except Exception as error:
                pass
        return categories

    def plot(self, axes=None, figsize=None, **kwargs):
        """Plot the the data.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        handles = []
        for category in self._items:
            axes = category.plot(axes=axes, **kwargs)
        handles = [mpatches.Patch(facecolor=category.color.to_hex(), label=category.name) for category in self._items]
        axes.legend(loc=1, handles=handles, frameon=True)
        plt.title(f"{self.__class__.__name__}")
        return axes
