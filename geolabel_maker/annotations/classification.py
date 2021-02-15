# Encoding: UTF-8
# File: classes.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from copy import deepcopy
from tqdm import tqdm
from pathlib import Path
import pandas as pd
from PIL import Image
import json

# Geolabel Maker
from ._utils import extract_paths
from .functional import extract_categories
from .annotation import Annotation
from geolabel_maker.utils import relative_path, retrieve_path


class Classification(Annotation):

    def __init__(self, images=None, categories=None, annotations=None, info=None):
        super().__init__(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def open(self, filename):
        pass

    @classmethod
    def build(cls, images=None, categories=None, labels=None, pattern="*.*", **kwargs):

        category2id = {category.name: i for i, category in enumerate(categories)}
        images_paths = extract_paths(images, pattern=pattern)
        labels_paths = extract_paths(labels, pattern=pattern)

        def get_annotations():
            class_annotations = []
            couple_labels = list(zip(images_paths, labels_paths))
            for image_path, label_path in tqdm(couple_labels, desc="Build Annotations", leave=True, position=0):
                annotation = {
                    "image_name": str(image_path)
                }
                annotation.update({name: 0 for name in category2id.keys()})
                label_image = Image.open(label_path).convert("RGB")
                label_colors = [stat[1] for stat in label_image.getcolors()]
                for category in categories:
                    visible = False
                    if tuple(category.color) in label_colors:
                        visible = True
                    annotation.update({
                        category.name: int(visible)
                    })
                class_annotations.append(annotation)
            return class_annotations

        def get_categories():
            # Create an empty categories' dictionary
            class_categories = []
            for category in tqdm(categories, desc="Build Categories", leave=True, position=0):
                category_id = category2id[category.name]
                class_categories.append({
                    "id": category_id,
                    "name": str(category.name),
                    "color": list(category.color),
                    "file_name": str(category.filename)
                })
            return class_categories

        def get_images():
            # Retrieve image paths / metadata
            class_images = []
            for image_id, image_path in enumerate(tqdm(images_paths, desc="Build Images", leave=True, position=0)):
                image = Image.open(image_path)
                width, height = image.size
                # Create image description
                class_images.append({
                    "id": image_id,
                    "width": width,
                    "height": height,
                    "file_name": str(image_path)
                })
            return class_images

        # Create the annotation as a dict
        class_images = get_images()
        class_categories = get_categories()
        class_annotations = get_annotations()

        return Classification(images=class_images, categories=class_categories, annotations=class_annotations)

    def save(self, out_file, **kwargs):
        extension = Path(out_file).suffix.lower()
        root = str(Path(out_file).parent)
        data = self.to_dict(root=root)

        # Write to JSON
        if extension in [".json"]:
            with open(out_file, "w") as f:
                json.dump(self.to_dict(root=root), f, indent=4, **kwargs)
        # Multiple formats supported by pandas (csv, zip, etc)
        else:
            df = pd.DataFrame(data["annotations"])
            df.index.name = "image_id"
            df.to_csv(out_file, **kwargs)
