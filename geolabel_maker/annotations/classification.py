# Encoding: UTF-8
# File: classes.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from datetime import datetime
from pathlib import Path
import json
import csv

# Geolabel Maker
from ._utils import extract_paths
from .functional import extract_categories
from .annotation import Annotation
from geolabel_maker.rasters import Raster


class Classification(Annotation):

    def __init__(self, annotations, info=None):
        super().__init__(annotations=annotations, info=info)

    @classmethod
    def build(cls, images=None, categories=None, labels=None, pattern="*.*"):

        category2id = {category.name: i for i, category in enumerate(categories)}
        images_paths = extract_paths(images, pattern=pattern)
        labels_paths = extract_paths(labels, pattern=pattern)

        def get_annotations():
            classif_annotations = []
            couple_labels = list(zip(images_paths, labels_paths))
            for image_id, image_path in enumerate(couple_labels):
                # Check if the category is part of the image
                raster = Raster.open(image_path)
                annotation = {
                    "image_name": image_path
                }
                for category_id, category in enumerate(categories):
                    category_cropped = category.crop_raster(raster)
                    visible = False
                    if not category_cropped.data.empty:
                        visible = True
                    annotation[category.name] = int(visible)
                yolo_annotations.append(annotation)
            return yolo_annotations

        # Create the annotation as a dict
        yolo_annotations = get_annotations()

        return Classification(yolo_annotations)

    def save(self, filename, sep=",", header=True):
        extension = Path(filename).suffix.lower()

        # Write JSON file
        if extension == ".json":
            with open(filename, "w") as f:
                json.dump(self.annotations, f)

        # Write TXT file
        elif extension == ".txt":
            with open(filename, "w") as f:
                # Write the header
                if header:
                    f.write(sep.join(self.annotations[0].keys()))
                for annotation in self.annotations:
                    f.write("\n" + sep.join([str(value) for value in annotation.values()]))

        elif extension == ".csv":
            with open(filename, "w") as f:
                writer = csv.writer(f)
                # Write the header
                if header:
                    writer.writerow([sep.join(self.annotations[0].keys())])
                for annotation in self.annotations:
                    writer.writerow([sep.join(annotation.values())])

        # File not recognized
        else:
            raise ValueError(f"The file {filename} is not recognized. Please provide a valid format ['txt, 'csv', 'json']")
