# Encoding: UTF-8
# File: object_detection.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from tqdm import tqdm
from pathlib import Path
import numpy as np
from PIL import Image
import json

# Geolabel Maker
from ._utils import extract_paths
from .functional import extract_categories
from geolabel_maker.vectors import Color
from .annotation import Annotation
from geolabel_maker.utils import relative_path, retrieve_path
from ._utils import find_paths, find_colors


class ObjectDetection(Annotation):

    def __init__(self, images, categories, annotations, info=None):
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

    # TODO: build method is similar to COCO: re-factorize everything.
    @classmethod
    def build(cls, images=None, categories=None, labels=None,
              dir_images=None, dir_labels=None, colors=None,
              pattern="*.*", root=None, is_crowd=False, **kwargs):
        r"""Generate object detection annotations from a couples of images and labels.

        Args:
            dataset (Dataset): The dataset containing the images and categories.
            zoom (int, optional): Zoom level used to generate the annotations.
            is_crowd (bool, optional): Defaults to ``False``.

        Returns:
            ObjectDetection: Build annotations.
        """
        images_paths = find_paths(files=images, in_dir=dir_images, pattern=pattern)
        labels_paths = find_paths(files=labels, in_dir=dir_labels, pattern=pattern)
        categories = find_colors(categories=categories, colors=colors)

        def get_annotations():
            # Retrieve the annotations (i.e. geometry / categories)
            detect_annotations = []
            annotation_id = 0
            couple_labels = list(zip(images_paths, labels_paths))
            for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
                label = Image.open(label_path).convert("RGB")
                for category_id, category in enumerate(extract_categories(label, categories, **kwargs)):
                    for _, row in category.data.iterrows():
                        polygon = row.geometry
                        # Get annotation elements
                        x, y, max_x, max_y = polygon.bounds
                        width = max_x - x
                        height = max_y - y
                        bbox = (x, y, width, height)
                        # Make annotation format
                        detect_annotations.append({
                            "iscrowd": int(is_crowd),
                            "image_id": image_id,
                            "image_name": str(image_path),
                            "category_id": category_id,
                            "id": annotation_id,
                            "bbox": list(bbox)
                        })
                        annotation_id += 1
            return detect_annotations

        def get_categories():
            # Create an empty categories' dictionary
            detect_categories = []
            for category_id, category in tqdm(enumerate(categories), desc="Build Categories", leave=True, position=0):
                detect_categories.append({
                    "id": category_id,
                    "name": str(category.name),
                    "color": list(category.color),
                    "file_name": str(category.filename)
                })
            return detect_categories

        def get_images():
            # Retrieve image paths / metadata
            detect_images = []
            for image_id, image_path in tqdm(enumerate(images_paths), desc="Build Images", leave=True, position=0):
                image = Image.open(image_path)
                width, height = image.size
                # Create image description
                detect_images.append({
                    "id": image_id,
                    "width": width,
                    "height": height,
                    "file_name": str(image_path)
                })
            return detect_images

        # Create the annotation as a dict
        detect_categories = get_categories()
        detect_images = get_images()
        detect_annotations = get_annotations()

        return ObjectDetection(detect_images, detect_categories, detect_annotations)

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