# Encoding: UTF-8
# File: config.py
# Creation: Saturday February 6th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
import json

# Geolabel Maker
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.vectors import Category, CategoryCollection
from geolabel_maker.utils import retrieve_path, relative_path


#! deprecated
class ConfigDataset:

    def __init__(self, images=None, categories=None, labels=None,
                 dir_images=None, dir_categories=None, dir_labels=None,
                 dir_mosaics=None, dir_tiles=None, filename=None):

        self.filename = filename or "config.json"
        self.dir_images = dir_images
        self.dir_categories = dir_categories
        self.dir_labels = dir_labels
        self.dir_mosaics = dir_mosaics
        self.dir_tiles = dir_tiles
        self._images = RasterCollection(images)
        self._categories = CategoryCollection(categories)
        self._labels = RasterCollection(labels)

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, rasters):
        self._images = RasterCollection(rasters)

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, categories):
        self._categories = CategoryCollection(categories)

    @property
    def labels(self):
        return self._labels

    @labels.setter
    def labels(self, rasters):
        self._labels = RasterCollection(rasters)

    @classmethod
    def open(cls, filename):
        r"""Load a configuration file, in the ``json`` format.
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
            and not from where the file will be opened.

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

        Args:
            filename (str): Path to the configuration file.

        Returns:
            ConfigDataset

        Examples:
            >>> config = ConfigDataset.open("config.json")
        """

        with open(filename, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Load everything
        root = str(Path(filename).parent)
        images = config.get("images", None)
        categories = config.get("categories", None)
        labels = config.get("labels", None)
        dir_images = retrieve_path(config.get("dir_images", None), root=root)
        dir_categories = retrieve_path(config.get("dir_categories", None), root=root)
        dir_labels = retrieve_path(config.get("dir_labels", None), root=root)
        dir_mosaics = retrieve_path(config.get("dir_mosaics", None), root=root)
        dir_tiles = retrieve_path(config.get("dir_tiles", None), root=root)

        def load_rasters(data=None, in_dir=None):
            r"""Load raster (images / labels) from the configuration file.
            Priority will be given to list of paths.

            Args:
                data (list, optional): List of dictionary ``{"file": "path/to/raster"}``,
                    from the configuration. Defaults to None.
                in_dir (str, optional): Path of the directory containing the rasters.
                    If the path is relative, it should be relative to the configuration file
                    and not to the ``Dataset`` object. Defaults to None.

            Returns:
                list: List of loaded rasters.
            """
            rasters = []
            # Load rasters if provided from a list of dict.
            if data:
                in_dir = in_dir or root
                for raster_info in data:
                    raster_path = retrieve_path(raster_info["filename"], root=in_dir)
                    rasters.append(Raster.open(raster_path))
            # Else, load all rasters from a directory.
            elif Path(in_dir).exists():
                for raster_path in Path(in_dir).iterdir():
                    rasters.append(Raster.open(raster_path))
            return rasters

        def load_categories(data=None, in_dir=None):
            r"""Load categories from the configuration file.
            Priority will be given to list of paths.

            Args:
                data (list, optional): List of dictionary ``{"file": "path/to/category", "name": "name_of_geometry", "color": "blue"}``,
                    from the configuration. Defaults to None.
                in_dir (str, optional): Path of the directory containing the categories.
                    If the path is relative, it should be relative to the configuration file
                    and not to the ``Dataset`` object. Defaults to None.

            Returns:
                list: List of loaded categories.
            """
            categories = []
            # Load categories if provided from a list of dict.
            if data:
                in_dir = in_dir or root
                for category_info in data:
                    color = category_info.get("color", None)
                    name = category_info.get("name", None)
                    category_path = retrieve_path(category_info["filename"], root=in_dir)
                    categories.append(Category.open(category_path, name=name, color=color))
            # Else, load all categories from a directory.
            elif Path(in_dir).exists():
                for category_path in Path(in_dir).iterdir():
                    categories.append(Category.open(category_path))
            return categories

        # Load the different objects either from a directory or list of paths.
        images = load_rasters(data=images, in_dir=dir_images)
        labels = load_rasters(data=labels, in_dir=dir_labels)
        categories = load_categories(data=categories, in_dir=dir_categories)

        return ConfigDataset(images=images, categories=categories, labels=labels,
                             dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
                             dir_mosaics=dir_mosaics, dir_tiles=dir_tiles)

    def to_dict(self, root=None, list_only=False):
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
            >>> config = ConfigDataset.open("../config.json")
            >>> data = config.to_dict(root="some/other/directory")
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
                    "color": category.color,
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
        # Add keys only if they are not empty.
        if not list_only:
            for key, value in self.__dict__.items():
                if value and key[:3] == "dir":
                    config[key] = relative_path(value, root=root)
            # Add images and categories, optionally
            if self.images:
                config["images"] = jsonify_rasters(self.images, self.dir_images)
            if self.categories:
                config["categories"] = jsonify_categories(self.categories, self.dir_categories)
            if self.labels:
                config["labels"] = jsonify_rasters(self.labels, self.dir_labels)
        else:
            config["images"] = jsonify_rasters(self.images, root)
            config["categories"] = jsonify_categories(self.categories, root)
            config["labels"] = jsonify_rasters(self.labels, root)
        return config

    def save(self, filename=None, **kwargs):
        r"""Save the information in a configuration file.

        Args:
            filename (str): Name of the configuration file to be saved.
            kwargs (dict): Other arguments from ``ConfigDataset.to_dict()`` method.

        Examples:
            >>> config = ConfigDataset.open("../config.json")
            >>> config.save("some/other/directory/config.json")
        """
        filename = filename or self.filename
        root = str(Path(filename).parent)

        config = self.to_dict(root=root, **kwargs)
        # If a previous configuration file exists, load it and overwrite only the items that changed.
        if Path(filename).exists():
            with open(filename, "r") as f:
                prev_config = json.load(f)
                prev_config.update(config)
                config = prev_config

        # Save and update the configuration file.
        with open(filename, "w") as f:
            json.dump(config, f, indent=4)
