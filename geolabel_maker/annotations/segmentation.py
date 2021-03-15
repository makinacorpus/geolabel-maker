# Encoding: UTF-8
# File: segmentation.py
# Creation: Tuesday December 29th 2020
# Author: arthurdjn
# ------
# Copyright (c) 2020, Makina Corpus


r"""
Create your annotations for segmentation tasks. 
There are two methods you can use:

- :func:`~geolabel_maker.annotations.segmentation.Segmentation.build`: Use masks (i.e. labels) to generate annotations,
- :func:`~geolabel_maker.annotations.segmentation.Segmentation.make`: Use categories to generate annotations.

.. code-block:: python

    from geolabel_maker.annotations import Segmentation
    
    # Generate annotations from mask images
    annotations = Segmentation.build(
        dir_images = "data/mosaics/images/18",
        dir_labels = "data/mosaics/labels/18",
        colors = {"buildings": "#92a9a2", "vegetation": "green"}
    )
    
    # Generate annotations directly from categories
    annotations = Segmentation.make(
        dir_images = "data/mosaics/images/18",
        dir_categories = "data/categories"
    )
"""


# Basic imports
from tqdm import tqdm
from pathlib import Path
import json
from PIL import Image
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection

# Geolabel Maker
from .annotation import Annotation
from .functional import find_categories
from geolabel_maker.vectors import Color
from geolabel_maker.rasters import Raster
from geolabel_maker.utils import retrieve_path
from ._utils import get_paths, get_categories


class Segmentation(Annotation):
    r"""Defines annotations for instance segmentation tasks. 
    It follows the format `Common Object in Context <http://cocodataset.org/>`__ (COCO) used by Microsoft.

    * :attr:`info` (dict, optional): Description of the annotation (metadata).

    * :attr:`images` (list): List of dictionaries containing metadata for the images in context.

    * :attr:`categories` (list): List of dictionaries containing the description of the categories used.

    * :attr:`annotations` (list): List of dictionaries containing the segmentation of an object associated to an image.

    """

    def __init__(self, images=None, categories=None, annotations=None, info=None):
        super().__init__(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def open(cls, filename):
        """Open segmentation annotations. The file must be in the `JSON` format.

        Args:
            filename (str): Name of the file to read.

        Returns:
            Segmentation: Loaded annotations.
            
        Examples:
            >>> annotations = Segmentation.open("segmentation.json")
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

        return Segmentation(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def build_annotations(cls, images=None, categories=None, labels=None, 
                          dir_images=None, dir_labels=None, colors=None, 
                          pattern_image="*", pattern_label="*", is_crowd=True, **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=pattern_image)
        labels_paths = get_paths(files=labels, in_dir=dir_labels, pattern=pattern_label)
        categories = get_categories(categories=categories, colors=colors)

        seg_annotations = []
        annotation_id = 0
        couple_labels = list(zip(images_paths, labels_paths))
        for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
            categories_extracted = find_categories(label_path, categories, **kwargs)
            for category_id, category in enumerate(categories_extracted):
                for _, row in category.data.iterrows():
                    polygon = row.geometry
                    if not isinstance(polygon, (Polygon, MultiPolygon)):
                        continue
                    # Get annotation elements
                    segmentation = np.array(polygon.exterior.coords).flatten().tolist()
                    x_min, y_min, x_max, y_max = polygon.bounds
                    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                    area = polygon.area
                    # Make annotation format
                    seg_annotations.append({
                        "segmentation": [segmentation],
                        "iscrowd": int(is_crowd),
                        "image_id": image_id,
                        "image_name": str(image_path),
                        "category_id": category_id,
                        "id": annotation_id,
                        "bbox": list(bbox),
                        "area": round(area, 2),
                    })
                    annotation_id += 1
        return seg_annotations

    @classmethod
    def make_annotations(cls, images=None, categories=None, 
                         dir_images=None, dir_categories=None, 
                         pattern_image=None, pattern_category=None,
                         is_crowd=True, **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=pattern_image)
        categories = get_categories(categories=categories, dir_categories=dir_categories, pattern=pattern_category)
        
        seg_annotations = []
        annotation_id = 0
        for image_id, image_path in enumerate(tqdm(images_paths, desc="Build Annotations", leave=True, position=0)):
            image = Raster.open(image_path)
            left, bottom, right, top = image.bounds
            height, width = image.data.shape
            for category_id, category in enumerate(categories):
                category_clipped = category.clip((left, bottom, right, top))
                for _, row in category_clipped.data.explode().iterrows():
                    polygon = row.geometry
                    if not isinstance(polygon, (Polygon, MultiPolygon)):
                        continue
                    # Convert the segmentation in image coordinates
                    segmentation = np.array(polygon.exterior.coords)
                    # Set the origin in the upper left corner
                    x = segmentation[:, 0] - left
                    y = top - segmentation[:, 1]
                    # Scale the segmentation to fit image dimensions
                    x *= width / (right - left)
                    y *= height / (top - bottom)
                    segmentation = np.around(np.column_stack((x, y)), decimals=2)
                    polygon = Polygon(segmentation)
                    segmentation = np.array(polygon.exterior.coords).flatten().tolist()
                    x_min, y_min, x_max, y_max = polygon.bounds
                    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                    area = polygon.area
                    # Make annotation format
                    seg_annotations.append({
                        "segmentation": [segmentation],
                        "iscrowd": int(is_crowd),
                        "image_id": image_id,
                        "image_name": str(image_path),
                        "category_id": category_id,
                        "id": annotation_id,
                        "bbox": list(bbox),
                        "area": round(area, 2),
                    })
                    annotation_id += 1
        return seg_annotations

    def save(self, out_file):
        """Save the segmentation annotations.

        Args:
            out_file (str): Name of the annotation file. Available formats are ``json``.

        Examples:
            >>> annotations = Segmentation.build(
            ...     dir_images="data/mosaics/images", 
            ...     dir_labels="data/mosaics/labels", 
            ...     categories=dataset.categories
            ... )
            >>> annotations.save("segmentation.json")
        """
        root = str(Path(out_file).parent)
        with open(out_file, "w") as f:
            json.dump(self.to_dict(root=root), f, indent=4)

    # TODO: change colors to {category_name: color}
    def plot(self, image_id=None, colors=None, plot_bbox=False, plot_name=False, ax=None, figsize=None):
        """Show the superposition of the segmentation map (labels) on an image.

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
            >>> annotations = Segmentation.open("segmentation.json")
            >>> annotations.plot()
        """
        from matplotlib.patches import Polygon
        
        # Create matplotlib axes
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)
            
        category2name = {category["id"]: category["name"] for category in self.categories}
        category2colors = colors or {}
        category2colors = {str(name): Color.get(color).to_hex() for name, color in category2colors.items()}

        # Find masks associated to image_id
        if image_id is None:
            image_id = random.choice([image["id"] for image in self.images])
        image = self.get_image(image_id)
        image = Image.open(image["file_name"]).convert("RGB")
        annotations = self.get_labels(image_id)

        # Plot the image
        width, height = image.size
        ax.imshow(image)

        colors = []
        polygons = []
        bboxes = []
        for annotation in annotations:
            category_name = category2name.get(annotation.get("category_id", None), None)
            if category2colors.get(category_name, None):
                color = category2colors[category_name]
            else:
                color = np.random.random(3) * 0.6 + 0.4
            colors.append(color)

            for segmentation in annotation["segmentation"]:
                polygon = np.array(segmentation).reshape((-1, 2))
                polygons.append(Polygon(polygon))

            if plot_bbox:
                x, y, w, h = annotation["bbox"]
                bbox = [(x, y), (x, y + h), (x + w, y + h), (x + w, y)]
                bbox = np.array(bbox).reshape((4, 2))
                bboxes.append(Polygon(bbox))

            if plot_name:
                x, y, _, _ = annotation["bbox"]
                ax.text(x, y, category_name, fontsize=10, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.4})

        # Add the annotations
        patches = PatchCollection(polygons, facecolor=colors, linewidths=0, alpha=0.4)
        ax.add_collection(patches)
        patches = PatchCollection(polygons, facecolor="none", edgecolors=colors, linewidths=2)
        ax.add_collection(patches)
        patches = PatchCollection(bboxes, facecolor="none", edgecolors=colors, linewidths=2, linestyles="--")
        ax.add_collection(patches)
        # Add a title
        ax.set_title(f"image_id n°{image_id}")
        plt.axis("off")

        return ax
