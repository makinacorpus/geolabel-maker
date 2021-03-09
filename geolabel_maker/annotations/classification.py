# Encoding: UTF-8
# File: classes.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
Create your annotations for classification tasks. 
There are two methods you can use:

- :func:`~geolabel_maker.annotations.classification.Classification.build`: Use masks (i.e. labels) to generate annotations,
- :func:`~geolabel_maker.annotations.classification.Classification.make`: Use categories to generate annotations.

.. code-block:: python

    from geolabel_maker.annotations import Classification
    
    # Generate annotations from mask images
    classif = Classification.build(
        dir_images = "data/mosaics/images/18",
        dir_labels = "data/mosaics/labels/18",
        colors = {"buildings": "#92a9a2", "vegetation": "green"}
    )

    # Generate annotations directly from categories
    classif = Classification.make(
        dir_images = "data/mosaics/images/18",
        dir_categories = "data/categories"
    )
"""


# Basic imports
from tqdm import tqdm
from pathlib import Path
import pandas as pd
from PIL import Image
import json
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from .annotation import Annotation
from geolabel_maker.rasters import Raster
from geolabel_maker.utils import retrieve_path
from ._utils import get_paths, get_categories


class Classification(Annotation):
    r"""Defines annotations for classification tasks.
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
            image_names = []
            df = pd.read_csv(filename, **kwargs)
            for annotation_id, row in df.iterrows():
                annotation = json.loads(row.to_json())
                image_name = annotation.get("image_name", None)
                image_id = annotation.get("image_id", annotation_id)
                annotation["image_id"] = image_id
                annotation["id"] = annotation.get("id", image_id)
                annotations.append(annotation)

                # Update the set of images
                if not image_name in image_names:
                    image_names.append(image_name)
                    images.append({"id": image_id, "file_name": image_name})

            # Update the categories from the annotations
            category_names = set(df.columns) - {"image_name", "image_id", "id"}
            for category_id, category_name in enumerate(category_names):
                categories.append({"id": category_id, "name": category_name, "supercategory": category_name})

        # Update the paths to the root of execution
        root = Path(filename).parent
        for image in images:
            image["file_name"] = retrieve_path(image.get("file_name", None), root)
        for category in categories:
            category["file_name"] = retrieve_path(category.get("file_name", None), root)
        for annotation in annotations:
            annotation["image_name"] = retrieve_path(annotation.get("image_name", None), root)

        return Classification(images=images, categories=categories, annotations=annotations)

    @classmethod
    def build_annotations(cls, images=None, categories=None, labels=None,
                          dir_images=None, dir_labels=None, colors=None,
                          pattern_image="*", pattern_label="*", **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=pattern_image)
        labels_paths = get_paths(files=labels, in_dir=dir_labels, pattern=pattern_label)
        categories = get_categories(categories=categories, colors=colors)

        classif_annotations = []
        couple_labels = list(zip(images_paths, labels_paths))
        for annotation_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
            annotation = {
                "id": annotation_id,
                "image_name": str(image_path),
                "image_id": annotation_id
            }
            annotation.update({category.name: 0 for category in categories})
            label = Image.open(label_path).convert("RGB")
            width, height = label.size
            label_colors = label.getcolors(width * height)
            for category in categories:
                visible = False
                if tuple(category.color) in label_colors:
                    visible = True
                annotation.update({
                    category.name: int(visible)
                })
            classif_annotations.append(annotation)
        return classif_annotations

    @classmethod
    def make_annotations(cls, images=None, categories=None, 
                         dir_images=None, dir_categories=None, 
                         pattern_image=None, pattern_category=None, **kwargs):
        images_paths = get_paths(files=images, in_dir=dir_images, pattern=pattern_image)
        categories = get_categories(categories=categories, dir_categories=dir_categories, pattern=pattern_category)
        
        classif_annotations = []
        for annotation_id, image_path in enumerate(tqdm(images_paths, desc="Build Annotations", leave=True, position=0)):
            image = Raster.open(image_path)
            left, bottom, right, top = image.bounds
            annotation = {
                "id": annotation_id,
                "image_name": str(image_path),
                "image_id": annotation_id
            }
            for category in categories:
                category_clipped = category.clip((left, bottom, right, top))
                visible = False
                if not category_clipped.data.empty:
                    visible = True
                annotation.update({
                    category.name: int(visible)
                })
            classif_annotations.append(annotation)
        return classif_annotations

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
            df = df.drop(columns=["id"])
            df.index.name = "id"
            df.to_csv(out_file, **kwargs)

    def plot(self, axes=None, figsize=None, image_id=None):
        """Show the labels associated to an image.

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
            >>> annotations = ObjectDetection.open("objects.json")
            >>> annotations.plot()
        """
        # Find masks associated to image_id
        if image_id is None:
            image_id = random.choice([image["id"] for image in self.images])
            
        image = self.get_image(image_id)
        image = Image.open(image["file_name"]).convert("RGB")
        # Keep only categories information
        labels = self.get_labels(image_id)[0]
        labels.pop("image_name", None)
        labels.pop("image_id", None)
        labels.pop("id", None)

        # Create matplotlib axes
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)

        axes.imshow(image)

        # Add the legend
        handles = [mpatches.Patch(facecolor="none", label=f"{category_name}: {bool(is_visible)}") for category_name, is_visible in labels.items()]
        axes.legend(loc=1, handles=handles, frameon=True)

        plt.title(f"image_id n°{image_id}")
        plt.axis("off")
        return axes
