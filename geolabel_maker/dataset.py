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
import inspect
import re
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
import rasterio.mask
from shapely.geometry import box
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from geolabel_maker.base import BoundingBox, CRS, GeoBase
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.rasters.utils import color_mask, merge_masks
from geolabel_maker.vectors import Category, CategoryCollection
from geolabel_maker.downloads import SentinelHubAPI, MapBoxAPI, OverpassAPI
from geolabel_maker.utils import retrieve_path, relative_path
from geolabel_maker.logger import logger


class Dataset(GeoBase):
    r"""
    A dataset is a combination of raster and vector data.

    .. note::
        If a ``filename`` is provided,
        every processing steps are saved in this configuration file.

    * :attr:`crs`: The coordinate reference system.

    * :attr:`bounds`: The geographic extent shared by rasters and vectors.

    * :attr:`root` (str): Path to the root of the dataset.

    * :attr:`filename` (str): Name of the configuration file associated to the dataset.

    * :attr:`dir_images` (str): Name of the directory containing the satellite images.

    * :attr:`dir_categories` (str): Name of the directory containing the vectors / geometries.

    * :attr:`dir_labels` (str): Name of the directory containing the labels associated to the satellite images.

    * :attr:`dir_mosaics` (str): Name of the directory containing the windows of the satellite images and labels.

    * :attr:`dir_tiles` (str): Name of the directory containing the slippy tiles of satellite images and labels.

    * :attr:`images` (list): Collection of raster images (usually satellite images).

    * :attr:`categories` (list): Collection of vector categories (i.e. geometries).

    * :attr:`labels` (list): Collection of raster labels (usually generated with :func:`~geolabel_maker.dataset.Dataset.generate_labels`).

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
        self.save(overwrite=True)

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
                logger.warning(f"The CRS values from '{self.__class__.__name__}' are different: " \
                               f"got EPSG:{crs.to_epsg()} and EPSG:{CRS(collection.crs).to_epsg()}.", RuntimeWarning)
                return crs
        return crs

    @property
    def bounds(self):
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
        r"""Loads a dataset from a configuration file in the JSON format.
        This file should be associated to a set of images and categories.

        .. warning:: 
            Relative path must be relative to the configuration file,
            and not from the execution of the function.

        Args:
            filename (str): Path to the configuration file.

        Returns:
            Dataset: The loaded dataset.

        Examples:
            Load a dataset with a minimal configuration ``dataset.json``:

            .. code-block:: json

                {
                    "dir_images":  "images",
                    "dir_categories":  "categories",
                    "dir_labels":  "labels"
                }

            This configuration will look for all images saved in ``images``, vectors in ``categories`` 
            and label images (if any) in ``labels``.

            >>> dataset = Dataset.open("dataset.json")

            If you wan to control more precisely the loading process, you can provide a more detailed configuration:

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
                You can mix both format (using directories or list of files). 
                Priority will be given to list of files.

            >>> dataset = Dataset.open("dataset.json")
        """
        if not Path(filename).is_file():
            raise ValueError(f"Could not read the dataset from configuration file '{filename}'.")

        # Load the configuration file.
        logger.debug(f"Opening the configuration file '{filename}'.")
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

        def load_collection(data_class, data_list=None, in_dir=None, desc="Loading"):
            r"""Loads a collection of raster or vector.

            Args:
                data_class (Raster or Category): Data to be loaded. Eg. ``Raster`` or ``Category``.
                data_list (list, optional): List of files provided from the configuration. Defaults to ``None``.
                in_dir (str, optional): Name of the directory used to search files. Defaults to ``None``.
                desc (str, optional): Message displayed while loading. Defaults to ``"Loading"``.

            Returns:
                GeoCollection: The loaded collection depending on the data type.
            """
            logger.debug(f"Loading '{data_class.__name__}' collection.")
            collection = []
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
            logger.debug(f"Successfully loaded '{data_class.__name__}'.")
            return collection

        # Load the different objects either from a directory or list of dict {"filename": path, **kwargs}.
        images = load_collection(Raster, data_list=images, in_dir=dir_images, desc="Loading Images")
        labels = load_collection(Raster, data_list=labels, in_dir=dir_labels, desc="Loading Labels")
        categories = load_collection(Category, data_list=categories, in_dir=dir_categories, desc="Loading Categories")
        logger.debug(f"Configuration file successfully loaded.")

        return Dataset(images=images, categories=categories, labels=labels,
                       dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
                       dir_mosaics=dir_mosaics, dir_tiles=dir_tiles, filename=filename)

    @classmethod
    def from_dir(cls, dir_images=None, dir_categories=None, dir_labels=None):
        r"""Loads a dataset from directories.

        Args:
            dir_images (str): Path to the images directory.
            dir_categories (str): Path to the categories directory.
            dir_labels (str): Path to the labels directory.

        Returns:
            Dataset: The loaded dataset.

        Examples:
            You can load a dataset directly from directories.
            It will create a default configuration in the working directory.

            >>> dataset = Dataset.from_dir(dir_images="images", dir_categories="categories")
        """
        images = RasterCollection.from_dir(dir_images)
        labels = RasterCollection.from_dir(dir_labels)
        categories = CategoryCollection.from_dir(dir_categories)
        return cls(images=images, categories=categories, labels=labels,
                   dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels)

    @classmethod
    def from_root(cls, root):
        r"""Loads a dataset from a root directory.
        The root directory must either contains a configuration file named ``dataset.json``,
        or directories named ``images``, ``categories`` and ``labels``.

        .. note:: 
            If a configuration file named ``dataset.json`` exists in the root directory,
            it will be loaded.

        Args:
            dir_images (str): Path to the images directory.
            dir_categories (str): Path to the categories directory.
            dir_labels (str): Path to the labels directory.

        Returns:
            Dataset: The loaded dataset.

        Examples:
            You can load a dataset directly from a root.
            It will create a default configuration in the working directory.

            >>> dataset = Dataset.from_root("data")
        """
        if not Path(root).is_dir():
            raise ValueError(f"Could not open the 'Dataset' from root './'.")

        filename = Path(root) / "dataset.json"
        # Create a default configuration file if it does not exist.
        if not filename.exists():
            logger.debug(f"No configuration file found at root '{filename.parent}'. " \
                         f"Creating a default configuration '{filename}'.")
            with open(filename, "w") as f:
                json.dump({
                    "dir_images": "images",
                    "dir_categories": "categories",
                    "dir_labels": "labels"
                }, f, indent=4)

        return cls.open(filename)

    @classmethod
    def download(cls, filename):
        r"""Dowloads images and categories from `SentinelHub <https://docs.sentinel-hub.com>`__, 
        `MapBox <https://docs.mapbox.com>`__ and 
        `Open Street Map <https://www.openstreetmap.org/>`__ .
        A configuration file with the user credentials is required.

        Args:
            filename (str): Name of the configuration file containing the credentials.

        Returns:
            Dataset: The downloaded dataset.

        Examples:
            If you provided credentials in ``config.json`` as:
            
            .. code-block:: json 

                {
                    "dir_images": "images",
                    "dir_categories": "categories",
                    "bbox": [2.34, 48.84, 2.36, 48.86],
                    "sentinelhub": {
                        "username": "...",
                        "password": "...",
                        "date": ["20200920", "20201020"],
                        "platformname": "Sentinel-2",
                        "processinglevel": "Level-2A",
                        "cloudcoverpercentage": [0, 10],
                        "bandname": "TCI",
                        "resolution": 10
                    },
                    "mapbox": {
                        "access_token": "pk...",
                        "zoom": 17, 
                        "high_res": true,
                        "slippy_maps": false,
                        "width": 10240,       
                        "height": 10240,   
                    },
                    "overpass": {
                        "geometries": [
                            {
                                "selector": "building",
                                "name": "buildings"
                            },
                            {
                                "selector": "natural=wood",
                                "name": "woods"
                            }
                        ]
                    }
                } 
            
            You can download the corresponding data with:

            >>> dataset = Dataset.download("config.json")
        """
        logger.debug(f"Opening the configuration file '{Path(filename)}'.")
        with open(filename, "r", encoding="utf-8") as f:
            config = json.load(f)

        root = str(Path(filename).parent)
        dir_images = retrieve_path(config.get("dir_images", "images"), root=root)
        dir_categories = retrieve_path(config.get("dir_categories", "categories"), root=root)
        bbox = config.get("bbox", None)
        sentinelhub = config.get("sentinelhub", None)
        mapbox = config.get("mapbox", None)
        overpass = config.get("overpass", None)

        assert bbox, "Could not download data if no bounding box is provided"
        if sentinelhub:
            username, password = sentinelhub.pop("username", None), sentinelhub.pop("password", None)
            assert username, "Could not download sentinel data if 'username' is not provided."
            assert password, "Could not download sentinel data if 'password' is not provided."
            api = SentinelHubAPI(username, password)
            api.download(bbox, out_dir=dir_images, **sentinelhub)

        if mapbox:
            access_token = mapbox.pop("access_token", None)
            assert access_token, "Could not download mapbox data if 'access_token' is not provided."
            api = MapBoxAPI(access_token)
            api.download(bbox, out_dir=dir_images, **mapbox)

        if overpass:
            geometries = overpass.pop("geometries", None)
            assert geometries, "Could not download overpass data if 'geometries' is not provided."
            api = OverpassAPI()
            for geometry in geometries:
                selector = geometry.get("selector", None)
                assert selector, "Could not download categories if 'selector' is not provided."
                name = geometry.pop("name", re.sub("[^a-zA-Z_-]", "_", selector))
                out_file = Path(dir_categories) / f"{name}.json"
                api.download(bbox, selector=selector, out_file=out_file, **overpass)

        return Dataset.from_dir(dir_images=dir_images, dir_categories=dir_categories)

    def to_dict(self, root=None):
        r"""Converts the dataset to a dictionary.
        The dictionary is similar to a configuration file,
        excepts it does not contains directory information.

        Args:
            root (str, optional): Root path from where the files are relative to. 
                If ``None``, the root will be the current directory ``"."``. Defaults to ``None``.
            list_only (bool, optional): If ``True``, will adds only ``images``, ``categories`` and ``labels`` as list,
                i.e. the directories information ``dir_images`` etc. are skipped.
                Then, the files are referenced from ``root``. Defaults to ``False``. 

        Returns:
            dict: The dataset's configuration.

        Examples:
            If ``dataset.json`` is a configuration file, load the dataset with:

            >>> dataset = Dataset.open("dataset.json")

            Then, all the paths linking images and vectors are relative to the working directory, ``./`` in this case.
            To generate a configuration linking images from another directory, you can use the above method:

            >>> config = dataset.to_dict(root="some/other/directory")

            Then, all paths will be relative to ``some/other/directory``.
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

    def save(self, filename=None, overwrite=False, **kwargs):
        r"""Saves the dataset information in a configuration file.

        .. warning::
            This method will update the ``filename`` dataset's attribute 
            if the associated argument is provided.

        Args:
            filename (str): Name of the configuration file to be saved.
            kwargs (dict): Other arguments from ``ConfigDataset.to_dict()`` method.

        Returns:
            str: Path to the saved configuration file.

        Examples:
            If ``dataset.json`` is a configuration file, load the dataset with:

            >>> dataset = Dataset.open("dataset.json")

            Then, all the paths linking images and vectors are relative to the working directory, ``./`` in this case.
            To generate a configuration linking images from another directory, you can use the above method:

            >>> config = dataset.save("some/other/directory/dataset.json")

            Then, all paths will be relative to ``some/other/directory``.
        """
        self.filename = filename or self.filename or "dataset.json"

        config = self.to_dict(root=self.root, **kwargs)
        # If a previous configuration file exists, load it and overwrite only the items that changed.
        if not overwrite and Path(self.filename).exists():
            with open(self.filename, "r") as f:
                prev_config = json.load(f)
                prev_config.update(config)
                config = prev_config

        # Save and update the configuration file.
        with open(self.filename, "w") as f:
            json.dump(config, f, indent=4)

        return self.filename

    def to_crs(self, crs, **kwargs):
        r"""Projects all elements in the dataset to ``crs``.

        .. warning::
            The returned dataset is loaded in memory, 
            meaning it is not associated to a configuration ``filename``.

        Args:
            crs (str, pyproj.crs.CRS): Destination `CRS`.

        Returns:
            Dataset: The dataset in another CRS.

        Examples:
            If ``data`` is a directory containing images in ``images`` and vectors in ``categories`` directories,
            then load the dataset with:

            >>> dataset = Dataset.open("data/")

            Once loaded, convert all the dataset's elements to another CRS with:

            >>> crs = "EPSG:4326"
            >>> out_dataset = dataset.to_crs(crs)

            Notice that the resulted dataset is loaded in-memory:

            >>> out_dataset.filename
                None
        """
        out_images = self.images.to_crs(crs, **kwargs)
        out_categories = self.categories.to_crs(crs, **kwargs)
        out_labels = self.labels.to_crs(crs, **kwargs)
        return Dataset(images=out_images, categories=out_categories, labels=out_labels,
                       dir_images=self.dir_images, dir_categories=self.dir_categories, dir_labels=self.dir_labels,
                       dir_mosaics=self.dir_mosaics, dir_tiles=self.dir_tiles, filename=None)

    def crop(self, bbox, **kwargs):
        r"""Crops the dataset from a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the dataset extent.

        Args:
            bbox (tuple): Bounding box used to crop the dataset,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            Dataset: The dataset with cropped elements.

        Examples:
            If ``data`` is a directory containing images in ``images`` and vectors in ``categories`` directories,
            then load the dataset with:

            >>> dataset = Dataset.open("data")

            Then, crop all its elements with:

            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> out_dataset = dataset.crop(bbox)

            Notice that the resulted dataset is loaded in-memory:

            >>> out_dataset.filename
                None
        """
        out_images = self.images.crop(bbox, **kwargs)
        out_categories = self.categories.crop(bbox, **kwargs)
        out_labels = self.labels.crop(bbox, **kwargs)
        return Dataset(images=out_images, categories=out_categories, labels=out_labels,
                       dir_images=self.dir_images, dir_categories=self.dir_categories, dir_labels=self.dir_labels,
                       dir_mosaics=self.dir_mosaics, dir_tiles=self.dir_tiles, filename=None)

    def generate_label(self, image_idx, out_file=None):
        r"""Generates label corresponding to one image. 
        The label associated to an image in respect of the categories 
        is a ``.tif`` image containing all geometries 
        within the geographic extents from the origin image.

        Args:
            out_file (str, optional): Output directory where the file will be saved. 

        Returns:
            str: Path to the created label.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_label(0)
        """
        image = self.images[image_idx]
        # Generate the mask
        label = image.mask(self.categories)
        out_file = out_file or Path(image.filename).parent / f"{Path(image.filename).stem}-label.tif" or f"image-{image_idx}-label.tif"
        label.save(out_file)
        # Close the label
        label.data.close()
        return str(out_file)

    def generate_labels(self, out_dir=None):
        r"""Generates labels from a set of ``images`` and ``categories``. 
        The label associated to an image in respect of the categories 
        is a ``.tif`` image containing all geometries 
        within the geographic extents from the origin image.
        The output labels are saved in the directory ``out_dir``. 

        .. note::
            This method will load the raster labels created dynamically.
            Access them through the :attr:`labels` attribute.

        Args:
            out_dir (str, optional): Output directory where the file will be saved. 
                If ``None``, the labels will be saved in the directory ``labels`` under the root dataset.
                Defaults to ``None``.

        Returns:
            str: Path to the directory containing the created label.

        Examples:
            By default, the labels are generated ``data/labels`` directory.

            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()

            The labels are generated in ``data/labels``.
        """
        # Clean previously generated labels
        self.labels = []
        dir_labels = str(out_dir or self.dir_labels or Path(self.root) / "labels")
        Path(dir_labels).mkdir(parents=True, exist_ok=True)

        # Generate and load the labels
        for image_idx, image in enumerate(tqdm(self.images, desc="Generating Labels", leave=True, position=0)):
            label_path = Path(dir_labels) / f"{Path(image.filename).stem}-label.tif"
            self.generate_label(image_idx, out_file=label_path)
            self.labels.append(Raster.open(label_path))

        self.dir_labels = dir_labels
        self.save()
        return self.dir_labels

    def generate_vrt(self, make_images=True, make_labels=True, **kwargs):
        r"""Writes virtual images from images and/or labels.

        .. seealso::
            Generate the labels with :func:`~geolabel_maker.Dataset.generate_labels` method.

        Args:
            make_images (bool, optional): If ``True``, generates a virtual image for georeferenced aerial images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generates virtual image for georeferenced label images.  
                Defaults to ``True``.

        Returns:
            str: The path(s) to the virtual image(s).

        Examples:
            If ``data`` is a directory containing images in ``images`` and vectors in ``categories`` directories,
            then load the dataset with:

            >>> dataset = Dataset.open("data")

            Generate virtual rasters with:

            >>> dataset.generate_vrt(make_images=True, make_labels=True)

            Notice that the argument ``make_labels`` is set to ``True``.
            To work, the dataset must have labels (generated with ``generate_labels``).
        """
        images_vrt = None
        labels_vrt = None

        # Make virtual images
        if make_images:
            out_file = Path(self.root) / "images.vrt"
            logger.info(f"Generating Images VRT at '{out_file}'.")
            images_vrt = self.images.generate_vrt(str(out_file), **kwargs)

        # Make virtual labels
        if make_labels:
            out_file = Path(self.root) / "labels.vrt"
            logger.info(f"Generating Labels VRT at '{out_file}'.")
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
        r"""Generates mosaics from the images and labels. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        .. seealso::
            Generate the labels with :func:`~geolabel_maker.Dataset.generate_labels` method.

        Args:
            make_images (bool, optional): If ``True``, generates a mosaic for georeferenced images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generates a mosaic for georeferenced label images.  
                Defaults to ``True``.
            out_dir (str, optional): Output directory where the mosaics will be saved. 
                If ``None``, the tiles will be saved in the directory ``mosaics`` under the root dataset.
                Defaults to ``None``.
            kwargs (dict): Remaining arguments from ``Raster.generate_mosaic`` method.

        Returns:
            str: The path to the output directory.

        Examples:
            If ``data`` is a directory containing images in ``images`` and vectors in ``categories`` directories,
            then load the dataset with:

            >>> dataset = Dataset.open("data/")

            Before creating a mosaic, the dataset must contains labels. If not, generate them with:

            >>> dataset.generate_labels()

            Then, generate mosaics for both images and labels:

            >>> dataset.generate_mosaics(make_images=True, make_labels=True, zoom="18")
        """
        dir_mosaics = str(out_dir or self.dir_mosaics or Path(self.root) / "mosaics")
        zoom_name = str(zoom or "original")

        # Generate mosaics from the images
        if make_images:
            out_dir = Path(dir_mosaics) / "images" / zoom_name
            logger.info(f"Generating Images Mosaics at '{out_dir}'.")
            self.images.generate_mosaics(out_dir=out_dir, zoom=zoom, **kwargs)

        # Generate mosaics from the labels
        if make_labels:
            out_dir = Path(dir_mosaics) / "labels" / zoom_name
            logger.info(f"Generating Labels Mosaics at '{out_dir}'.")
            kwargs.pop("resampling", None)
            self.labels.generate_mosaics(out_dir=out_dir, zoom=zoom, resampling="nearest", **kwargs)

        self.dir_mosaics = dir_mosaics
        self.save()
        return self.dir_mosaics

    def generate_tiles(self, out_dir=None, make_images=True, make_labels=True, **kwargs):
        r"""Generates tiles from the images and optionally the generated labels.

        .. note::
            This method can generates two set of tiles: one from the ``images``, 
            and the other one from the ``labels``.

        .. seealso::
            Generate the labels with ``geolabel_maker.Dataset.generate_labels`` method.

        Args:
            make_images (bool, optional): If ``True``, generates tiles for georeferenced images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generates tiles for georeferenced label images.  
                Defaults to ``True``.
            out_dir (str, optional): Output directory where the tiles will be saved. 
                If ``None``, the tiles will be saved in the directory ``tiles`` under the root dataset.
                Defaults to ``None``.

        Examples:
            If ``data`` is a directory containing images in ``images`` and vectors in ``categories`` directories,
            then load the dataset with:

            >>> dataset = Dataset.open("data/")

            Before creating a mosaic, the dataset must contains labels. If not, generate them with:

            >>> dataset.generate_labels()

            Then, generate tiles for both images and labels:

            >>> dataset.generate_tiles(make_images=True, make_labels=True, zoom="18")
        """
        dir_tiles = str(out_dir or self.dir_tiles or Path(self.root) / "tiles")

        # Generate tiles from the images
        if make_images:
            out_dir = Path(dir_tiles) / "images"
            logger.info(f"Generating Images Tiles at '{out_dir}'.")
            self.images.generate_tiles(out_dir, **kwargs)

        # Generate tiles from the labels
        if make_labels:
            out_dir = Path(dir_tiles) / "labels"
            logger.info(f"Generating Labels Tiles at '{out_dir}'.")
            self.labels.generate_tiles(out_dir, **kwargs)

        self.dir_tiles = dir_tiles
        self.save()
        return self.dir_tiles

    def plot_bounds(self, ax=None, figsize=None):
        r"""Plots the geographic extent of the images and categories using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.
        """
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)

        ax = self.categories.plot_bounds(ax=ax)
        ax = self.images.plot_bounds(ax=ax)

        # Plot the dataset bounding box
        bounds = self.bounds
        x, y = box(*bounds).exterior.xy
        ax.legend(loc=1, frameon=True)
        plt.title(f"Bounds of the Dataset")
        return ax

    def plot(self, ax=None, figsize=None, alpha=0.5, **kwargs):
        r"""Plots the images and categories of the dataset using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            image_color (str, optional): Name of the color used to show images. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.
        """
        # Create matplotlib axes
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)

        # Visualize images + bounds and categories
        ax = self.images.plot(ax=ax, **kwargs)
        ax = self.categories.plot(ax=ax, alpha=alpha, **kwargs)

        # Add the legend
        category_handles = []
        image_handles = []
        for category in self.categories:
            category_handles.append(mpatches.Patch(facecolor=category.color.to_hex(), label=category.name))
        for i, image in enumerate(self.images):
            label = Path(image.filename).stem if image.filename else f"image {i}"
            image_handles.append(mpatches.Patch(facecolor="none", label=label))
        handles = category_handles + image_handles
        ax.legend(loc=1, handles=handles, frameon=True)
        # Add a title
        plt.title(self.__class__.__name__)

        return ax

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
