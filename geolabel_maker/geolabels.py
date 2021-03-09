# Encoding: UTF-8
# File: __main__.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import begin
from pathlib import Path

# Geolabel Maker
from geolabel_maker.annotations import *
from geolabel_maker import Dataset
from geolabel_maker.logger import logger


def open_dataset(images=None, categories=None, labels=None,
                 dir_images=None, dir_categories=None, dir_labels=None,
                 config=None, root=None):
    try:
        if images is not None and categories is not None:
            return Dataset(images=images, categories=categories, labels=labels)
        elif config:
            return Dataset.open(config)
        elif root:
            return Dataset.from_root(root)
        elif dir_images and dir_categories:
            return Dataset.from_dir(dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels)
    except Exception as error:
        error_msg = f"Could not open the dataset located from configuration '{config}'. " \
                    f"The following error occurred: {error}"    
        logger.critical(error_msg)       
        raise RuntimeError(error_msg)


@begin.subcommand
def download(config):
    try:
        return Dataset.download(config)
    except Exception as error:
        error_msg = f"Could not download data from configuration '{config}'. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)


@begin.subcommand
def make_labels(images=None, categories=None, 
                dir_images=None, dir_categories=None,
                config=None, root=None, out_dir=None):
    dataset = open_dataset(
        images=images, categories=categories, 
        dir_images=dir_images, dir_categories=dir_categories,
        config=config, root=root
    )
    try:
        out_dir = dataset.generate_labels(out_dir)
        logger.info(f"Labels successfully generated at '{out_dir}'.")  
    except Exception as error:
        error_msg = f"Could not generate labels. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)


@begin.subcommand
def make_mosaics(images=None, categories=None, labels=None,
                 dir_images=None, dir_categories=None, dir_labels=None,
                 config=None, root=None, 
                 make_images=True, make_labels=True, zoom=None, out_dir=None):
    dataset = open_dataset(
        images=images, categories=categories, labels=labels,
        dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
        config=config, root=root
    )
    try:
        out_dir = dataset.generate_mosaics(make_images=make_images, make_labels=make_labels, zoom=zoom, out_dir=out_dir)
        logger.info(f"Mosaics successfully generated at '{out_dir}'.")
    except Exception as error:
        error_msg = f"Could not generate mosaics. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    return out_dir

@begin.subcommand
def make_tiles(images=None, categories=None, labels=None,
               dir_images=None, dir_categories=None, dir_labels=None,
               config=None, root=None, 
               make_images=True, make_labels=True, zoom=None, out_dir=None):
    dataset = open_dataset(
        images=images, categories=categories, labels=labels,
        dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
        config=config, root=root
    )
    try:
        out_dir = dataset.generate_tiles(make_images=make_images, make_labels=make_labels, zoom=zoom, out_dir=out_dir)
        logger.info(f"Tiles successfully generated at '{out_dir}'.")
    except Exception as error:
        error_msg = f"Could not generate tiles. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    return out_dir

@begin.subcommand
def build_annotations(images=None, labels=None, categories=None,
                      dir_images=None, dir_labels=None, colors=None,
                      pattern_image="*.*", pattern_label="*.*", is_crowd=True,
                      ann_type="coco", out_file=None):
    try:
        if ann_type.lower() in ["coco", "co"]:
            ann_class = COCO   
        elif ann_type.lower() in ["object_detection", "od"]:
            ann_class = ObjectDetection
        elif ann_type.lower() in ["classification", "cl"]:
            ann_class = Classification
        else:
            logger.critical(f"Annnotation {type} not found. Available annotations are: " \
                            f"'coco' (or 'co'), 'object_detection' (or 'od'), 'classification' (or 'cl').")
        annotation = ann_class.build(
            images=images, labels=labels, categories=categories,
            dir_images=dir_images, dir_labels=dir_labels, colors=colors,
            pattern_image=pattern_image, pattern_label=pattern_label, is_crowd=is_crowd
        )
    except Exception as error:
        error_msg = f"Could not build the annnotations '{type}'. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    try:
        out_file = out_file or f"{ann_type}.json"
        out_file = annotation.save(out_file)
        logger.info(f"Annotations file successfully saved at '{out_file}'.")
    except Exception as error:
        error_msg = f"Could not save the annotations. " \
                    f"The following error occurred: {error}"    
        logger.critical(error_msg)
        raise RuntimeError(error_msg)


@begin.subcommand
def make_annotations(images=None, categories=None,
                     dir_images=None, dir_categories=None,
                     pattern_image="*.*", pattern_label="*.*", is_crowd=True,
                     ann_type="coco", out_file=None):
    try:
        if ann_type.lower() in ["coco", "co"]:
            ann_class = COCO   
        elif ann_type.lower() in ["object_detection", "od"]:
            ann_class = ObjectDetection
        elif ann_type.lower() in ["classification", "cl"]:
            ann_class = Classification
        else:
            logger.critical(f"Annnotation {type} not found. Available annotations are: " \
                            f"'coco' (or 'co'), 'object_detection' (or 'od'), 'classification' (or 'cl').")
        annotation = ann_class.make(
            images=images, categories=categories,
            dir_images=dir_images, dir_categories=dir_categories,
            pattern_image=pattern_image, pattern_label=pattern_label, is_crowd=is_crowd
        )
    except Exception as error:
        error_msg = f"Could not build the annnotations '{type}'. " \
                    f"The following error occurred: {error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    try:
        out_file = out_file or f"{ann_type}.json"
        out_file = annotation.save(out_file)
        logger.info(f"Annotations file successfully saved at '{out_file}'.")
    except Exception as error:
        error_msg = f"Could not save the annotations. " \
                    f"The following error occurred: {error}"    
        logger.critical(error_msg)
        raise RuntimeError(error_msg)


@begin.subcommand
def make_all(config=None, root=None, dir_images=None, dir_categories=None,
             dir_labels=None, dir_mosaics=None, dir_tiles=None,
             make_images=True, make_labels=True, zoom=None,    
             images=None, labels=None, categories=None, colors=None,
             pattern_image="*.*", pattern_label="*.*", is_crowd=True,
             ann_type="coco", out_file=None):

    make_labels(
        images=images, categories=categories, 
        dir_images=dir_images, dir_categories=dir_categories, 
        config=config, root=root, out_dir=dir_labels
    )
    if dir_mosaics:
        out_dir = make_tiles(
            images=images, categories=categories, 
            dir_images=dir_images, dir_categories=dir_categories,
            config=config, root=root, 
            make_images=make_images, make_labels=make_labels,
            zoom=zoom, out_dir=dir_mosaics
        )
    elif dir_tiles:
        out_dir = make_tiles(
            images=images, categories=categories,
            dir_images=dir_images, dir_categories=dir_categories,
            config=config, root=root,
            make_images=make_images, make_labels=make_labels, 
            zoom=zoom, out_dir=dir_tiles
        )
    dir_images = Path(out_dir) / "images" / str(zoom or "original")
    dir_labels = Path(out_dir) / "labels" / str(zoom or "original")
    make_annotations(
        categories=categories,
        dir_images=dir_images, dir_labels=dir_labels, colors=colors,
        pattern_image=pattern_image, pattern_label=pattern_label, is_crowd=is_crowd,
        ann_type=ann_type, out_file=out_file
    )


@begin.start(short_args=True, lexical_order=True)
def main():
    pass
