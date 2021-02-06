# Encoding: UTF-8
# File: __main__.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import begin

# Geolabel Maker
from geolabel_maker.annotations import *
from geolabel_maker import Dataset
from geolabel_maker.logger import logger


def open_dataset(root="data"):
    try:
        logger.info(f"Loading the dataset at '{root}'")
        dataset = Dataset.open(root)
        logger.info(f"Dataset successfully loaded.")
        return dataset
    except Exception as error:
        logger.error(f"Could not open the dataset located at '{root}'. The following error occurred: {error}")
        quit()


@begin.subcommand
def download():
    pass


@begin.subcommand
def make_labels(root="data"):
    logger.info("MAKE LABELS")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the labels
    try:
        labels_path = dataset.generate_labels()
    except Exception as error:
        logger.error(f"Could not generate the labels. The following error occurred: {error}")
        quit()


@begin.subcommand
def make_tiles(root="data", make_images=True, make_labels=True, zoom="13-20"):
    logger.info("MAKE TILES")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the tiles
    try:
        dataset.generate_tiles(make_images=make_images, make_labels=make_labels, zoom=zoom)
    except Exception as error:
        logger.error(f"Could not generate the labels. The following error occurred: {error}")
        quit()


@begin.subcommand
def make_annotations(root="data", zoom=17, type="COCO", outfile=None, is_crowd=False):
    logger.info("MAKE ANNOTATIONS")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the tiles
    try:
        if type.lower() == "coco":
            annotation = COCO.from_dataset(dataset, zoom, is_crowd=is_crowd)
            outfile = annotation.save(outfile)
        else:
            logger.error(f"Annnotation {type} not found. Available annotations are: 'coco'.")
        logger.info(f"Annotations successfully generated at '{outfile}'")
    except Exception as error:
        logger.error(f"Could not make the annnotation {type}. The following error occurred: {error}")
        quit()


@begin.subcommand
def make_all(root, type, zoom, outfile=None, is_crowd=False):
    make_labels(root)
    make_tiles(root, zoom=zoom)
    make_annotations(root, type, zoom, outfile=outfile, is_crowd=is_crowd)


@begin.start(short_args=True, lexical_order=False)
def main():
    pass
