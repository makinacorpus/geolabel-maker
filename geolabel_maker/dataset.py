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
from geolabel_maker.vectors.category import read_categories
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np
import rasterio
import rasterio.mask

# Geolabel Maker
from geolabel_maker.rasters import Raster, to_raster, generate_tiles, generate_vrt
from geolabel_maker.rasters import utils
from geolabel_maker.vectors import Category
from geolabel_maker.logger import logger


# Global variables
Image.MAX_IMAGE_PIXELS = 156_250_000


class Dataset:
    """
    A ``Dataset`` is a combination of ``Raster`` and ``Category`` data.

    * :attr:`images` (list): List of images (either of type ``Raster`` of path to the aerial image).

    * :attr:`labels` (list): List of label images (either of type ``Raster`` of path to the label image).

    * :attr:`categories` (list): List of categories (either of type ``Category`` of path to the categories).

    * :attr:`root` (str): Path to the root folder, containing logs, cache and generated labels.

    """

    __slots__ = ["root", "images", "categories", "labels"]

    def __init__(self, images, categories, labels=None, root="data"):
        # Create the `root` directory if it does not exist
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        self.root = str(root_path)
        # Load the data / images / categories / labels
        self.categories = self._init_categories(categories)
        self.images = self._init_rasters(images)
        self.labels = self._init_rasters(labels)

    @classmethod
    def open(cls, root, overwrite=True):
        r"""Open the dataset from a ``root`` folder. 
        The root folder contains all data needed for cache and computations.
        To open the dataset, this folder must have a ``images`` directory where all georeferenced aerial images are located,
        a ``categories`` directory containing geometries in the same area, 
        and finally a ``categories.json`` file used to index the geometries and their name / color.
        The ``categories.json`` file is a JSON like:

        .. code-block:: python

            {
                "vegetation": {
                    "file": "categories/vegetation.json",
                },
                # etc...
            }

        The ``data/`` directory should follow the tree structure:

        .. code-block:: python

            data
            ├── categories
            │   ├── buildings.json
            │   ├── ...
            │   └── vegetation.json
            ├── images
            │   ├── 1843_5174_08_CC46.tif
            │   ├── ...
            │   └── 1844_5173_08_CC46.tif   
            └── categories.json

        Args:
            root (str): Path to the root directory.

        Returns:
            Dataset

        Examples:
            >>> dataset = Dataset.open("data/", overwrite=True)
        """
        logger.info(f"Opening the dataset at '{root}'...")
        # Load images that are not a label
        logger.info(f"Loading images at '{Path(root) / 'images'}'.")
        dir_images = Path(root) / "images"
        images = []
        for image_path in dir_images.iterdir():
            if not "label" in image_path.stem:
                images.append(Raster.open(str(image_path)))

        # Load labels
        logger.info(f"Loading labels at '{Path(root) / 'labels'}'.")
        dir_labels = Path(root) / "labels"
        labels = []
        if dir_labels.is_dir():
            for label_path in dir_labels.iterdir():
                if "label" in label_path.stem:
                    labels.append(Raster.open(str(label_path)))

        # Read the categories
        logger.info(f"Loading categories from file '{Path(root) / 'categories.json'}'.")
        categories_path = Path(root) / "categories.json"
        categories = read_categories(categories_path, overwrite=overwrite)

        logger.info(f"Dataset at '{root}' successfully loaded.")
        return Dataset(images, categories, labels=labels, root=root)

    def _init_rasters(self, rasters):
        if rasters is None:
            return []
        elif isinstance(rasters, Raster) or isinstance(rasters, str) or isinstance(rasters, Path):
            return [to_raster(rasters)]
        elif isinstance(rasters, list) or isinstance(rasters, tuple):
            return [to_raster(raster) for raster in rasters]

        raise ValueError(f"Unknown element: Cannot convert the element {type(rasters)} to a `Raster` collection.")

    def _init_categories(self, categories):
        if isinstance(categories, Category):
            return [categories]
        elif isinstance(categories, list) or isinstance(categories, tuple):
            return categories
        elif isinstance(categories, str) or isinstance(categories, Path):
            return read_categories(categories)

        raise ValueError(f"Unknown element: Cannot convert the category {type(categories)} to a `Category` collection.")

    def generate_label(self, image_idx, outdir=None):
        """Extract the categories visible in one image's extent. 
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
        """Generate labels from a set of ``images`` and ``categories``. 
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
            self.labels.append(to_raster(label_path))
        return outdir

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

    def generate_mosaics(self, make_images=True, make_labels=True, outdir=None, **kwargs):
        """Generate sets of mosaics from the images and labels. 
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
        outdir = outdir or Path(self.root) / "mosaics"
        # Generate mosaic from the images
        if make_images:
            print(f"Generating image mosaic...")
            images_vrt = self.generate_vrt(make_images=True, make_labels=False)
            outdir = Path(outdir) / "images"
            outdir.mkdir(parents=True, exist_ok=True)
            raster_vrt = Raster.open(images_vrt)
            raster_vrt.generate_mosaic(outdir=outdir, **kwargs)
        # Generate mosaic from the labels
        if make_labels:
            print(f"Generating label mosaic...")
            labels_vrt = self.generate_vrt(make_images=False, make_labels=True)
            outdir = Path(outdir) / "labels"
            outdir.mkdir(parents=True, exist_ok=True)
            raster_vrt = Raster.open(labels_vrt)
            raster_vrt.generate_mosaic(outdir=outdir, **kwargs)

    def generate_tiles(self, make_images=True, make_labels=True, outdir=None, **kwargs):
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
        outdir = outdir or Path(self.root) / "tiles"
        # Generate tiles from the images
        if make_images:
            print(f"Generating image tiles...")
            images_vrt = self.generate_vrt(make_images=True, make_labels=False)
            outdir_images = Path(outdir) / "images"
            outdir_images.mkdir(parents=True, exist_ok=True)
            generate_tiles(images_vrt, outdir_images, **kwargs)
        # Generate tiles from the labels
        if make_labels:
            print(f"Generating label tiles...")
            labels_vrt = self.generate_vrt(make_images=False, make_labels=True)
            outdir_labels = Path(outdir) / "labels"
            outdir_labels.mkdir(parents=True, exist_ok=True)
            generate_tiles(labels_vrt, outdir_labels, **kwargs)

    def __repr__(self):
        rep = f"Dataset(\n"
        rep += "  images(\n"
        for i, image in enumerate(self.images):
            rep += f"    ({i}): {image}\n"
        rep += "  )\n"
        rep += "  categories(\n"
        for i, category in enumerate(self.categories):
            rep += f"    ({i}): {category}\n"
        rep += "  )\n)"
        return rep
