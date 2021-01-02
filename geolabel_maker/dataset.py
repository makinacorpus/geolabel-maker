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
    
    dataset = Dataset.open("data/")
    dataset.generate_labels()
    dataset.generate_tiles()
    # Extract the geometries per categories
    categories = dataset.extract_categories()
"""

# Basic imports
from shutil import ReadError
from pathlib import Path
from collections import defaultdict
from PIL import Image
import geopandas as gpd
import json
import matplotlib.pyplot as plt

# Geolabel Maker
from geolabel_maker.rasters import to_raster, generate_tiles, make_vrt
from geolabel_maker.vectors import Category
from geolabel_maker.functional import retrieve_masks, find_polygons, generate_label

# Global variables
Image.MAX_IMAGE_PIXELS = 156_250_000


class Dataset:
    """
    A ``Dataset`` is a combination of ``Raster`` and ``Category`` data.

    * :attr:`images` (list): List of images (either of type ``Raster`` of path to the aerial image).

    * :attr:`categories` (list): List of categories (either of type ``Category`` of path to the categories).

    .. note::
        To avoid memory overload, the dataset does not contains the ``Raster`` and ``Category`` data
        directly but their paths.

    """

    def __init__(self, images, categories, root="data"):
        self.images = [to_raster(image) for image in images]
        self.categories = categories
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        self.root = str(root_path)

    @property
    def dir_images(self):
        return str(Path(self.root) / "images")

    @property
    def dir_categories(self):
        return str(Path(self.root) / "categories")

    @property
    def dir_labels(self):
        return str(Path(self.root) / "labels")

    @property
    def dir_tiles(self):
        return str(Path(self.root) / "tiles")

    @property
    def dir_tiles_labels(self):
        return str(Path(self.dir_tiles) / "labels")

    @property
    def dir_tiles_images(self):
        return str(Path(self.dir_tiles) / "images")

    @property
    def labels(self):
        labels = []
        dir_labels = Path(self.dir_labels)
        for label_path in dir_labels.iterdir():
            if "label" in label_path.stem:
                labels.append(to_raster(str(label_path)))
        return labels

    @classmethod
    def open(cls, root):
        r"""Open the dataset from a ``root`` folder. 
        The root folder contains all data needed for cache and computations.
        To open the dataset, this folder must have a ``images`` directory where all georeferenced aerial images are located,
        a ``categories`` directory containing geometries in the same area, 
        and finally a ``categories.json`` file used to index the geometries and their name / color.
        The ``categories.json`` file is a JSON like:

        .. code-block:: python

            {
                "vegetation": {
                    "id": 0,
                    "file": "categories/vegetation.json",
                    "color": [0, 150, 0]
                },
                # etc...
            }

        Args:
            root (str): Path to the root directory.

        Returns:
            Dataset

        Examples:
            >>> dataset = Dataset.open("data/")
        """
        # Load images that are not a label
        dir_images = Path(root) / "images"
        images = []
        for image_path in dir_images.iterdir():
            if not "label" in image_path.stem:
                images.append(str(image_path))

        # Read the categories
        categories_path = Path(root) / "categories.json"
        if not categories_path.is_file():
            raise ReadError("The 'categories.json' file is not found. "
                            "Please create one before loading the dataset.")
        with open(categories_path, "r", encoding="utf-8") as file:
            categories_dict = json.load(file)

        # Load category / geometry file
        categories = []
        for name, category_info in categories_dict.items():
            color = tuple(category_info["color"])
            filename = Path(root) / Path(category_info["file"])
            categories.append(Category.open(filename, name=name, color=color))

        return Dataset(images, categories, root=root)

    def generate_labels(self):
        """Generate labels from the set of ``images`` and ``categories``. 
        The label associated to a image in respect of the categories 
        is a ``.tif`` image containing all geometries 
        within the geographic extents from the origin image.
        The output labels are saved in the directory ``dir_label``. 

        Returns:
            str: Path to the label directory.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.dir_labels
                "data/labels"
            >>> dataset.generate_labels()
            >>> # Labels generated in "data/labels"
        """
        for image in self.images:
            generate_label(image, self.categories, dir_labels=self.dir_labels)
        return self.dir_labels

    def make_vrt(self, make_images=True, make_labels=True):
        r"""Write virtual images from images and/or labels.

        .. note::
            Generate the labels with ``generate_labels()`` method

        Args:
            make_images (bool, optional): If ``True``, generate virtual image for 
                georeferenced images in the ``images`` folder. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate virtual image for 
                georeferenced images in the ``labels`` folder.  
                Defaults to ``True``.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.make_vrt(make_images=True, make_labels=True)
        """
        images_vrt = None
        labels_vrt = None

        # Make virtual images
        if make_images:
            outfile = Path(self.root) / "images.vrt"
            images_vrt = make_vrt(str(outfile), self.images)
        # Make virtual labels
        if make_labels:
            outfile = Path(self.root) / "labels.vrt"
            labels_vrt = make_vrt(str(outfile), self.labels)

        # Return the path to the created files
        if not labels_vrt:
            return images_vrt
        if not images_vrt:
            return labels_vrt
        return images_vrt, labels_vrt

    def generate_tiles(self, make_images=True, make_labels=True, **kwargs):
        r"""Generate tiles from the images and optionally the generated labels.

        .. note::
            Generate the labels with ``generate_labels()`` method

        Args:
            make_images (bool, optional): If ``True``, generate tiles for 
                georeferenced images in the ``images`` folder. 
                Defaults to ``True``.
            make_labels (bool, optional): If ``True``, generate tiles for 
                georeferenced images in the ``labels`` folder.  
                Defaults to ``True``.

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_tiles(make_images=True, make_labels=True, zoom="14-16")
        """
        # Generate tiles from the images
        if make_images:
            print(f"Generating image tiles...")
            images_vrt = self.make_vrt(make_images=True, make_labels=False)
            generate_tiles(images_vrt, self.dir_tiles_images, **kwargs)
        # Generate tiles from the labels
        if make_labels:
            print(f"Generating label tiles...")
            labels_vrt = self.make_vrt(make_images=False, make_labels=True)
            generate_tiles(labels_vrt, self.dir_tiles_labels, **kwargs)

    # TODO: keep additional data from categories (example: a street name)
    def extract_categories(self, zoom, **kwargs):
        r"""Retrieve the polygons for all tile labels.
        This method must be used once the tiles are generated (see ``generate_tiles`` method).

        Args:
            zoom (int, optional): Zoom level where the polygons will be extracted. Defaults to 16.
            **kwargs (optional): See ``geolabel_maker.functional.find_polygons`` method arguments.

        Returns:
            tuple: Tuple of ``Category``. The categories contains a set of geometries 
                (e.g. all buildings from the images at ``zoom`` level).

        Examples:
            >>> dataset = Dataset.open("data/")
            >>> dataset.generate_labels()
            >>> dataset.generate_tiles(zoom="14-16")
            >>> categories = dataset.extract_categories(zoom=15)
        """
        color2id = {tuple(category.color): i for i, category in enumerate(self.categories)}
        categories_dict = defaultdict(list)

        # Load all label (tile) images
        dir_path = Path(self.dir_tiles_labels) / str(zoom)
        # Make sure the tiles exist
        if not dir_path.is_dir():
            raise RuntimeError("The labels were not found. "
                               f"Please try to generate them with `generate_tiles()` method. "
                               f"In addition the tiles must be in {dir_path} directory.")

        for tile_index, tile_file in enumerate(dir_path.rglob("*.png")):
            # Read label image
            tile_label = Image.open(tile_file)
            tile_label = tile_label.convert("RGB")
            # Find all masks / categories
            masks = retrieve_masks(tile_label, self.categories)
            for color, mask in masks.items():
                # Find all polygons within a category
                polygons = find_polygons(mask, **kwargs)
                for polygon in polygons:
                    category_id = int(color2id[color])
                    categories_dict[category_id].append({
                        "image_id": int(tile_index),
                        "image_name": str(tile_file),
                        "geometry": polygon,
                    })

        # Group by categories
        categories = []
        # Sort the generated categories to match the `dataset.categories` order
        for category_id, category_data in sorted(categories_dict.items()):
            name = self.categories[category_id].name
            color = self.categories[category_id].color
            data = gpd.GeoDataFrame(category_data)
            category = Category(name, data, color)
            categories.append(category)

        return tuple(categories)

    def show_images(self, columns=2, save=False, outfile="images.jpg"):
        figure = plt.figure(figsize=(12, 6))

        for i, image in enumerate(self.images):
            image = image.numpy().transpose(1, 2, 0)           
            plt.subplot(int(len(self.images)/columns + 1), columns, i + 1)
            plt.imshow(image)
            plt.axis('off')

        if save:
            plt.savefig(outfile)

        plt.show()
