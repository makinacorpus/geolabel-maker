#!/usr/bin/env python

"Main module"
from pathlib import Path
import begin
import json

from geolabel_maker import rasters
from geolabel_maker import labels
from geolabel_maker import tiles
from geolabel_maker import annotations


@begin.subcommand
def make_labels(dir_img, categories):
    """
    Make the label image from a configuration JSON file.
    :param dir_img: path to the folder containing the images to be labeled
    :param categories: Categories JSON file
    """
    print('MAKE LABELS')
    # Read json file
    with open(categories) as json_file:
        categories_dict = json.load(json_file)

    # List images
    img_path = Path(dir_img)
    rasters = [f for f in img_path.iterdir()]

    # Create the label image associated to the merged raster
    try:
        for raster in rasters:
            output_label = labels.make_label(str(raster), categories_dict)
            print(f'Created label : {output_label}')
    except ValueError:
        print('Please check your configuration file.')


@begin.subcommand
def make_rasters(dir_img):
    """
    Merge all raster images into a single image.
    :param dir_img: Image directory path
    :return the names of the virtual raster files created for images and labels
    """
    print('MAKE VIRTUAL RASTERS')
    # List images and labels files
    images = []
    labels = []
    img_path = Path(dir_img)
    for f in img_path.iterdir():
        if 'label' in f.stem:
            labels.append(str(f))
        else:
            images.append(str(f))

    # Merge raster images
    if len(images) > 0:
        images_vrt = str(img_path / "images.vrt")
        rasters.make_vrt(images, output_file=images_vrt)
        print(f'{len(images)} images are merged in the file {images_vrt}.')
    else:
        raise ValueError(f'Your directory {dir_img} does not contain images.')

    # Merge labels
    if len(labels) > 0:
        labels_vrt = str(img_path / "labels.vrt")
        rasters.make_vrt(labels, output_file=labels_vrt)
        print(f'{len(labels)} labels are merged in the file {labels_vrt}.')
    else:
        raise ValueError(f'Your directory {dir_img} does not contain labels.')

    return images_vrt, labels_vrt


@begin.subcommand
def make_tiles(raster_file, label_file, dir_tiles):
    """
    Split raster and label images into tiles at different zoom levels
    :param raster_file: Raster image file
    :param label_file: Label image file
    :param dir_tiles: Path to the directory where tiles will be registered
    """
    print('MAKE TILES')
    # Get sub-folder names
    dir_imgtiles, dir_labeltiles = tiles.get_tiles_directories(dir_tiles)

    # Create sub-folders
    dir_imgtiles.mkdir(parents=True, exist_ok=True)
    dir_labeltiles.mkdir(parents=True, exist_ok=True)

    # Create image and label tiles
    tiles.create_tiles(raster_file, dir_imgtiles)
    print(f'The image tiles are created in the folder {dir_imgtiles}.')
    tiles.create_tiles(label_file, dir_labeltiles)
    print(f'The label tiles are created in the folder {dir_labeltiles}.')


@begin.subcommand
def make_annotations(dir_tiles, config, zoom='18'):
    """
    Create an annotation JSON file in the COCO format for a specific zoom level
    :param dir_tiles: Tiles directory path
    :param config: Configuration JSON file
    :param zoom: Zoom level (by default it is equal to 18)
    """
    print('MAKE ANNOTATIONS')
    # Read groups file
    with open(config) as json_file:
        config = json.load(json_file)

    # Get sub-folder names
    dir_imgtiles, dir_labeltiles = tiles.get_tiles_directories(dir_tiles)

    dir_imgtiles_zoom = dir_imgtiles / zoom
    dir_labeltiles_zoom = dir_labeltiles / zoom

    # Create the annotation JSON file
    is_crowd = False
    annotations_json = annotations.write_complete_annotations(
        dir_imgtiles_zoom,
        dir_labeltiles_zoom,
        config,
        is_crowd,
        zoom
    )

    print(f'The file {annotations_json} contains your annotations.')


@begin.subcommand
def make_all(img, tiles, categories, zoom='18'):
    """
    Run the full process to get a ground truth in the COCO format :
    1. Make label images
    2. Create virtual raster files to combine images and labels
    3. Split image and label virtual files creating tiles
    4. Create an annotation JSON file in the COCO format
    for a specific zoom level
    ----------
    Parameters
    ----------
    :param img: Image directory path
    :param tiles: Tiles directory path
    :param categories: JSON file path
    :param zoom: Zoom level (by default it is equal to 18)
    """

    # Create the label image associated to the merged raster
    make_labels(img, categories)

    # Merge raster files
    images_vrt, labels_vrt = make_rasters(img)

    # Split image and label into tiles
    make_tiles(images_vrt, labels_vrt, tiles)

    # Create the annotation file
    make_annotations(tiles, categories, zoom)


@begin.start(short_args=True, lexical_order=False)
def main():
    pass
