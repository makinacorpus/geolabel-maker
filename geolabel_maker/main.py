# Encoding: UTF-8
# File: main.py
# Creation: Sunday March 14th 2021
# Supervisor: Daphne Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import textwrap

# Geolabel Maker
from geolabel_maker import Dataset
from geolabel_maker.annotations import Classification, ObjectDetection, Segmentation
from geolabel_maker.version import __version__


def open_dataset(images=None, categories=None, labels=None,
                 dir_images=None, dir_categories=None, dir_labels=None,
                 config=None, root=None, **kwargs):
    if images is not None and categories is not None:
        return Dataset(images=images, categories=categories, labels=labels)
    elif config:
        return Dataset.open(config)
    elif root:
        return Dataset.from_root(root)
    elif dir_images and dir_categories:
        return Dataset.from_dir(dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels)


def run_download(config, **kwargs):
    return Dataset.download(config)


def run_labels(dataset=None, images=None, categories=None,
               dir_images=None, dir_categories=None,
               config=None, root=None, out_dir=None, **kwargs):
    dataset = dataset or open_dataset(
        images=images, categories=categories,
        dir_images=dir_images, dir_categories=dir_categories,
        config=config, root=root
    )
    out_dir = dataset.generate_labels(out_dir)


def run_mosaics(dataset=None, images=None, categories=None, labels=None,
                dir_images=None, dir_categories=None, dir_labels=None,
                config=None, root=None, zoom=None, out_dir=None, **kwargs):
    dataset = dataset or open_dataset(
        images=images, categories=categories, labels=labels,
        dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
        config=config, root=root
    )
    return dataset.generate_mosaics(zoom=zoom, out_dir=out_dir)


def run_tiles(dataset=None, images=None, categories=None, labels=None,
              dir_images=None, dir_categories=None, dir_labels=None,
              config=None, root=None, zoom=None, out_dir=None, **kwargs):
    dataset = dataset or open_dataset(
        images=images, categories=categories, labels=labels,
        dir_images=dir_images, dir_categories=dir_categories, dir_labels=dir_labels,
        config=config, root=root
    )
    return dataset.generate_tiles(zoom=zoom, out_dir=out_dir)


def run_annotations(dataset=None, images=None, labels=None, categories=None,
                    dir_images=None, dir_labels=None, dir_categories=None, colors=None,
                    pattern_image="*.*", pattern_label="*.*", pattern_category="*", is_crowd=True,
                    type="segmentation", out_file="annotations.json", use_labels=True, **kwargs):
    if type.lower() in ["segmentation", "coco", "s"]:
        ann_class = Segmentation
    elif type.lower() in ["object_detection", "o"]:
        ann_class = ObjectDetection
    elif type.lower() in ["classification", "c"]:
        ann_class = Classification

    categories = dataset.categories if dataset else categories
    colors = dict([value.strip().split("=") for value in colors.strip().split(",")]) if colors else None

    if not use_labels:
        annotation = ann_class.make(
            images=images, categories=categories,
            dir_images=dir_images, dir_categories=dir_categories,
            pattern_image=pattern_image or "*.*", pattern_category=pattern_category, is_crowd=is_crowd
        )
    else:
        annotation = ann_class.build(
            images=images, labels=labels, categories=categories,
            dir_images=dir_images, dir_labels=dir_labels, colors=colors,
            pattern_image=pattern_image, pattern_label=pattern_label, is_crowd=is_crowd
        )
    out_file = annotation.save(out_file)


def run_all(**kwargs):

    dataset = open_dataset(**kwargs)
    run_labels(dataset=dataset, **kwargs)
    if "mosaics" in kwargs.keys():
        out_dir = run_mosaics(dataset=dataset, **kwargs)
    elif "tiles" in kwargs.keys():
        out_dir = run_tiles(dataset=dataset, **kwargs)
    zoom = kwargs.pop("zoom", None) or "original"
    dir_images = Path(out_dir) / "images" / str(zoom)
    dir_labels = Path(out_dir) / "labels" / str(zoom)
    kwargs["dir_images"] = dir_images
    kwargs["dir_labels"] = dir_labels
    kwargs.pop("images", None)
    kwargs.pop("labels", None)
    run_annotations(dataset=dataset, **kwargs)


def get_parser():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(f"""\
                                geolabel-maker v{__version__}

              ____            _       _          _   __  __       _             
             / ___| ___  ___ | | __ _| |__   ___| | |  \/  | __ _| | _____ _ __ 
            | |  _ / _ \/ _ \| |/ _` | "_ \ / _ \ | | |\/| |/ _` | |/ / _ \ "__|
            | |_| |  __/ (_) | | (_| | |_) |  __/ | | |  | | (_| |   <  __/ |   
             \____|\___|\___/|_|\__,_|_.__/ \___|_| |_|  |_|\__,_|_|\_\___|_|   

            Generate labels and annotations for geospatial artificial intelligence tasks.
        """)
    )

    parent_parser = parser.add_subparsers(dest="command")

    parent_dataset = ArgumentParser(add_help=False)
    parent_images = ArgumentParser(add_help=False)
    parent_categories = ArgumentParser(add_help=False)
    parent_labels = ArgumentParser(add_help=False)
    parent_dataset.add_argument("--config", type=str, metavar="", required=False,
                                help="path to the configuration file of the dataset, e.g. --config data/dataset.json")
    parent_dataset.add_argument("--root", type=str, metavar="", required=False,
                                help="path to the root directory of the dataset, e.g. --root data")
    parent_images.add_argument("--dir_images", type=str, metavar="", required=False,
                               help="path to the directory containing images, e.g. --dir_images data/images")
    parent_categories.add_argument("--dir_categories", type=str, metavar="", required=False,
                                   help="path to the directory containing categories, e.g. --dir_categories data/categories")
    parent_labels.add_argument("--dir_labels", type=str, metavar="", required=False,
                               help="path to the directory containing labels, e.g. --dir_labels data/labels")
    parent_images.add_argument("--images", type=str, nargs="+", metavar="", required=False,
                               help="list of images to be used, e.g. --images data/images/tile1.tif data/images/tile2.tif")
    parent_categories.add_argument("--categories", type=str, nargs="+", metavar="", required=False,
                                   help="list of categories to be used, e.g. --categories data/categories/buildings.json data/categories/vegetation.json")
    parent_labels.add_argument("--labels", type=str, metavar="", nargs="+", required=False,
                               help="list of labels to be used, e.g. --labels data/labels/tile1.tif data/labels/tile2.tif")

    cmd_download = parent_parser.add_parser(
        "download", formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
                                    Download satellite imagery and vector data from SentinelHub, MapBox or OpenStreetMap.
                                                                        
                                    Example:
                                    geolabel_maker download --config credentials.json
                                    """)
    )
    cmd_download.add_argument("--config", type=str, metavar="", required=True,
                              help="path to the configuration file used to store credentials, e.g. --config credentials.json")

    cmd_labels = parent_parser.add_parser(
        "labels", parents=[parent_dataset, parent_images, parent_categories],
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
                                    Generate labels (i.e. masks) associated to an image and vector data.
                                                                        
                                    Example:
                                    geolabel_maker download --config credentials.json
                                    """)
    )
    cmd_labels.add_argument("--out_dir", type=str, metavar="", required=False,
                            help="path to the outout directory, e.g. --out_dir data/labels")

    cmd_mosaics = parent_parser.add_parser(
        "mosaics", parents=[parent_dataset, parent_images, parent_categories, parent_labels],
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
                                    Generate mosaics from images and labels.
                                                                        
                                    Example:
                                    geolabel_maker mosaics --config dataset.json --zoom 18
                                    """)
    )
    cmd_mosaics.add_argument("--out_dir", type=str, metavar="", required=False,
                             help="path to the outout directory, e.g. --out_dir data/mosaics")
    cmd_mosaics.add_argument("--zoom", type=int, metavar="", required=False,
                             help="zoom level at which the sub images will be generated, e.g. --zoom 18")
    cmd_mosaics.add_argument("--width", type=int, default=256, metavar="", required=False,
                             help="width of the mosaics, e.g. --width 256")
    cmd_mosaics.add_argument("--height", type=int, default=256, metavar="", required=False,
                             help="height of the mosaics, e.g. --height 256")
    cmd_mosaics.add_argument("--is_full", type=bool, default=True, metavar="", required=False,
                             help="if True, only generate tiles at full width and height, e.g. --is_full True")

    cmd_tiles = parent_parser.add_parser(
        "tiles", parents=[parent_dataset, parent_images, parent_categories, parent_labels],
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
                                    Generate tiles from images and labels.
                                                                        
                                    Example:
                                    geolabel_maker tiles --config dataset.json --zoom 17-18
                                    """)
    )
    cmd_tiles.add_argument("--out_dir", type=str, metavar="", required=False,
                           help="path to the outout directory, e.g. --out_dir data/tiles")
    cmd_tiles.add_argument("--zoom", type=int, metavar="", required=False,
                           help="zoom level at which the sub images will be generated, e.g. --zoom 18")

    cmd_annotations = parent_parser.add_parser("annotations", parents=[parent_dataset],
                                               description="Generate annotations from images, labels and categories.")
    cmd_annotations.add_argument("--dir_images", type=str, metavar="", required=False,
                                 help="path to the directory containing sub images, e.g. --dir_images data/mosaics/images/18")
    cmd_annotations.add_argument("--dir_categories", type=str, metavar="", required=False,
                                 help="path to the directory containing categories, e.g. --dir_categories data/categories")
    cmd_annotations.add_argument("--dir_labels", type=str, metavar="", required=False,
                                 help="path to the directory containing sub labels, e.g. --dir_labels data/mosaics/labels/18")
    cmd_annotations.add_argument("--images", type=str, nargs="+", metavar="", required=False,
                                 help="list of sub images to be used, e.g. --images data/mosaics/images/18/sub_tile0.png data/mosaics/images/18/sub_tile1.png")
    cmd_annotations.add_argument("--categories", type=str, nargs="+", metavar="", required=False,
                                 help="list of categories to be used, e.g. --categories data/categories/buildings.json data/categories/vegetation.json")
    cmd_annotations.add_argument("--labels", type=str, nargs="+", metavar="", required=False,
                                 help="list of sub labels to be used, e.g. --labels data/mosaics/labels/18/sub_tile0.png data/mosaics/labels/18/sub_tile1.png")
    cmd_annotations.add_argument("--colors", type=str, metavar="", required=False,
                                 help="names and colors associated to the categories, e.g. --colors buildings=white,vegetation=green")
    cmd_annotations.add_argument("--use_labels", type=bool, default=True, metavar="", required=False,
                                 help="if True build annotations from labels, else from categories, e.g. --use_labels True")
    cmd_annotations.add_argument("--type", type=str, default="segmentation", metavar="", required=False,
                                 help="type of annotations to build, e.g. --type segmentation")
    cmd_annotations.add_argument("--out_file", type=str, default="annotations.json", metavar="", required=False,
                                 help="name of the output file, e.g. --out_file annotations.json")

    cmd_all = parent_parser.add_parser("all", parents=[parent_dataset, parent_images, parent_categories],
                                       formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
                                    Generate labels and annotations.
                                                                        
                                    Example:
                                    geolabel_maker all --config dataset.json --zoom 18
                                    """)
    )
    cmd_all.add_argument("--mosaics", type=bool, default=True, metavar="", required=False,
                         help="if True will generate mosaics, e.g. --mosaics True")
    cmd_all.add_argument("--tiles", type=bool, default=False, metavar="", required=False,
                         help="if True will generate tiles, e.g. --tiles True")
    cmd_all.add_argument("--zoom", type=int, metavar="", required=False,
                         help="zoom level at which the sub images will be generated, e.g. --zoom 18")
    cmd_all.add_argument("--colors", type=str, metavar="", required=False,
                         help="names and colors associated to the categories, e.g. --colors buildings=white,vegetation=green")
    cmd_all.add_argument("--use_labels", type=bool, default=True, metavar="", required=False,
                         help="if True build annotations from labels, else from categories, e.g. --use_labels True")
    cmd_all.add_argument("--type", type=str, default="segmentation", metavar="", required=False,
                         help="type of annotations to build, e.g. --type segmentation")
    cmd_all.add_argument("--out_file", type=str, default="annotations.json", metavar="", required=False,
                         help="name of the output file, e.g. --out_file annotations.json")

    return parser


def main():
    parser = get_parser()
    args = vars(parser.parse_args())
    command = args.pop("command", None)
    if command == "download":
        run_download(**args)
    elif command == "labels":
        run_labels(**args)
    elif command == "mosaics":
        run_mosaics(**args)
    elif command == "tiles":
        run_tiles(**args)
    elif command == "annotations":
        run_annotations(**args)
    elif command == "all":
        run_all(**args)
    else:
        raise RuntimeError("Unrecognized command")


if __name__ == "__main__":
    main()
