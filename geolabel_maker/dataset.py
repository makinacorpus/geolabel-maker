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
import logging
import json
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np
import rasterio
import rasterio.mask

# Geolabel Maker
from geolabel_maker.rasters import Raster, RasterCollection, generate_tiles, generate_vrt
from geolabel_maker.rasters import utils
from geolabel_maker.vectors import Category, CategoryCollection
from geolabel_maker.utils import retrieve_path
from geolabel_maker.logger import setup_logger


# Global variables
Image.MAX_IMAGE_PIXELS = 156_250_000


class Dataset:
    r"""
    A ``Dataset`` is a combination of ``Raster`` and ``Category`` data.

    * :attr:`images` (list): List of images (either of type ``Raster`` of path to the aerial image).

    * :attr:`labels` (list): List of label images (either of type ``Raster`` of path to the label image).

    * :attr:`categories` (list): List of categories (either of type ``Category`` of path to the categories).

    * :attr:`filename` (str): Name of the configuration file associated to the dataset.

    * :attr:`root` (str): Path to the root folder, containing logs, cache and generated labels.

    """

    def __init__(self, images, categories, labels=None, filename=None, root=None):

        # Find root / filename if partially provided
        if not filename and not root:
            filename = "config.json"
            root = "."
        elif not filename:
            filename = Path(root) / "config.json"
        elif not root:
            root = Path(filename).parent
        self.root = str(root)
        self.filename = str(filename)

        self._images = RasterCollection(images)
        self._categories = CategoryCollection(categories)
        self._labels = RasterCollection(labels)
        # Save the configuration file
        self.save()

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
    def open(cls, config):
        r"""Open a ``Dataset`` from a configuration file. The file must be in ``json`` format.
        This file should be associated to a set of images and categories.
        Provide the ``images``, ``categories`` and ``labels`` you want to load from directories with:

        .. code-block:: json

            {
                "dir_images":  "images",
                "dir_categories":  "categories",
                "dir_labels":  "labels"
            }

        .. warning:: 
            If the path is relative, it should be relative to the configuration file
            and not to the ``Dataset`` object.

        Alternatively, you can specify manually the path to each elements with:

        .. code-block:: json

            {
                "images":  [{
                    "filename": "path/to/raster.tif"
                }], 
                "categories":  [{
                    "filename": "path/to/buildings.json",
                    "name": "buildings",
                    "color": "white"
                }],
                "labels":  [{
                    "filename": "path/to/raster.tif"
                }]
            }

        .. note::
            You can mix both format. 
            Priority will be given to list of elements.

        You can also load data from a ``root`` folder. 
        The root folder contains all data needed for cache and computations.
        To open the dataset, this folder must have a ``images`` directory where all georeferenced aerial images are located
        and a ``categories`` directory containing geometries in the same area.

        The ``data/`` directory should follow the tree structure:

        .. code-block:: python

            data
            ├── categories
            │   ├── buildings.json
            │   ├── ...
            │   └── vegetation.json
            └── images
                ├── 1843_5174_08_CC46.tif
                ├── ...
                └── 1844_5173_08_CC46.tif   

        Args:
            filename (str): Path to the configuration file e.g. ``config.json``.

        Returns:
            Dataset

        Examples:
            >>> # Load from directories
            >>> config = {
            ...     "dir_images":  "images",
            ...     "dir_categories":  "categories",
            ...     "dir_labels":  "labels"
            ... }
            >>> dataset = Dataset.open(config)
            >>> # Specify some paths
            >>> config = {
            ...    "images":  [{
            ...        "filename": "path/to/raster.tif"
            ...    }], 
            ...    "categories":  [{
            ...        "filename": "path/to/buildings.json",
            ...        "name": "buildings",
            ...        "color": "white"
            ...    }],
            ...    "labels":  [{
            ...        "filename": "path/to/raster.tif"
            ...    }]
            ... }
            >>> dataset = Dataset.open(config)
            >>> # Load directly from a configuration file
            >>> dataset = Dataset.open("config.json")
            >>> # Load from a root folder
            >>> dataset = Dataset.open("data")
        """
        if isinstance(config, (str, Path)):
            # Load from a root directory
            if Path(config).is_dir():
                root = config
                filename = Path(root) / "config.json"
                # Create a default configuration file if it does not exist.
                if not filename.exists():
                    with open(filename, "w") as f:
                        json.dump({
                            "dir_images": "images",
                            "dir_categories": "categories",
                            "dir_labels": "labels"
                        }, f, indent=4)
            # Load from the path to a configuration file
            else:
                filename = config
                root = str(Path(filename).parent)

            # Load the configuration file
            with open(filename, "r", encoding="utf-8") as f:
                config = json.load(f)

        # Load directly from a config dictionary
        elif isinstance(config, dict):
            filename = "config.json"
            root = "."
        else:
            raise ValueError(f"Could not open a `Dataset` from unknown type {type(config)}")

        images = config.get("images", None)
        categories = config.get("categories", None)
        labels = config.get("labels", None)
        dir_images = retrieve_path(config.get("dir_images", None), root=root)
        dir_categories = retrieve_path(config.get("dir_categories", None), root=root)
        dir_labels = retrieve_path(config.get("dir_labels", None), root=root)

        def load_rasters(data=None, indir=None):
            r"""Load raster (images / labels) from the configuration file.
            Priority will be given to list of paths.

            Args:
                data (list, optional): List of dictionary ``{"file": "path/to/raster"}``,
                    from the configuration. Defaults to None.
                indir (str, optional): Path of the directory containing the rasters. 
                    If the path is relative, it should be relative to the configuration file
                    and not to the ``Dataset`` object. Defaults to None.

            Returns:
                list: List of loaded rasters.
            """
            rasters = []
            # Load rasters if provided from a list of dict.
            if data:
                for raster_info in data:
                    raster_path = retrieve_path(raster_info["filename"], root=root)
                    rasters.append(Raster.open(raster_path))
            # Load all rasters in a directory.
            elif indir and Path(indir).exists():
                for raster_path in Path(indir).iterdir():
                    rasters.append(Raster.open(raster_path))
            return rasters

        def load_categories(data=None, indir=None):
            r"""Load categories from the configuration file.
            Priority will be given to list of paths.

            Args:
                data (list, optional): List of dictionary ``{"file": "path/to/category", "name": "name_of_geometry", "color": "blue"}``,
                    from the configuration. Defaults to None.
                indir (str, optional): Path of the directory containing the categories. 
                    If the path is relative, it should be relative to the configuration file
                    and not to the ``Dataset`` object. Defaults to None.

            Returns:
                list: List of loaded categories.
            """
            categories = []
            # Load categories if provided from a list of dict.
            if data:
                for category_info in data:
                    color = category_info.get("color", None)
                    name = category_info.get("name", None)
                    category_path = retrieve_path(category_info["filename"], root=root)
                    categories.append(Category.open(category_path, name=name, color=color))
            # Load all categories in a directory.
            elif indir and Path(indir).exists():
                for category_path in Path(indir).iterdir():
                    categories.append(Category.open(category_path))
            return categories

        # Load the different objects either from a directory or list of paths.
        images = load_rasters(data=images, indir=dir_images)
        labels = load_rasters(data=labels, indir=dir_labels)
        categories = load_categories(data=categories, indir=dir_categories)

        return Dataset(images, categories, labels=labels, filename=filename, root=root)

    def to_dict(self):
        r"""Convert the dataset to a dictionary.
        The dictionary is similar to a configuration file, 
        excepts it does not contains directory information.

        Examples:
            >>> dataset = Dataset.open("data")
            >>> config = dataset.to_dict()
        """

        def jsonify_categories(values):
            categories = []
            for id, category in enumerate(values):
                filename = category.filename
                if not Path(filename).is_absolute():
                    filename = Path(filename).relative_to(self.root)
                categories.append({
                    "id": id,
                    "name": category.name,
                    "color": category.color,
                    "filename": str(filename)
                })

            return categories

        def jsonify_rasters(values):
            rasters = []
            for id, raster in enumerate(values):
                filename = raster.filename
                if not Path(filename).is_absolute():
                    filename = Path(filename).relative_to(self.root)
                rasters.append({
                    "id": id,
                    "filename": str(filename)
                })

            return rasters

        config = {}
        # Add keys only if they are not empty.
        if self.images:
            config["images"] = jsonify_rasters(self.images)
        if self.categories:
            config["categories"] = jsonify_categories(self.categories)
        if self.labels:
            config["labels"] = jsonify_rasters(self.labels)
        return config

    def save(self):
        r"""Save the information in a configuration file.
        If a previous configuration file already exists, it will only overwrite the elements that have changed.

        Examples:
            >>> dataset = Dataset.open("data")
            >>> dataset.labels
                []
            >>> dataset.generate_labels()
            >>> dataset.save()
            >>> # Now, the configuration file contains the list of generated labels.
            >>> dataset = Dataset.open("data")
            >>> dataset.labels
                [Raster(...), Raster(...), ...]
        """
        config = self.to_dict()
        # If the configuration file already exists, load it and update it.
        if Path(self.filename).exists():
            with open(self.filename, "r") as f:
                prev_config = json.load(f)
            # Update the images / categories / labels
            prev_config.update(config)
            config = prev_config

        # Save and update the configuration file.
        with open(self.filename, "w") as f:
            json.dump(config, f, indent=4)

    def generate_label(self, image_idx, outdir=None):
        r"""Extract the categories visible in one image's extent. 
        This method will saved the extracted geometries as a raster image.

        Args:
            image_idx (int): Image index used to generate the labels. 
            outdir (str, optional): Output directory where the file will be saved. 
                If ``None``, the file will be saved in ``"{root}/labels"``.
                Default to ``None``.

        Returns:
            str: Path to the created label image

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_label(0)
        """
        image = self.images[image_idx]
        img_list = []
        out_transform = None
        for category in self.categories:
            # Match the category to the raster extends
            category_cropped = category.crop_raster(image)
            # If the category contains vectors in the cropped area
            if not category_cropped.data.empty:
                # Create a raster from the geometries
                out_image, out_transform = rasterio.mask.mask(
                    image.data,
                    list(category_cropped.data.geometry),
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
        label_array = np.rollaxis(np.array(label_image), -1, 0)

        # Update the profile before saving the tif
        # See the list of options and effects: https://gdal.org/drivers/raster/gtiff.html#creation-options
        # NOTE: the profile should be divided into windows 256x256, we keep it for the labels
        out_profile = image.data.profile
        out_profile.update({
            "driver": "GTiff",
            "height": label_array.shape[1],  # numpy.array.shape[1] or PIL.Image.size[1],
            "width": label_array.shape[2],   # numpy.array.shape[2] or PIL.Image.size[0],
            "count": 3,
            "transform": out_transform,
            "photometric": "RGB"
        })

        # Generate filename "raster-label.tif"
        raster_path = Path(image.data.name)
        out_name = f"{raster_path.stem}-label.tif"
        # Create the output directory if it does not exists
        outdir = outdir or Path(self.root) / "labels"
        Path(outdir).mkdir(parents=True, exist_ok=True)
        out_path = Path(outdir) / out_name

        # Write the `tif` image
        with rasterio.open(out_path, 'w', **out_profile) as dst:
            dst.write(label_array.astype("uint8"))

        return out_path

    def generate_labels(self, outdir=None):
        r"""Generate labels from a set of ``images`` and ``categories``. 
        The label associated to an image in respect of the categories 
        is a ``.tif`` image containing all geometries 
        within the geographic extents from the origin image.
        The output labels are saved in the directory ``outdir``. 

        .. note::
            This method will load the raster labels created dynamically.
            Access them through the ``Dataset.labels`` attribute.

        Args:
            outdir (str, optional): Output directory where the file will be saved. 
                If ``None``, the file will be saved in ``"{root}/labels"``.
                Default to ``None``.

        Returns:
            str: Path to the directory containing the created ``Raster`` label.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> # Labels generated in "data/labels"
        """
        # Initialize/Clean the labels attribute
        self.labels = []
        # Generate and load the labels
        for image_idx, _ in enumerate(self.images):
            label_path = self.generate_label(image_idx, outdir=outdir)
            self.labels.append(Raster.open(label_path))

        return str(outdir)

    def generate_vrt(self, make_images=True, make_labels=True):
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
            outfile = Path(self.root) / "images.vrt"
            images_vrt = generate_vrt(str(outfile), self.images)
        # Make virtual labels
        if make_labels:
            outfile = Path(self.root) / "labels.vrt"
            labels_vrt = generate_vrt(str(outfile), self.labels)

        # Return the path to the created files
        if not labels_vrt:
            return images_vrt
        if not images_vrt:
            return labels_vrt
        return images_vrt, labels_vrt

    # TODO: write from a VRT image. Currently not supported in rasterio.
    def generate_mosaics(self, outdir=None, make_images=True, make_labels=True, **kwargs):
        r"""Generate sets of mosaics from the images and labels. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``outdir`` does not exist,
            it will be created.

        .. seealso::
            Generate the labels with ``geolabel_maker.Dataset.generate_labels`` method.

        Args:
            make_images (bool, optional): If ``True``, generate a mosaic for georeferenced images. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate a mosaic for georeferenced label images.  
                Defaults to ``True``.
            outdir (str, optional): Output directory where the tiles will be saved. 
                If ``None``, the tiles will be saved in ``"{root}/mosaics"``, where ``root`` reference the root dataset.
                The label mosaic will be saved under ``"{outdir}/labels"``,
                and the image mosaic under ``"{outdir}/images"``.
                Default to ``None``.
            kwargs (dict): Remaining arguments from ``Raster.generate_mosaic`` method.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_mosaic(make_images=True, make_labels=True)
        """
        dir_mosaics = outdir or Path(self.root) / "mosaics"
        # Generate mosaic from the images
        if make_images:
            print(f"Generating image mosaic...")
            outdir = Path(dir_mosaics) / "images"
            outdir.mkdir(parents=True, exist_ok=True)
            # TODO: Generate from a VRT
            for image in self.images:
                image.generate_mosaic(outdir=outdir, **kwargs)
        # Generate mosaic from the labels
        if make_labels:
            print(f"Generating label mosaic...")
            outdir = Path(dir_mosaics) / "labels"
            outdir.mkdir(parents=True, exist_ok=True)
            # TODO: Generate from a VRT
            for label in self.labels:
                label.generate_mosaic(outdir=outdir, **kwargs)

        return str(dir_mosaics)

    def generate_tiles(self, outdir=None, make_images=True, make_labels=True, **kwargs):
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
            outdir (str, optional): Output directory where the tiles will be saved. 
                If ``None``, the tiles will be saved in ``"{root}/tiles"``, where ``root`` reference the root dataset.
                The label tiles will be saved under ``"{outdir}/labels"``,
                and the image tiles under ``"{outdir}/images"``.
                Default to ``None``.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_tiles(make_images=True, make_labels=True, zoom="14-16")
        """
        dir_tiles = outdir or Path(self.root) / "tiles"
        # Generate tiles from the images
        if make_images:
            print(f"Generating image tiles at {str(Path(dir_tiles) / 'images')}")
            images_vrt = self.generate_vrt(make_images=True, make_labels=False)
            outdir_images = Path(dir_tiles) / "images"
            outdir_images.mkdir(parents=True, exist_ok=True)
            generate_tiles(images_vrt, outdir_images, **kwargs)
        # Generate tiles from the labels
        if make_labels:
            print(f"Generating label tiles at {str(Path(dir_tiles) / 'labels')}")
            labels_vrt = self.generate_vrt(make_images=False, make_labels=True)
            outdir_labels = Path(dir_tiles) / "labels"
            outdir_labels.mkdir(parents=True, exist_ok=True)
            generate_tiles(labels_vrt, outdir_labels, **kwargs)

        return str(dir_tiles)

    def __repr__(self):
        rep = f"Dataset("
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
