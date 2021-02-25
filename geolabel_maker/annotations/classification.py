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
from .functional import extract_categories
from .annotation import Annotation
from geolabel_maker.utils import relative_path, retrieve_path
from ._utils import find_paths, find_colors


class Classification(Annotation):
    r"""Defines an annotation for classification tasks.
    For classification tasks, annotations tells if a category is visible in an image.

    * :attr:`info` (dict, optional): Description of the annotation (metadata).

    * :attr:`images` (list): List of dictionaries containing metadata for the images in context.

    * :attr:`categories` (list): List of dictionaries containing the description of the categories used.

    * :attr:`annotations` (list): List of dictionaries containing the segmentation of an object associated to an image.

    """

    def __init__(self, images=None, categories=None, annotations=None, info=None):
        super().__init__(images=images, categories=categories, annotations=annotations, info=info)

    @classmethod
    def open(cls, filename, **kwargs):
        """Open a classification annotations.

        Args:
            filename (str): Name of the file to read.

        Returns:
            Classification: Loaded annotations.
            
        Examples:
            >>> annotations = Classification.open("classification.txt")
        """
        annotations = []
        extension = Path(filename).suffix.lower()
        if extension in [".json"]:
            with open(filename) as f:
                annotations = json.load(f)
        else:
            df = pd.read_csv(filename, **kwargs)
            for i, row in df.iterrows():
                annotations.append(json.loads(row.to_json()))
        return Classification(annotations=annotations)

    @classmethod
    def build(cls, images=None, categories=None, labels=None,
              dir_images=None, dir_labels=None, colors=None,
              pattern="*.*", root=None, is_crowd=False, **kwargs):
        r"""Generate classification annotations from couples of images and labels.

        Args:
            dataset (Dataset): The dataset containing the images and categories.
            zoom (int, optional): Zoom level used to generate the annotations.
            is_crowd (bool, optional): Defaults to ``False``.

        Returns:
            Classification: Build annotations.
        """

        images_paths = find_paths(files=images, in_dir=dir_images, pattern=pattern)
        labels_paths = find_paths(files=labels, in_dir=dir_labels, pattern=pattern)
        categories = find_colors(categories=categories, colors=colors)

        def get_annotations():
            class_annotations = []
            couple_labels = list(zip(images_paths, labels_paths))
            for image_path, label_path in tqdm(couple_labels, desc="Build Annotations", leave=True, position=0):
                annotation = {
                    "image_name": str(image_path)
                }
                annotation.update({category.name: 0 for category in categories})
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
            for category_id, category in tqdm(enumerate(categories), desc="Build Categories", leave=True, position=0):
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
            for image_id, image_path in tqdm(enumerate(images_paths), desc="Build Images", leave=True, position=0):
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
        """Save the annotations

        Args:
            out_file (str): Name of the annotation file. Available are ``txt``, ``csv`` and ``json``.

        Examples:
            >>> annotations = Classification.build(
            ...     dir_images="data/mosaics/images", 
            ...     dir_labels="data/mosaics/labels", 
            ...     categories=dataset.categories
            ... )
            >>> annotations.save("classification.txt")
        """
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

