# Encoding: UTF-8
# File: object_detection.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
Create your annotations for object detection tasks. 
There are two methods you can use:

- :func:`~geolabel_maker.annotations.object_detection.ObjectDetection.build`: Use masks (i.e. labels) to generate annotations,
- :func:`~geolabel_maker.annotations.object_detection.ObjectDetection.make`: Use categories to generate annotations.

.. code-block:: python

    from geolabel_maker.annotations import ObjectDetection
    
    # Generate annotations from mask images
    objects = ObjectDetection.build(
        dir_images = "data/mosaics/images/18",
        dir_labels = "data/mosaics/labels/18",
        colors = {"buildings": "#92a9a2", "vegetation": "green"}
    )
    
    # Generate annotations directly from categories
    objects = ObjectDetection.make(
        dir_images = "data/mosaics/images/18",
        dir_categories = "data/categories"
    )
"""


# Basic imports
from tqdm import tqdm
from pathlib import Path
import json
from PIL import Image, ImageDraw
from shapely.geometry import box
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from .functional import find_categories
from .annotation import Annotation
from geolabel_maker.rasters import Raster
from geolabel_maker.vectors import Color
from geolabel_maker.utils import retrieve_path
from ._utils import get_paths, get_categories


class ObjectDetection(Annotation):
    r"""Defines annotations for object detection tasks. 

    * :attr:`info` (dict, optional): Description of the annotation (metadata).

    * :attr:`images` (list): List of dictionaries containing metadata for the images in context.

    * :attr:`categories` (list): List of dictionaries containing the description of the categories used.

    * :attr:`annotations` (list): List of dictionaries containing the localization of an object associated to an image.

    """

    def __init__(self, images=None, categories=None, annotations=None, info=None):
        super().__init__(images, categories, annotations, info=info)

    @classmethod
    def open(cls, filename):
        """Open object detection annotations. The file must be in the ``json`` format.

        Args:
            filename (str): Name of the file to read.

        Returns:
            ObjectDetection: Loaded annotations.
            
        Examples:
            >>> annotations = ObjectDetection.open("objects.json")
        """
        with open(filename, "r") as f:
            data = json.load(f)
        images = data.get("images", None)
        categories = data.get("categories", None)
        annotations = data.get("annotations", None)
        info = data.get("info", None)

        root = Path(filename).parent
        for image in images:
            image["file_name"] = retrieve_path(image.get("file_name", None), root)
        for category in categories:
            category["file_name"] = retrieve_path(category.get("file_name", None), root)
        for annotation in annotations:
            annotation["image_name"] = retrieve_path(annotation.get("image_name", None), root)       

        return ObjectDetection(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def build_annotations(cls, images=None, categories=None, labels=None, 
                          dir_images=None, dir_labels=None, colors=None, 
                          pattern="*", is_crowd=True, **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=pattern)
        labels_paths = get_paths(files=labels, in_dir=dir_labels, pattern=pattern)
        categories = get_categories(categories=categories, colors=colors)

        objects_annotations = []
        annotation_id = 0
        couple_labels = list(zip(images_paths, labels_paths))
        for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
            categories_extracted = find_categories(label_path, categories, **kwargs)
            for category_id, category in enumerate(categories_extracted):
                for _, row in category.data.iterrows():
                    polygon = row.geometry
                    # Get annotation elements
                    bbox = polygon.bounds
                    objects_annotations.append({
                        "iscrowd": int(is_crowd),
                        "image_id": image_id,
                        "image_name": str(image_path),
                        "category_id": category_id,
                        "id": annotation_id,
                        "bbox": list(bbox)
                    })
                    annotation_id += 1
        return objects_annotations

    @classmethod
    def make_annotations(cls, images=None, categories=None, 
                         dir_images=None, dir_categories=None, 
                         image_pattern=None, category_pattern=None,
                         is_crowd=True, **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=image_pattern)
        categories = get_categories(categories=categories, dir_categories=dir_categories, pattern=category_pattern)
        
        objects_annotations = []
        annotation_id = 0
        for image_id, image_path in enumerate(tqdm(images_paths, desc="Build Annotations", leave=True, position=0)):
            image = Raster.open(image_path)
            left, bottom, right, top = image.bounds
            height, width = image.data.shape
            for category_id, category in enumerate(categories):
                category_clipped = category.clip((left, bottom, right, top))
                for _, row in category_clipped.data.explode().iterrows():
                    polygon = row.geometry
                    x_min, y_min, x_max, y_max = polygon.bounds
                    bbox = (x_min, x_max, x_max - x_min, y_max - y_min)
                    # Set the origin in the upper left corner
                    x_min = round((x_min - left) * width / (right - left), 2)
                    x_max = round((x_max - left) * width / (right - left), 2)
                    y_min = round((top - y_min) * height / (top - bottom), 2)
                    y_max = round((top - y_max) * height / (top - bottom), 2)
                    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                    # Make annotation format
                    objects_annotations.append({
                        "iscrowd": int(is_crowd),
                        "image_id": image_id,
                        "image_name": str(image_path),
                        "category_id": category_id,
                        "id": annotation_id,
                        "bbox": list(bbox)
                    })
                    annotation_id += 1
        return objects_annotations

    def save(self, out_file):
        """Save the object detection annotations.

        Args:
            out_file (str): Name of the annotation file. Available formats are ``json``.

        Examples:
            >>> annotations = ObjectDetection.build(
            ...     dir_images="data/mosaics/images", 
            ...     dir_labels="data/mosaics/labels", 
            ...     categories=dataset.categories
            ... )
            >>> annotations.save("coco.json")
        """
        root = str(Path(out_file).parent)
        with open(out_file, "w") as f:
            json.dump(self.to_dict(root=root), f, indent=4)
            
    def plot(self, axes=None, figsize=None, image_id=None, colors=None, opacity=0.7):
        """Show the labels associated to an image.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            image_id (int, optional): ID of the image to be displayed. 
                If ``None``, will display a random image. Defaults to ``None``.
            colors (dict, optional): Dictionary of colors indexed by categories' ID. 
                If ``None``, will display each label in a random color. Defaults to ``None``.
            opacity (float, optional): Blending perecentage. Defaults to 0.7.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.

        Examples:
            >>> annotations = ObjectDetection.open("objects.json")
            >>> annotations.plot()
        """
        # Create a map of colors / categories
        category2name = {category["id"]: category["name"] for category in self.categories}
        colors = colors or {}
        colors = {str(name): Color.get(color).to_hex() for name, color in colors.items()}
        for category in self.categories:
            if not category["name"] in colors.keys():
                colors[category["name"]] = Color.random().to_hex()

        # Find masks associated to image_id
        if image_id is None:
            image_id = random.choice([image["id"] for image in self.images])
        image = self.get_image(image_id)
        image = Image.open(image["file_name"]).convert("RGB")
        labels = self.get_labels(image_id)
        
        draw = ImageDraw.Draw(image)
        for label in labels:
            x_min, y_min, width, height = label["bbox"]
            bbox = (x_min, y_min, x_min + width, y_min + height)
            category_id = label["category_id"]
            category_name = category2name[category_id]
            color = colors[category_name]
            draw.line(list(box(*bbox).exterior.coords), fill=color)
            
        # Create matplotlib axes
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
            
        axes.imshow(image)
        
        # Add the legend
        handles = [mpatches.Patch(facecolor=color, label=category_name) for category_name, color in colors.items()]
        axes.legend(loc=1, handles=handles, frameon=True)

        plt.title(f"image_id n°{image_id}")
        plt.axis("off")
        return axes
