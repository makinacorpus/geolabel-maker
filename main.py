# Encoding: UTF-8
# File: __main__.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import sys
from argparse import ArgumentParser
import json
import logging

# Geolabel Maker
from geolabel_maker.annotations import *
from geolabel_maker.dataset import Dataset


# Logger template
logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)


def open_dataset(root):
    try:
        logging.info(f"Loading the dataset at '{root}'")
        dataset = Dataset.open(root)
        logging.info(f"Dataset successfully loaded.")
        return dataset
    except Exception as error:
        logging.error(f"Could not open the dataset located at '{root}'. The following error occurred: {error}")
        quit()


def download():
    pass


def make_labels(root):
    logging.info("MAKE LABELS")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the labels
    try:
        logging.info(f"Generating labels...")
        labels_path = dataset.generate_labels()
        logging.info(f"Labels successfully generated at '{labels_path}'")
    except Exception as error:
        logging.error(f"Could not generate the labels. The following error occurred: {error}")
        quit()


def make_tiles(root, make_images=False, make_labels=True, zoom="13-20"):
    logging.info("MAKE TILES")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the tiles
    try:
        logging.info(f"Generating tiles at zoom level {zoom}...")
        dataset.generate_tiles(make_images=make_images, make_labels=make_labels, zoom=zoom)
        logging.info(f"Tiles successfully generated at '{dataset.dir_tiles}'")
    except Exception as error:
        logging.error(f"Could not generate the labels. The following error occurred: {error}")
        quit()


def make_annotations(root, type, zoom, outfile=None, is_crowd=False):
    logging.info("MAKE ANNOTATIONS")
    # Load the dataset
    dataset = open_dataset(root)
    # Generate the tiles
    try:
        if type.lower() == "coco":
            logging.info(f"Generating annotation COCO...")
            annotation = COCO.from_dataset(dataset, zoom, is_crowd=is_crowd)
            outfile = annotation.save(outfile)
        else:
            logging.error(f"Annnotation {type} not found. Available annotations are: 'coco'.")
        logging.info(f"Annotations successfully generated at '{outfile}'")
    except Exception as error:
        logging.error(f"Could not make the annnotation {type}. The following error occurred: {error}")
        quit()

def parse_args(args):
    parser = ArgumentParser()
    pparser = ArgumentParser(add_help=False)

    pparser.add_argument("-c", "--config", action="store", type=str, default=None,
                         help="Path to the config.json file.")

    pparser.add_argument("-r", "--root", action="store", type=str, default=None,
                         help="Path to the root folder. E.g. -r data")

    # add subcommands
    subparsers = parser.add_subparsers(dest="command")

    d = subparsers.add_parser("download", parents=[pparser], help="Download OSM geometries or satellite images from Sentinel Hub.")
    l = subparsers.add_parser("make_labels", parents=[pparser], help="Generate georeferenced raster labels from a set of aerial images and geometries.")
    t = subparsers.add_parser("make_tiles", parents=[pparser], help="Generate tiles from georeferenced labels and images.")
    a = subparsers.add_parser("make_annotations", parents=[pparser], help="Generate an annotation file.")

    # annotation has optionals parameter
    a.add_argument("-z", "--zoom", default=None, type=int,
                   help="Zoom level used to extract the geometries. E.g. -z 16")

    a.add_argument("-f", "--file", default="coco.json", type=str,
                   help="Output annotation filename E.g. -f coco.json")

    a.add_argument("-t", "--type", default="COCO", type=str,
                   help="Type of annotation. E.g. -t COCO")

    a.add_argument("--iscrowd", default=False, type=bool,
                   help="Information on the generated annotation.")

    # tiles has an optional parameter
    t.add_argument("-z", "--zoom", default=None, type=str,
                   help="Zoom interval used to generate tiles. E.g. -z 14-17")

    # turn namespace into dictionary
    parsed_args = vars(parser.parse_args(args))

    return parsed_args


def main():
    args = parse_args(sys.argv[1:])
    cmd = args.pop("command")

    # config = json.load(open(args.get("config")))
    root = args.get("root")

    if cmd == "download":
        download()

    elif cmd == "make_labels":
        make_labels(root)

    elif cmd == "make_tiles":
        zoom = args.get("zoom")
        make_tiles(root, zoom=zoom)

    elif cmd == "make_annotations":
        annotation_type = args.get("type")
        zoom = args.get("zoom")
        outfile = args.get("file")
        iscrowd = args.get("iscrowd")
        make_annotations(root, annotation_type, zoom, outfile=outfile, is_crowd=iscrowd)


if __name__ == "__main__":
    main()
