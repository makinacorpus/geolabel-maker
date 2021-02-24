# Encoding: UTF-8
# File: coco.py
# Creation: Tuesday December 29th 2020
# Author: arthurdjn
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from tqdm import tqdm
from copy import deepcopy
from pathlib import Path
import json
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
import numpy as np
import random

# Geolabel Maker
from .annotation import Annotation
from ._utils import extract_paths
from .functional import extract_categories
from geolabel_maker.vectors import Color
from geolabel_maker.utils import relative_path, retrieve_path


class COCO(Annotation):
    r"""Defines an annotation for `Common Object in Context <http://cocodataset.org/>`__. 
    It follows the format used by Microsoft for `COCO` annotations.

    * :attr:`info` (dict, optional): Description of the annotation (metadata).

    * :attr:`images` (list): List of dictionaries containing metadata for the images in context.

    * :attr:`categories` (list): List of dictionaries containing the description of the categories used.

    * :attr:`annotations` (list): List of dictionaries containing the segmentation of an object associated to an image.

    """

    def __init__(self, images=None, categories=None, annotations=None, info=None):
        super().__init__(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def open(cls, filename):
        """Open ``COCO`` annotations. The file must be in the `JSON` format.

        Args:
            filename (str): Name of the file to read.

        Returns:
            COCO
            
        Examples:
            >>> annotations = COCO.open("coco.json")
        """
        with open(filename, "r") as f:
            data = json.load(f)
        images = data.get("images", None)
        categories = data.get("categories", None)
        annotations = data.get("annotations", None)
        info = data.get("info", None)

        root = Path(filename).parent
        for image in images:
            image["file_name"] = retrieve_path(image["file_name"], root)
        for category in categories:
            category["file_name"] = retrieve_path(category["file_name"], root)
        for annotation in annotations:
            annotation["image_name"] = retrieve_path(annotation["image_name"], root)

        return COCO(images=images, categories=categories, annotations=annotations, info=info)

    # TODO: change args images: add dir_images (to be more clear)
    # TODO: add requirements images or dir_images / categories or dir_categories
    @classmethod
    def build(cls, images=None, categories=None, labels=None,
              pattern="*.*", root=None, is_crowd=False, **kwargs):
        r"""Generate a ``COCO`` annotation from a ``Dataset``.

        .. seealso::
            The provided dataset must contains a set of georeferenced images and categories (vectorized geometries).
            See ``Dataset`` for further details.

        Args:
            dataset (Dataset): The dataset containing the images and categories.
            zoom (int, optional): Zoom level used to generate the annotations.
            is_crowd (bool, optional): Defaults to ``False``.

        Returns:
            COCO
        """
        # Map the categories and their ids
        category2id = {category.name: i for i, category in enumerate(categories)}
        images_paths = extract_paths(images, pattern=pattern)
        labels_paths = extract_paths(labels, pattern=pattern)

        # TODO: Remove get_ functions outside as it is redundant with other annotations 
        # TODO: Put them as functions in _utils.py
        def get_annotations():
            # Retrieve the annotations (i.e. geometry / categories)
            coco_annotations = []
            annotation_id = 0
            couple_labels = list(zip(images_paths, labels_paths))
            for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
                for category in extract_categories(label_path, categories, **kwargs):
                    category_id = category2id[category.name]
                    for _, row in category.data.iterrows():
                        polygon = row.geometry
                        # Get annotation elements
                        segmentation = np.array(polygon.exterior.coords).ravel().tolist()
                        x, y, max_x, max_y = polygon.bounds
                        width = max_x - x
                        height = max_y - y
                        bbox = (x, y, width, height)
                        area = polygon.area
                        # Make annotation format
                        coco_annotations.append({
                            "segmentation": [segmentation],
                            "iscrowd": int(is_crowd),
                            "image_id": image_id,
                            "image_name": str(image_path),
                            "category_id": category_id,
                            "id": annotation_id,
                            "bbox": list(bbox),
                            "area": float(area),
                        })
                        annotation_id += 1
            return coco_annotations

        def get_categories():
            # Create an empty categories' dictionary
            coco_categories = []
            for category in tqdm(categories, desc="Build Categories", leave=True, position=0):
                category_id = category2id[category.name]
                coco_categories.append({
                    "id": category_id,
                    "name": str(category.name),
                    "color": list(category.color),
                    "file_name": str(category.filename),
                    "supercategory": str(category.name)
                })
            return coco_categories

        def get_images():
            # Retrieve image paths / metadata
            coco_images = []
            for image_id, image_path in enumerate(tqdm(images_paths, desc="Build Images", leave=True, position=0)):
                image = Image.open(image_path)
                width, height = image.size
                # Create image description
                coco_images.append({
                    "id": image_id,
                    "width": width,
                    "height": height,
                    "file_name": str(image_path)
                })
            return coco_images

        # Create the annotation as a dict
        coco_images = get_images()
        coco_categories = get_categories()
        coco_annotations = get_annotations()

        return COCO(coco_images, coco_categories, coco_annotations)

    def save(self, out_file):
        """Save the `COCO` annotation in a `JSON` format.

        Args:
            out_file (str): Name of the annotation file.

        Examples:
            >>> annotations = COCO.build(images="data/mosaics/images", labels="data/mosaics/labels", categories=dataset.categories)
            >>> annotations.save("coco.json")
        """
        root = str(Path(out_file).parent)
        with open(out_file, "w") as f:
            json.dump(self.to_dict(root=root), f, indent=4)

    def get_image(self, image_id):
        """Get the image from its id.

        Args:
            image_id (int): ID of the image to be retrieved.

        Returns:
            PIL.Image

        Examples:
            >>> annotations = COCO.open("coco.json")
            >>> image = annotations.get_image(19)
        """
        for image in self.images:
            if image["id"] == image_id:
                return Image.open(image["file_name"]).convert("RGB")
        return None

    def get_masks(self, image_id):
        """Get the list of masks associated to an image.

        Args:
            image_id (int): ID of the image.

        Returns:
            list: List of dictionary containing the segmentation.

        Examples:
            >>> annotations = COCO.open("coco.json")
            >>> masks = annotations.get_masks(19)
        """
        masks = []
        for annotation in self.annotations:
            if annotation["image_id"] == image_id:
                masks.append(annotation)
        return masks

    def show(self, image_id=None, colors=None, blend_percentage=0.7):
        """Show the superposition of the segmentation map (labels) on an image.

        Args:
            image_id (int, optional): ID of the image to be displayed. 
                If ``None``, will display a random image. Defaults to ``None``.
            colors (dict, optional): Dictionary of colors indexed by categories' ID. 
                If ``None``, will display each label in a random color. Defaults to ``None``.
            blend_percentage (float, optional): Blending perecentage. Defaults to 0.7.

        Returns:
            PIL.Image

        Examples:
            >>> annotations = COCO.open("coco.json")
            >>> annotations.show(19)
        """
        # Create a map of colors / categories
        colors = colors or {}
        colors = {int(key): value for key, value in colors.items()}
        for category in self.categories:
            if not category["id"] in colors.keys():
                colors[category["id"]] = Color.random().to_hex()

        # Find masks associated to image_id
        if image_id is None:
            image_id = random.choice([image["id"] for image in self.images])
        image = self.get_image(image_id)
        masks = self.get_masks(image_id)
        for mask in masks:
            image_mask = image.copy()
            draw = ImageDraw.Draw(image)
            segmentation = mask["segmentation"][0]
            x = segmentation[::2]
            y = segmentation[1::2]
            polygon = Polygon(np.column_stack((x, y)))
            color = colors[mask["category_id"]]
            draw.polygon(list(polygon.exterior.coords), fill=color)
            image = Image.blend(image_mask, image, blend_percentage)
        return image

    def __repr__(self):
        return f"COCO(images={len(self.images)}, categories={len(self.categories)}, annotations={len(self.annotations)})"
