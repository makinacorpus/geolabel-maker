# Encoding: UTF-8
# File: dataset.py
# Creation: Monday December 28th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
This module handles the main usage of data manipulation of `geolabel_maker`.
From this module, you can generate labels, tiles and extract geometries / polygons
from raster images.

.. code-block:: python

    from geolabel_maker import Dataset
  
    # Open the dataset from a root directory
    dataset = Dataset.open("data/")
    
    # Generate the labels
    dataset.generate_labels()
    
    # Split the images / labels into mosaics
    dataset.generate_mosaics()
    
    # Generate subsets of tiles from images / labels
    dataset.generate_tiles()
"""

# Basic imports
import warnings
import inspect
import re
import json
from pathlib import Path
from tqdm import tqdm
from pyproj.crs import CRS
from shapely.geometry import box
from PIL import Image, ImageChops
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import rasterio
import rasterio.mask

# Geolabel Maker
from geolabel_maker.data import BoundingBox, GeoBase
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.rasters import utils
from geolabel_maker.vectors import Category, CategoryCollection
from geolabel_maker.utils import retrieve_path, relative_path
from geolabel_maker.logger import logger


# Global variables
Image.MAX_IMAGE_PIXELS = 156_250_000


class Dataset(GeoBase):
    r"""
    A ``Dataset`` is a combination of ``Raster`` and ``Category`` data.

    .. note::
        If a ``filename`` is provided,
        every processing steps are saved in this configuration file.

    * :attr:`root` (str): Path to the root of the dataset.

    * :attr:`filename` (str): Name of the configuration file associated to the dataset.

    * :attr:`dir_images` (str): Name of the directory containing the satellite images.

    * :attr:`dir_categories` (str): Name of the directory containing the vectors / geometries.

    * :attr:`dir_labels` (str): Name of the directory containing the labels associated to the satellite images.

    * :attr:`dir_mosaics` (str): Name of the directory containing the windows of the satellite images and labels.

    * :attr:`dir_tiles` (str): Name of the directory containing the slippy tiles of satellite images and labels.

    * :attr:`images` (list): Collection of raster images (usually satellite images).

    * :attr:`categories` (list): Collection of vector categories (usually geometries a.k.a ``GeoDataFrame``).

    * :attr:`labels` (list): Collection of raster labels (usually generated with ``generate_labels()``).

    """

    def __init__(self, images=None, categories=None, labels=None,
                 dir_images=None, dir_categories=None, dir_labels=None,
                 dir_mosaics=None, dir_tiles=None, filename=None):
        super().__init__()
        self.filename = str(Path(filename)) if filename else None
        self.dir_images = None if not dir_images else str(Path(dir_images))
        self.dir_categories = None if not dir_categories else str(Path(dir_categories))
        self.dir_labels = None if not dir_labels else str(Path(dir_labels))
        self.dir_mosaics = None if not dir_mosaics else str(Path(dir_mosaics))
        self.dir_tiles = None if not dir_tiles else str(Path(dir_tiles))
        self._images = RasterCollection(images)
        self._categories = CategoryCollection(categories)
        self._labels = RasterCollection(labels)
        self.save()

    @property
    def crs(self):
        collections = []
        if self.images:
            collections.append(self.images)
        if self.categories:
            collections.append(self.categories)
        if self.labels:
            collections.append(self.labels)
        crs = None
        for collection in collections:
            if crs is None:
                crs = CRS(collection.crs)
            elif crs and crs and CRS(collection.crs) != crs:
                error_msg = f"The CRS values from {self.__class__.__name__} are different: " \
                            f"got EPSG:{crs.to_epsg()} != EPSG:{CRS(collection.crs).to_epsg()}."
                warnings.warn(error_msg, RuntimeWarning)
                logger.warning(error_msg)
                return crs
        return crs

    @property
    def bounds(self):
        """Get the minimal geographic extend that covers both categories and images.

        Returns:
            BoundingBox
        """
        images_bounds = self.images.bounds
        labels_bounds = self.labels.bounds
        categories_bounds = self.categories.bounds

        bounds_array = [np.array([*bounds]) for bounds in [images_bounds, labels_bounds, categories_bounds] if bounds]
        if len(bounds_array) == 0:
            return None

        bounds_array = np.stack(bounds_array)
        left = np.max(bounds_array[:, 0])
        bottom = np.max(bounds_array[:, 1])
        right = np.min(bounds_array[:, 2])
        top = np.min(bounds_array[:, 3])
        return BoundingBox(left, bottom, right, top)

    @property
    def root(self):
        if self.filename:
            return str(Path(self.filename).parent)
        return None

    @bounds.setter
    def bounds(self, value):
        self._bounds = BoundingBox(*value)

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, rasters):
        self._images = RasterCollection(rasters)
        self.dir_images = None
        self.bounds = None

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, categories):
        self._categories = CategoryCollection(categories)
        self.dir_categories = None
        self.bounds = None

    @property
    def labels(self):
        return self._labels

    @labels.setter
    def labels(self, rasters):
        self._labels = RasterCollection(rasters)
        self.dir_labels = None

    @classmethod
    def open(cls, filename):
        r"""Load a ``Dataset`` from a configuration file in the ``json`` format.
        This file should be associated to a set of images and categories.
        Provide the ``images``, ``categories`` and ``labels`` you want to load from **directories** with:

        .. code-block:: json

            {
                "dir_images":  "images",
                "dir_categories":  "categories",
                "dir_labels":  "labels"
            }

        .. warning:: 
            Relative path must be relative to the configuration file,
            and not from the execution of the function.

        Alternatively, you can specify manually the path to each elements with:

        .. code-block:: json

            {
                "images":  [{
                    "filename": "images/raster.tif"
                }], 
                "categories":  [{
                    "filename": "categories/buildings.json",
                    "name": "buildings",
                    "color": "white"
                }],
                "labels":  [{
                    "filename": "labels/raster.tif"
                }]
            }

        .. note::
            You can mix both format. 
            Priority will be given to list of elements.

        .. note::
            If a root is specified instead of a configuration file (e.g. ``"data/"``),
            it will first try to load the file ``"data/dataset.json"``, if available.
            If not, it will create a default configuration file in the root directory ``"data/"``.

        Args:
            filename (str): Path to the configuration file.

        Returns:
            Dataset

        Examples:
            >>> dataset = Dataset.open("data/dataset.json")
            >>> dataset = Dataset.open("data/")
        """
        assert isinstance(filename, (str, Path)), f"Could not open the `Dataset` from {type(filename)}."
        # Load from a root directory
        if Path(filename).is_dir():
            filename = Path(filename) / "dataset.json"
            # Create a default configuration file if it does not exist.
            if not filename.exists():
                with open(filename, "w") as f:
                    json.dump({
                        "dir_images": "images",
                        "dir_categories": "categories",
                        "dir_labels": "labels"
                    }, f, indent=4)

        # Load the configuration file.
        with open(filename, "r", encoding="utf-8") as f:
            config = json.load(f)

        root = str(Path(filename).parent)
        images = config.get("images", None)
        categories = config.get("categories", None)
        labels = config.get("labels", None)
        dir_images = retrieve_path(config.get("dir_images", None), root=root)
        dir_categories = retrieve_path(config.get("dir_categories", None), root=root)
        dir_labels = retrieve_path(config.get("dir_labels", None), root=root)
        dir_mosaics = retrieve_path(config.get("dir_mosaics", None), root=root)
        dir_tiles = retrieve_path(config.get("dir_tiles", None), root=root)

        def load_collection(data_name, data_list=None, in_dir=None, desc="Loading"):
            collection = []
            data_class = eval(data_name)
            data_optional_args = dict(inspect.signature(data_class.open).parameters)
            data_optional_args = [arg for arg in data_optional_args if arg not in ["cls", "self", "filename"]]
            # Load rasters if provided from a list of dict.
            if data_list:
                in_dir = in_dir or root
                for data_info in tqdm(data_list, desc=desc, leave=True, position=0):
                    filename = retrieve_path(data_info["filename"], root=in_dir)
                    args = {arg: data_info.get(arg, None) for arg in data_optional_args}
                    collection.append(data_class.open(filename, **args))
            # Else, load all rasters from a directory.
            elif in_dir and Path(in_dir).exists():
                data_list = list(Path(in_dir).iterdir())
                for raster_path in tqdm(data_list, desc=desc, leave=True, position=0):
                    collection.append(data_class.open(raster_path))
            return collection

        # Load the different objects either from a directory or list of dict {"filename": path, **kwargs}.
        images = load_collection("Raster", data_list=images, in_dir=dir_images, desc="Loading Images")
        labels = load_collection("Raster", data_list=labels, in_dir=dir_labels, desc="Loading Labels")
        categories = load_collection("Category", data_list=categories, in_dir=dir_categories, desc="Loading Categories")

        return Dataset(images=images, categories=categories, labels=labels,
                       dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
                       dir_mosaics=dir_mosaics, dir_tiles=dir_tiles, filename=filename)

    @classmethod
    def download(cls, filename):
        """Dowload images and categories from `SentinelHub` and `OpenStreetMap`.
        A configuration file with the user credentials is required.

        Args:
            filename (str): Name of the configuration file containing the credentials.

        Returns:
            Dataset

        Examples:
            >>> dataset = Dataset.download("config.json")
        """

        with open(filename, "r", encoding="utf-8") as f:
            config = json.load(f)

        root = str(Path(filename).parent)
        dir_images = retrieve_path(config.get("dir_images", None), root=root)
        dir_categories = retrieve_path(config.get("dir_categories", None), root=root)
        bbox = config.get("bbox", None)
        sentinelhub = config.get("sentinelhub", None)
        mapbox = config.get("mapbox", None)
        overpass = config.get("overpass", None)

        assert bbox, "Could not download data if no bounding box is provided"
        images = []
        categories = []
        if sentinelhub:
            assert dir_images, "Could not download sentinel data if `dir_images` is not provided."
            username, password = sentinelhub.pop("username"), sentinelhub.pop("password")
            assert username, "Could not download sentinel data if `username` is not provided."
            assert password, "Could not download sentinel data if `password` is not provided."
            rasters = Raster.download(username, password, bbox, out_dir=dir_images, **sentinelhub)
            images.extend(rasters)
        if overpass:
            assert dir_categories, "Could not download overpass data if `dir_categories` is not provided."
            geometries = overpass.pop("geometries", None)
            assert geometries, "Could not download overpass data if `geometries` is not provided."
            for geometry in geometries:
                selector = geometry["selector"]
                name = geometry.pop("name", re.sub("[^a-zA-Z_-]", "_", selector))
                out_file = Path(dir_categories) / f"{name}.json"
                category = Category.download(bbox, out_file=out_file, **overpass, **geometry)
                categories.append(category)

        # filename = Path(filename).parent / "dataset.json"
        return Dataset(images, categories, dir_images=dir_images, dir_categories=dir_categories)

    def to_dict(self, root=None):
        r"""Convert the dataset to a dictionary.
        The dictionary is similar to a configuration file,
        excepts it does not contains directory information.

        Args:
            root (str, optional): Root path from where the files are relative to. 
                If ``None``, the root will be the current directory ``"."``. Default to ``None``.
            list_only (bool, optional): If ``True``, will add only ``images``, ``categories`` and ``labels`` as list,
                i.e. the directories information ``dir_images``etc. are skipped.
                Then, the files are referenced from ``root``. Default to ``False``. 

        Examples:
            >>> dataset = Dataset.open("../dataset.json")
            >>> data = dataset.to_dict(root="some/other/directory")
        """
        root = root or "."

        def jsonify_categories(values, out_dir=None):
            categories = []
            out_dir = out_dir or root
            for id, category in enumerate(values):
                filename = relative_path(category.filename, root=out_dir)
                categories.append({
                    "id": id,
                    "name": category.name,
                    "color": tuple(category.color),
                    "filename": str(filename)
                })
            return categories

        def jsonify_rasters(values, out_dir=None):
            rasters = []
            out_dir = out_dir or root
            for id, raster in enumerate(values):
                filename = relative_path(raster.filename, root=out_dir)
                rasters.append({
                    "id": id,
                    "filename": str(filename)
                })
            return rasters

        config = {}
        # Add elements only if they are not None.
        for key, value in self.__dict__.items():
            if value and key[:3] == "dir":
                config[key] = relative_path(value, root=root)
        if self.images:
            config["images"] = jsonify_rasters(self.images, self.dir_images)
        if self.categories:
            config["categories"] = jsonify_categories(self.categories, self.dir_categories)
        if self.labels:
            config["labels"] = jsonify_rasters(self.labels, self.dir_labels)
        return config

    def save(self, filename=None, **kwargs):
        r"""Save the dataset information in a configuration file.

        Args:
            filename (str): Name of the configuration file to be saved.
            kwargs (dict): Other arguments from ``ConfigDataset.to_dict()`` method.

        Examples:
            >>> dataset = Dataset.open("../dataset.json")
            >>> dataset.save("some/other/directory/dataset.json")
        """
        self.filename = filename or self.filename
        # Save if possible
        if not self.filename:
            return None

        config = self.to_dict(root=self.root, **kwargs)
        # If a previous configuration file exists, load it and overwrite only the items that changed.
        if Path(self.filename).exists():
            with open(self.filename, "r") as f:
                prev_config = json.load(f)
                prev_config.update(config)
                config = prev_config

        # Save and update the configuration file.
        with open(self.filename, "w") as f:
            json.dump(config, f, indent=4)

    def to_crs(self, crs, **kwargs):
        """Project all elements in the dataset to ``crs``.

        .. warning::
            The returned dataset is loaded in memory, 
            meaning it is not associated to a configuration ``filename``.

        Args:
            crs (str, pyproj.crs.CRS): Destination `CRS`.

        Returns:
            Dataset

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset_proj = dataset.to_crs("EPSG:4326")
            >>> dataset_proj.filename
                None
        """
        out_images = self.images.to_crs(crs, **kwargs)
        out_categories = self.categories.to_crs(crs, **kwargs)
        out_labels = self.labels.to_crs(crs, **kwargs)
        return Dataset(images=out_images, categories=out_categories, labels=out_labels,
                       dir_images=self.dir_images, dir_categories=self.dir_categories, dir_labels=self.dir_labels,
                       dir_mosaics=self.dir_mosaics, dir_tiles=self.dir_tiles, filename=None)

    def crop(self, bbox, **kwargs):
        """Crop the dataset from a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the dataset extent.

        Args:
            bbox (tuple): Bounding box used to crop the dataset,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            Dataset
        """
        out_images = self.images.crop(bbox, **kwargs)
        out_categories = self.categories.crop(bbox, **kwargs)
        out_labels = self.labels.crop(bbox, **kwargs)
        return Dataset(images=out_images, categories=out_categories, labels=out_labels,
                       dir_images=self.dir_images, dir_categories=self.dir_categories, dir_labels=self.dir_labels,
                       dir_mosaics=self.dir_mosaics, dir_tiles=self.dir_tiles, filename=None)

    def generate_labels(self, out_dir=None):
        r"""Generate labels from a set of ``images`` and ``categories``. 
        The label associated to an image in respect of the categories 
        is a ``.tif`` image containing all geometries 
        within the geographic extents from the origin image.
        The output labels are saved in the directory ``out_dir``. 

        .. note::
            This method will load the raster labels created dynamically.
            Access them through the ``Dataset.labels`` attribute.

        Args:
            out_dir (str, optional): Output directory where the file will be saved. 
                If ``None``, the file will be saved in ``"{root}/labels"``.
                Default to ``None``.

        Returns:
            str: Path to the directory containing the created ``Raster`` label.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()

            The labels are generated in ``"data/labels" ``.
        """
        # Clean previously generated labels
        self.labels = []
        dir_labels = str(out_dir or self.dir_labels or Path(self.root) / "labels")
        Path(dir_labels).mkdir(parents=True, exist_ok=True)

        # Generate and load the labels
        for image in tqdm(self.images, desc="Generating Labels", leave=True, position=0):
            label = image.mask(self.categories)
            label_path = Path(dir_labels) / f"{Path(image.filename).stem}-label.tif"
            label.save(label_path)
            self.labels.append(Raster.open(label_path))

        self.dir_labels = dir_labels
        self.save()
        return self.dir_labels

    def generate_vrt(self, make_images=True, make_labels=True, **kwargs):
        r"""Write virtual images from images and/or labels.

        .. seealso::
            Generate the labels with ``geolabel_maker.Dataset.generate_labels`` method.

        Args:
            make_images (bool, optional): If ``True``, generate a virtual image for georeferenced aerial images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate virtual image for georeferenced label images.  
                Defaults to ``True``.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_vrt(make_images=True, make_labels=True)
        """
        images_vrt = None
        labels_vrt = None

        # Make virtual images
        if make_images:
            out_file = Path(self.root) / "images.vrt"
            images_vrt = self.images.generate_vrt(str(out_file), **kwargs)

        # Make virtual labels
        if make_labels:
            out_file = Path(self.root) / "labels.vrt"
            labels_vrt = self.labels.generate_vrt(str(out_file), **kwargs)

        # Return the path to the created files
        if not labels_vrt:
            return images_vrt
        if not images_vrt:
            return labels_vrt
        return images_vrt, labels_vrt

    # TODO: write from a VRT image. Currently not supported in rasterio.
    # TODO: remove zoom directory before writing to file (issue if the user re-run with different width, height)
    def generate_mosaics(self, out_dir=None, make_images=True, make_labels=True, zoom=None, **kwargs):
        r"""Generate sets of mosaics from the images and labels. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        .. seealso::
            Generate the labels with ``geolabel_maker.Dataset.generate_labels`` method.

        Args:
            make_images (bool, optional): If ``True``, generate a mosaic for georeferenced images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate a mosaic for georeferenced label images.  
                Defaults to ``True``.
            out_dir (str, optional): Output directory where the tiles will be saved. 
                If ``None``, the tiles will be saved in ``"{root}/mosaics"``, where ``root`` reference the root dataset.
                The label mosaic will be saved under ``"{out_dir}/labels"``,
                and the image mosaic under ``"{out_dir}/images"``.
                Default to ``None``.
            kwargs (dict): Remaining arguments from ``Raster.generate_mosaic`` method.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_mosaic(make_images=True, make_labels=True)
        """
        dir_mosaics = str(out_dir or self.dir_mosaics or Path(self.root) / "mosaics")
        zoom_dir = str(zoom) if zoom else "original"

        # Generate mosaic from the images
        if make_images:
            out_dir = Path(dir_mosaics) / "images" / zoom_dir
            for image in tqdm(self.images, desc="Generating Image Mosaics", leave=True, position=0):
                image.generate_mosaic(out_dir=out_dir, zoom=zoom, **kwargs)

        # Generate mosaic from the labels
        if make_labels:
            out_dir = Path(dir_mosaics) / "labels" / zoom_dir
            for label in tqdm(self.labels, desc="Generating Label Mosaics", leave=True, position=0):
                label.generate_mosaic(out_dir=out_dir, zoom=zoom, **kwargs)

        self.dir_mosaics = dir_mosaics
        self.save()
        return self.dir_mosaics

    def generate_tiles(self, out_dir=None, make_images=True, make_labels=True, **kwargs):
        r"""Generate tiles from the images and optionally the generated labels.

        .. note::
            This method can generates two set of tiles: one from the ``images``, 
            and the other one from the ``labels``.

        .. seealso::
            Generate the labels with ``geolabel_maker.Dataset.generate_labels`` method.

        Args:
            make_images (bool, optional): If ``True``, generate tiles for georeferenced images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate tiles for georeferenced label images.  
                Defaults to ``True``.
            out_dir (str, optional): Output directory where the tiles will be saved. 
                If ``None``, the tiles will be saved in ``"{root}/tiles"``, where ``root`` reference the root dataset.
                The label tiles will be saved under ``"{out_dir}/labels"``,
                and the image tiles under ``"{out_dir}/images"``.
                Default to ``None``.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_tiles(make_images=True, make_labels=True, zoom="14-16")
        """
        dir_tiles = str(out_dir or self.dir_tiles or Path(self.root) / "tiles")

        # Generate tiles from the images
        if make_images:
            logger.info(f"Generating Image Tiles at {str(Path(dir_tiles) / 'images')}")
            out_dir_images = Path(dir_tiles) / "images"
            self.images.generate_tiles(out_dir_images, **kwargs)

        # Generate tiles from the labels
        if make_labels:
            logger.info(f"Generating Label Tiles at {str(Path(dir_tiles) / 'labels')}")
            out_dir_labels = Path(dir_tiles) / "labels"
            self.labels.generate_tiles(out_dir_labels, **kwargs)

        self.dir_tiles = dir_tiles
        self.save()
        return self.dir_tiles

    def plot_bounds(self, axes=None, figsize=None, dataset_color=None, image_color=None, category_color=None):
        """Show the geographic extent.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            image_color (str, optional): Name of the color used to show images. Defaults to ``None``.
            category_color (str, optional): Name of the color used to show categories. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        dataset_color = dataset_color or "red"
        image_color = image_color or "steelblue"
        category_color = category_color or "lightseagreen"
        axes = self.categories.plot_bounds(axes=axes, color=category_color, label="categories")
        axes = self.images.plot_bounds(axes=axes, color=image_color, label="images")

        # Plot the dataset bounding box
        bounds = self.bounds
        x, y = box(*bounds).exterior.xy
        axes.plot(x, y, color=dataset_color, label="dataset")
        axes.legend(loc=1, frameon=True)
        plt.title(f"Bounds of the Dataset")
        return axes

    def plot(self, axes=None, figsize=None, dataset_color=None, image_color=None, **kwargs):
        """Show the elements of the dataset.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            image_color (str, optional): Name of the color used to show images. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        # Create matplotlib axes
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)

        dataset_color = dataset_color or "red"
        image_color = image_color or "steelblue"
        axes = self.categories.plot(axes=axes, label="categories", **kwargs)
        axes = self.images.plot_bounds(axes=axes, color=image_color, label="images", **kwargs)

        # Add the legend
        handles = [mpatches.Patch(facecolor=category.color.to_hex(), label=category.name) for category in self.categories]
        handles.append(mpatches.Patch(facecolor="white", edgecolor=image_color, label="images"))
        axes.legend(loc=1, handles=handles, frameon=True)
        plt.title(f"Dataset")

        return axes

    def __repr__(self):
        rep = f"Dataset("
        if self.root:
            rep += f"\n  (root): '{self.root}'"
        for key, value in self.__dict__.items():
            # Add images / categories / labels if provided
            if value and key[0] == "_":
                rep += f"\n  ({key[1:]}): "
                rep += "\n  ".join(value.__repr__().split("\n"))
            # Add root / directories / options if provided
            elif value:
                rep += f"\n  ({key}): '{value}'"
        rep += f"\n)"
        return rep
