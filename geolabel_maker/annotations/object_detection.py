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
from datetime import datetime
import json
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
import numpy as np
import random

# Geolabel Maker
from geolabel_maker.annotations.functional import extract_categories
from geolabel_maker.vectors import Color
from .annotation import Annotation
from ._utils import extract_paths


class ObjectDetection(Annotation):

    def __init__(self, images, categories, annotations, info=None):
        super().__init__(images, categories, annotations, info=info)

    @classmethod
    def build(cls, images=None, categories=None, labels=None, pattern="*.*", is_crowd=False, **kwargs):

        # Map the categories and their ids
        category2id = {category.name: i for i, category in enumerate(categories)}
        images_paths = extract_paths(images, pattern=pattern)
        labels_paths = extract_paths(labels, pattern=pattern)

        def get_annotations():
            yolo_annotations = []
            annotation_id = 0
            couple_labels = list(zip(images_paths, labels_paths))
            pbar = tqdm(total=len(couple_labels), desc="Build Annotations", leave=True, position=0)
            for image_id, (image_path, label_path) in enumerate(couple_labels):
                for category in extract_categories(label_path, categories, **kwargs):
                    category_id = category2id[category.name]
                    for _, row in category.data.iterrows():
                        polygon = row.geometry
                        # Get annotation elements
                        x, y, max_x, max_y = polygon.bounds
                        width = max_x - x
                        height = max_y - y
                        bbox = (x, y, width, height)
                        area = polygon.area
                        # Make annotation format
                        yolo_annotations.append({
                            "iscrowd": int(is_crowd),
                            "image_id": image_id,
                            "image_name": str(image_path),
                            "category_id": category_id,
                            "id": annotation_id,
                            "bbox": bbox,
                            "area": area,
                        })
                        annotation_id += 1
                pbar.update(1)
            return yolo_annotations

        yolo_annotations = get_annotations()

        return ObjectDetection(yolo_annotations)
