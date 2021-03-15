# Encoding: UTF-8
# File: category.py
# Creation: Thursday December 31st 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
This module handles loading geometries.
The class :class:`~geolabel_maker.vectors.category.Category` wraps the :class:`geopandas.GeoDataFrame` class 
and contains two additional attributes: :attr:`name` and :attr:`color`.

.. code-block:: python

    # Basic imports
    import geopandas as gpd
    from geolabel_maker.vectors import Category
    
    # 1. Load directly from Geolabel Maker
    category = Category.open("categories/buildings.json", name="buildings", color=(255, 255, 255))
    
    # 1.1. Load from GeoPandas
    data = gpd.read_file("categories/buildings.json")
    category = Category(data, "buildings", color=(255, 255, 255))
    
    # 2. Change the coordinate reference system (CRS)
    out_category = category.to_crs("EPSG:4326")
    
    # 3. Crop the geometries
    out_category = category.crop((3, 34, 4, 35))
    
    # 4. Clip the geometries (modifies the structure of the vectors)
    out_category = category.clip((3, 34, 4, 35))
    
    # 5. Save your category
    out_category.save("category.json")
"""

# Basic imports
from abc import abstractmethod
from tqdm import tqdm
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from geolabel_maker.base import GeoBase, GeoData, GeoCollection, BoundingBox, CRS
from geolabel_maker.vectors.color import Color
from geolabel_maker.logger import logger


__all__ = [
    "Category",
    "CategoryCollection",
]


def _check_geopandas(element):
    r"""Checks if an object is a :class:`geopandas.GeoDataFrame`.

    Args:
        element (any): Element to check. 

    Examples:
        >>> _check_geopandas("buildings.json")
            ValueError("Element of class 'str' is not a 'geopandas.GeoDataFrame'.")
    """
    if not isinstance(element, gpd.GeoDataFrame):
        ValueError(f"Element of class '{type(element).__name__}' is not a 'geopandas.GeoDataFrame'.")


class CategoryBase(GeoBase):
    r"""
    Abstract architecture used to wrap all category elements.

    """

    @abstractmethod
    def clip(self, bbox, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def simplify(self, max_area, **kwargs):
        raise NotImplementedError


class Category(GeoData, CategoryBase):
    r"""
    A category is a set of vectors (or geometries) corresponding to different instances
    of the same geographic class (e.g. multiple buildings).
    A category must have a name (e.g. ``"buildings"``) and a color (e.g. ``"red"``),
    which will be used to draw the vectors on raster images (called labels).
    This class is used to extract polygons / geometries from satellite images, and then create the labels.

    * :attr:`data` (geopandas.GeoDataFrame): A table of geometries.

    * :attr:`filename` (str): Name of the category's file.

    * :attr:`crs` (CRS): Coordinate reference system.

    * :attr:`bounds` (BoundingBox): Bounding box of the geographic extent.

    * :attr:`name` (str): The name of the category corresponding to the elements.

    * :attr:`color` (tuple): RGB tuple of pixel values (from 0 to 255).


    """

    def __init__(self, data, name, color=None, filename=None):
        _check_geopandas(data)
        GeoData.__init__(self, data, filename=filename)
        self.name = name
        self._color = Color.get(color) if color else Color.random()

    @property
    def crs(self):
        try:
            return CRS(self.data.crs)
        except:
            logger.warning(f"There are no CRS for the category {self.name}. "
                           f"Maybe its in geographic coordinates, or try using `to_crs()` method.")
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
        r"""Loads a category from a vector file. 
        The supported extensions are the one supported by :func:`fiona` package.
        This method relies on :func:`geopandas.read_file` function.

        Args:
            filename (str): The path to the vector file.
            name (str, optional): Name of the category. If ``None``, the name will be ``filename``. Defaults to ``None``.
            color (tuple, optional): Color in the format :math:`(R, G, B)`. Defaults to ``None``.

        Returns:
            Category: The loaded category.

        Examples:
            If ``buildings.json`` is a geometry available from the disk, create a category with:

            >>> from geolabel_maker.vectors import Category
            >>> category = Category.open("buildings.json", "buildings", (255, 255, 255))
        """
        data = gpd.read_file(str(filename))
        name = name or Path(filename).stem
        return Category(data, name, color=color, filename=str(filename))

    @classmethod
    def from_postgis(cls, name, sql, conn, color=None, **kwargs):
        r"""Loads a category from a `PostGIS` database.
        This method relies on :func:`geopandas.read_postgis` function.

        Args:
            name (str, optional): Name of the category.
            sql (str): Query posted in the database.
            conn (DB connection object or SQLAlchemy engine): Connection to the database.
            color (tuple, optional): Color in the format :math:`(R, G, B)`. Defaults to ``None``.
            kwargs (dict): Remaining arguments.

        Returns:
            Category: The category from PostGis.

        Examples:
            We can use :func:`sqlalchemy` to connect to the database.

            >>> from sqlalchemy import create_engine  
            >>> db_connection_url = "postgres://myusername:mypassword@myhost:5432/mydb"
            >>> con = create_engine(db_connection_url)  

            Then, create your request:

            >>> sql = "SELECT geom FROM buildings"

            Finally, load your category:

            >>> category = Category.from_postgis("buildings", sql, con, color=(255, 255, 255))  
        """
        data = gpd.read_postgis(sql, conn, **kwargs)
        return Category(data, name, color=color)

    def save(self, out_file):
        """Saves the category in JSON format.
        This method relies on :func:`geopandas.GeoDataFrame.to_file` method.

        Args:
            out_file (str): Name of the output file.

        Returns:
            str: Path to the saved file.
        """
        self.data.to_file(out_file, driver="GeoJSON")
        return str(out_file)

    def overwrite(self, category):
        """Overwrites the current category by another.

        .. note::
            This operation will modify the values in place,
            and overwrite the category saved on the disk.

        Args:
            category (Category): The category to be saved.

        Returns:
            Category: The saved category.
        """
        if not self.filename:
            logger.warning(f"Could not overwrite a category loaded in memory. You should save it first.")
        else:
            category.save(self.filename)
            category = Category(category.data, category.name, color=category.color, filename=self.filename)
            self.data = category.data
            self.name = category.name
            self.color = category.color
        return category

    def to_crs(self, crs=None, overwrite=False, **kwargs):
        r"""Projects the category from its initial coordinate reference system (CRS) to another one.

        .. note::
            By default, this method will create an in-memory category.
            To automatically save it, use ``overwrite`` argument.

        Args:
            crs (str, pyproj.crs.CRS): The destination coordinate reference system (CRS).
            overwrite (bool, optional): If ``True``, overwrites the initial category saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Category: The projected category.

        Examples:
            If ``buildings.json`` is a category available from the disk, 
            change its CRS with:

            >>> category = Category.open("buildings.json", name="buildings", color=(255, 255, 255))
            >>> crs = "EPSG:4326"
            >>> out_category = category.to_crs(crs)

            The output category is loaded in-memory:

            >>> out_category.filename
                None

            To automatically replace the ``buildings.json`` with the output category,
            use the ``overwrite`` argument:

            >>> out_category = category.to_crs(crs, overwrite=True)
            >>> out_category.filename
                'buildings.json'
        """
        out_data = self.data.to_crs(crs=crs, **kwargs)
        out_category = Category(out_data, self.name, self.color)

        if overwrite:
            return self.overwrite(out_category)

        return out_category

    def crop(self, bbox, overwrite=False):
        r"""Crops a category within a bounding box.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the category.

        .. note::
            By default, this method will create an in-memory category.
            To automatically save it, use ``overwrite`` argument.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial category saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Category: The cropped category.

        Examples:
            If ``buildings.json`` is a category available from the disk, 
            crop it with:

            >>> category = Category.open("buildings.json", name="buildings", color=(255, 255, 255))
            >>> bbox = (1843000, 5173000, 1845000, 5174000)
            >>> out_category = category.crop(bbox)

            The output category is loaded in-memory:

            >>> out_category.filename
                None

            To automatically replace the ``buildings.json`` with the output category,
            use the ``overwrite`` argument:

            >>> out_category = category.crop(bbox, overwrite=True)
            >>> out_category.filename
                'buildings.json'
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
        out_data = self.data.cx[Xmin:Xmax, Ymin:Ymax]

        # Create the output category
        out_category = Category(out_data, self.name, color=self.color)

        if overwrite:
            return self.overwrite(out_category)

        return out_category

    def clip(self, bbox, overwrite=False):
        r"""Clips points, lines, or polygon geometries to the bounding box extent.
        This method will modify the structure of the points, lines, or polygons so that
        all parts outside of the bounding box are deleted.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the category.

        .. note::
            By default, this method will create an in-memory category.
            To automatically save it, use ``overwrite`` argument.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial category saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Category: The clipped category.

        Examples:
            If ``buildings.json`` is a category available from the disk, 
            clip it with:

            >>> category = Category.open("buildings.json", name="buildings", color=(255, 255, 255))
            >>> bbox = (1843000, 5173000, 1845000, 5174000)
            >>> out_category = category.clip(bbox)

            The output category is loaded in-memory:

            >>> out_category.filename
                None

            To automatically replace the ``buildings.json`` with the output category,
            use the ``overwrite`` argument:

            >>> out_category = category.clip(bbox, overwrite=True)
            >>> out_category.filename
                'buildings.json'
        """
        # Create the mask used to clip the data
        mask = gpd.GeoDataFrame([{"geometry": box(*bbox)}], crs=self.crs)

        # Clip the data
        out_data = self.data.copy()
        out_data["geometry"] = out_data.buffer(0)
        out_data = gpd.clip(out_data, mask)

        # Create the output category
        out_category = Category(out_data, name=self.name, color=self.color)

        if overwrite:
            return self.overwrite(out_category)

        return out_category

    def simplify(self, min_area=0, overwrite=False):
        r"""Simplify geometries by merging the overlaping ones and removing small ones.
        This method will modify the structure of the points, lines, or polygons.

        .. note::
            By default, this method will create an in-memory category.
            To automatically save it, use ``overwrite`` argument.

        Args:
            max_area (float): Minimum area (in meters) for each polygon. Defaults to ``0``.
            overwrite (bool, optional): If ``True``, overwrites the initial category saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Category: The simplified category.

        Examples:
            If ``buildings.json`` is a category available from the disk, 
            simpl it with:

            >>> category = Category.open("buildings.json", name="buildings", color=(255, 255, 255))
            >>> out_category = category.simplify(min_area=25)

            The output category is loaded in-memory:

            >>> out_category.filename
                None

            To automatically replace the ``buildings.json`` with the output category,
            use the ``overwrite`` argument:

            >>> out_category = category.simplify(min_area=25, overwrite=True)
            >>> out_category.filename
                'buildings.json'
        """
        # Merge overlapping polygons
        out_polygons = self.data.unary_union
        out_data = gpd.GeoDataFrame({"geometry": out_polygons}, crs=self.data.crs)
        out_data = out_data.loc[out_data.area > min_area]

        # Create the output category
        out_category = Category(out_data, self.name, color=self.color)

        if overwrite:
            return self.overwrite(out_category)

        return out_category

    def plot(self, ax=None, figsize=None, alpha=0.7, **kwargs):
        r"""Plots a category using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure the category. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from :func:`geopandas.GeoDataFrame.plot`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.
        """
        color = self.color.to_hex()
        ax = self.data.plot(ax=ax, figsize=figsize, color=color, alpha=alpha, **kwargs)
        ax = self.data.boundary.plot(ax=ax, edgecolor=color, **kwargs)
        handle = mpatches.Patch(facecolor=self.color.to_hex(), label=self.name)
        ax.legend(loc=1, handles=[handle], frameon=True)
        plt.title(f"{self.__class__.__name__}")
        return ax

    def inner_repr(self):
        rows, cols = self.data.shape
        return f"data=GeoDataFrame({rows} rows, {cols} columns), name='{self.name}', color={tuple(self.color)}"


class CategoryCollection(GeoCollection, CategoryBase):
    r"""
    A category collection is an ordered set of categories.
    This class behaves similarly as a list, 
    excepts it is made only of :class:`~geolabel_maker.vectors.category.Category`.

    .. note::
        The categories have unique colors.

    .. warning::
        If you initialize a :class:`~geolabel_maker.vectors.category.CategoryCollection` from categories with duplicated colors,
        the duplicated ones will be replaced with random colors.

    * :attr:`crs` (CRS): Coordinate reference system.

    * :attr:`bounds` (BoundingBox): Bounding box of the geographic extent.

    """

    __inner_class__ = Category

    def __init__(self, *categories):
        GeoCollection.__init__(self, *categories)

    @classmethod
    def open(cls, *filenames, **kwargs):
        r"""Opens multiple categories.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.open` method for further details.

        Returns:
            CategoryCollection

        Examples:
            If ``buildings.json`` and ``vegetation.json`` are vectors available from the disk, 
            open them with:

            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
        """
        return super().open(*filenames, **kwargs)

    def save(self, out_dir, in_place=True):
        r"""Saves all the categories in a given directory.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.save` method for further details.

        Args:
            out_dir (str): Path to the output directory.

        Returns:
            CategoryCollection: Collection of categories loaded in memory.
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        for i, category in enumerate(self._items):
            out_name = Path(category.filename).name if category.filename else f"{category.name}.json"
            out_file = Path(out_dir) / out_name
            category.save(out_file)
            # Update the collection
            if in_place:
                self._items[i] = Category(category.data, category.name, category.color, filename=out_file)
        return str(out_dir)

    def _make_unique_colors(self):
        colors = [category.color for category in self._items]
        for i, color in enumerate(colors):
            other_colors = set(colors[:i] + colors[i + 1:])
            max_steps = 200  # Prevent infinite loops
            while color in other_colors and max_steps > 0:
                color = Color.random()
                max_steps -= 1
            self._items[i].color = color

    def append(self, category):
        super().append(category)
        self._make_unique_colors()

    def extend(self, categories):
        super().extend(categories)
        self._make_unique_colors()

    def insert(self, index, category):
        super().insert(index, category)
        self._make_unique_colors()

    def colors(self):
        r"""Iterates on all colors.

        Yields:
            tuple: RGB color.
        """
        for category in self:
            yield category.color

    def names(self):
        r"""Iterates on all names.

        Yields:
            str: Name of the categories.
        """
        for category in self:
            yield category.name

    def to_crs(self, *args, **kwargs):
        r"""Projects all categories from their initial coordinate reference system (CRS) to another one.

        .. note::
            By default, this method will create in-memory categories.
            To automatically save it, use ``overwrite`` argument.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.to_crs` method for further details.

        Args:
            crs (CRS): The destination coordinate reference system (CRS).
            overwrite (bool, optional): If ``True``, overwrites the initial categories saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            CategoryCollection: The projected category collection.

        Examples:
            If ``buildings.json`` and ``vegetation.json`` are vectors available from the disk,
            change their CRS with:

            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> crs = "EPSG:4326"
            >>> out_categories = categories.to_crs(crs)
        """
        return super().to_crs(*args, **kwargs)

    def crop(self, *args, **kwargs):
        r"""Crops all categories in box extent.

        .. note::
            By default, this method will create in-memory categories.
            To automatically save it, use ``overwrite`` argument.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the category collection.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.crop` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.                
            overwrite (bool, optional): If ``True``, overwrites the initial categories saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            CategoryCollection: The cropped categories.

        Examples:
            If ``buildings.json`` and ``vegetation.json`` are vectors available from the disk, 
            crop them with:

            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> bbox = (1843000, 5173000, 1845000, 5174000)
            >>> out_categories = categories.crop(bbox)
        """
        return super().crop(*args, **kwargs)

    def clip(self, *args, **kwargs):
        r"""Clips all categories in box extent.

        .. note::
            By default, this method will create in-memory categories.
            To automatically save it, use ``overwrite`` argument.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the category collection.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.clip` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial categories saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            CategoryCollection: The cropped categories.

        Examples:
            If ``buildings.json`` and ``vegetation.json`` are vectors available from the disk, 
            clip them with:

            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> bbox = (1843000, 5173000, 1845000, 5174000)
            >>> out_categories = categories.clip(bbox)
        """
        out_categories = CategoryCollection()
        for category in tqdm(self._items, desc="Clipping", leave=True, position=0):
            try:
                out_categories.append(category.clip(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not clip category '{category.filename}': {error}")
        return out_categories

    def simplify(self, *args, **kwargs):
        r"""Clips all categories in box extent.

        .. note::
            By default, this method will create in-memory categories.
            To automatically save it, use ``overwrite`` argument.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the category collection.

        .. seealso::
            See :func:`~geolabel_maker.vectors.category.Category.clip` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the geometries,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial categories saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            CategoryCollection: The cropped categories.

        Examples:
            If ``buildings.json`` and ``vegetation.json`` are vectors available from the disk, 
            clip them with:

            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> bbox = (1843000, 5173000, 1845000, 5174000)
            >>> out_categories = categories.clip(bbox)
        """
        out_categories = CategoryCollection()
        for category in tqdm(self._items, desc="Simplifying", leave=True, position=0):
            try:
                out_categories.append(category.simplify(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not simplify category '{category.filename}': {error}")
        return out_categories

    def plot(self, ax=None, figsize=None, **kwargs):
        """Plots the data using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from :func:`geopandas.GeoDataFrame.plot`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.
        """
        # Create matplotlib axes
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)

        handles = []
        for category in self._items:
            ax = category.plot(ax=ax, **kwargs)
            handles.append(mpatches.Patch(facecolor=category.color.to_hex(), label=category.name))

        # Add legend and title
        ax.legend(loc=1, handles=handles, frameon=True)
        plt.title(f"{self.__class__.__name__}")

        return ax
