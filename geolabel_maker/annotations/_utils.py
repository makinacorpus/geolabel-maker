# Encoding: UTF-8
# File: utils.py
# Creation: Sunday February 7th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from tqdm import tqdm
from pathlib import Path
from types import GeneratorType
from PIL import Image
import numpy as np


# Geolabel Maker
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.vectors import Category, CategoryCollection
from .functional import extract_categories


def extract_paths(element, pattern="*.*"):
    paths = []
    if isinstance(element, (str, Path)):
        if Path(element).is_dir():
            paths = list(Path(element).rglob(pattern))
        elif Path(element).is_file():
            paths = [Path(element)]
    elif isinstance(element, (Raster, Category)):
        paths = [Path(element.filename)]
    elif isinstance(element, (RasterCollection, CategoryCollection)):
        paths = [Path(elem.filename) for elem in element]
    elif isinstance(element, (tuple, list, GeneratorType)):
        for elem in element:
            path = extract_paths(elem, pattern=pattern)
            paths.extend(path)
    else:
        raise ValueError(f"Unrecognized type {type(element).__name__}")
    return paths


def find_paths(files=None, in_dir=None, pattern="*"):
    assert files or in_dir, "Files or an input directory must be provided."
    
    # First, retrieve paths from a directory
    if in_dir and Path(in_dir).is_dir():
        return list(Path(in_dir).rglob(pattern))
    
    # Then from a list or collection
    elif files:
        if isinstance(files, (Raster, Category)):
            return [Path(files.filename)]
        elif isinstance(files, (RasterCollection, CategoryCollection)):
            return [Path(data.filename) for data in files]
        elif isinstance(files, (tuple, list, GeneratorType)):
            return files
        else:
            raise ValueError(f"Unrecognized type {type(files).__name__}")


def find_colors(categories=None, colors=None):
    assert categories or colors, "Categories or colors must be provided."
    
    if colors:
        categories = CategoryCollection()
        for name, color in colors.items():
            categories.append(Category(None, name, color=color))
        return categories
    return categories


# TODO: Re-factorize build methods. Not finished.
def get_annotations(images_paths, labels_paths, categories, is_crowd=False, **kwargs):
    # Retrieve the annotations (i.e. geometry / categories)
    coco_annotations = []
    annotation_id = 0
    couple_labels = list(zip(images_paths, labels_paths))
    for image_id, (image_path, label_path) in enumerate(tqdm(couple_labels, desc="Build Annotations", leave=True, position=0)):
        for category_id, category in enumerate(extract_categories(label_path, categories, **kwargs)):
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

def get_categories(categories):
    # Create an empty categories' dictionary
    coco_categories = []
    for category_id, category in tqdm(enumerate(categories), desc="Build Categories", leave=True, position=0):
        coco_categories.append({
            "id": category_id,
            "name": str(category.name),
            "color": list(category.color),
            "file_name": str(category.filename),
            "supercategory": str(category.name)
        })
    return coco_categories

def get_images(images_paths):
    # Retrieve image paths / metadata
    coco_images = []
    for image_id, image_path in tqdm(enumerate(images_paths), desc="Build Images", leave=True, position=0):
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
