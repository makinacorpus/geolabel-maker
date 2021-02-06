# Encoding: UTF-8
# File: object_detection.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np

# Geolabel Maker
from geolabel_maker.rasters import Raster


class ObjectDetection:

    def __init__(self, annotations):
        self.annotations = annotations

    @classmethod
    def build(cls, dir_images, categories, pattern="*.*"):
        annotations = []
        annotation_id = 0
        for image_id, image_path in enumerate(dir_images.rglob(pattern)):
            # Check if the category is part of the image
            raster = Raster.open(image_path)
            for category_id, category in enumerate(categories):
                category_cropped = category.crop_raster(raster)
                for i, row in category_cropped.data.iterrows():
                    polygon = row.geometry
                    annotation = {
                        "image_id": image_id,
                        "image_name": image_path,
                        "bbox": polygon.bounds,
                        "category_id": category_id,
                        "id": annotation_id
                    }
                    annotation_id += 1
                    annotations.append(annotation)
        return ObjectDetection(annotations)


