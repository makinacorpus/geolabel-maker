# Encoding: UTF-8
# File: classes.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from tqdm import tqdm
from pathlib import Path
import pandas as pd
from PIL import Image
import json

# Geolabel Maker
from .functional import has_color
from .annotation import Annotation
from geolabel_maker.utils import retrieve_path
from ._utils import find_paths, find_colors


class Classification(Annotation):
    r"""Defines an annotation for classification tasks.
    For classification tasks, annotations tells if a category is visible in an image.

    * :attr:`info` (dict, optional): Description of the annotation (metadata).

    * :attr:`images` (list): List of dictionaries containing metadata for the images in context.

    * :attr:`categories` (list): List of dictionaries containing the description of the categories used.

    * :attr:`annotations` (list): List of dictionaries indicating if a category is visible in an image.

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
        categories = []
        images = []
        extension = Path(filename).suffix.lower()
        # Open from a JSON file
        if extension in [".json"]:
            with open(filename) as f:
                data = json.load(f)
                images = data.get("images", None)
                categories = data.get("categories", None)
                annotations = data.get("annotations", None)
        # Open from csv, txt etc.
        else:
            images_paths = []
            df = pd.read_csv(filename, **kwargs)
            for annotation_id, row in df.iterrows():
                annotation = json.loads(row.to_json())
                annotations.append(annotation)
                image_name = annotation.get("image_name", None)
                annotation.pop("image_id")
                annotation["id"] = annotation_id
                if not image_name in images_paths:
                    images_paths.append(image_name)

            # Update the images and categories from the annotations
            for image_id, image_path in enumerate(images_paths):
                images.append({"id": image_id, "file_name": image_path})
            for category_id, category_name in enumerate(annotation.keys()):
                categories.append({"id": category_id, "name": category_name})

        # Update the paths
        root = Path(filename).parent
        for image in images:
            image["file_name"] = retrieve_path(image.get("file_name", None), root)
        for category in categories:
            category["file_name"] = retrieve_path(category.get("file_name", None), root)
        for annotation in annotations:
            annotation["image_name"] = retrieve_path(annotation.get("image_name", None), root)

        return Classification(images=images, categories=categories, annotations=annotations)

    @classmethod
    def build(cls, images=None, categories=None, labels=None,
              dir_images=None, dir_labels=None, colors=None,
              pattern="*.*", **kwargs):
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
            for annotation_id, (image_path, label_path) in tqdm(enumerate(couple_labels), desc="Build Annotations", leave=True, position=0):
                annotation = {
                    "image_name": str(image_path),
                    "id": annotation_id
                }
                annotation.update({category.name: 0 for category in categories})
                label_image = Image.open(label_path).convert("RGB")
                for category in categories:
                    visible = False
                    if has_color(label_image, category.color):
                        visible = True
                    annotation.update({
                        category.name: int(visible)
                    })
                class_annotations.append(annotation)
            return class_annotations

        def get_categories():
            class_categories = []
            for category_id, category in tqdm(enumerate(categories), desc="Build Categories", leave=True, position=0):
                class_categories.append({
                    "id": category_id,
                    "name": str(category.name)
                })
            return class_categories

        def get_images():
            class_images = []
            for image_id, image_path in tqdm(enumerate(images_paths), desc="Build Images", leave=True, position=0):
                class_images.append({
                    "id": image_id,
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
