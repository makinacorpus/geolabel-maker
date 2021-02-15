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

# Geolabel Maker
from ._utils import extract_paths
from .functional import extract_categories
from geolabel_maker.vectors import Color
from .annotation import Annotation
from geolabel_maker.utils import relative_path


class ObjectDetection(Annotation):

    def __init__(self, images, categories, annotations, info=None):
        super().__init__(images, categories, annotations, info=info)

    @classmethod
    def build(cls, images=None, categories=None, labels=None, pattern="*.*", root=None, is_crowd=False, **kwargs):

        # Map the categories and their ids
        category2id = {category.name: i for i, category in enumerate(categories)}
        images_paths = extract_paths(images, pattern=pattern)
        labels_paths = extract_paths(labels, pattern=pattern)

        def get_annotations():
            # Retrieve the annotations (i.e. geometry / categories)
            detect_annotations = []
            annotation_id = 0
            couple_labels = list(zip(images_paths, labels_paths))
            for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
                for category in extract_categories(label_path, categories, **kwargs):
                    category_id = category2id[category.name]
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
            for category in tqdm(categories, desc="Build Categories", leave=True, position=0):
                category_id = category2id[category.name]
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
            for image_id, image_path in enumerate(tqdm(images_paths, desc="Build Images", leave=True, position=0)):
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
