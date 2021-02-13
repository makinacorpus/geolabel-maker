# Encoding: UTF-8
# File: functions.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
Functions used to interact with ``Raster`` objects, 
like the creation of virtual images or merging tiles.
.. code-block:: python
    from geolabel_maker.rasters import Raster
    from geolabel_maker.vectors import Vector
    from geolabel_maker.functional import *
    
    # Generate tiles
    raster = Raster.open("raster.tif")
    generate_tiles(raster, "tiles")
    
    # Generate virtual raster(s)
    tile1 = Raster.open("tile1.tif")
    tile2 = Raster.open("tile2.tif")
    generate_vrt("tiles.vrt", [tile1, tile2])
    
    # Merge raster(s)
    tile1 = Raster.open("tile1.tif")
    tile2 = Raster.open("tile2.tif")
    merge_rasters("tiles.tif", [tile1, tile2])
"""

# Basic imports
import os
from pathlib import Path
from osgeo import gdal
import gdal2tiles


__all__ = [
    "generate_tiles",
    "generate_vrt"
]


def generate_tiles(out_dir, filename, **kwargs):
    r"""Create tiles from a raster file (using GDAL)

    .. note::
        If the output directory ``out_dir`` does not exist,
        it will be created.

    Args:
        out_dir (str, optional): Path to the directory where the tiles will be saved.
        filename (str): Name of the raster file used to generate tiles.

    Examples:
        >>> generate_tiles("raster.tif", out_dir="tiles")
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    gdal2tiles.generate_tiles(str(filename), out_dir, **kwargs)


def generate_vrt(out_file, rasters):
    """Builds a virtual raster from a list of rasters.

    Args:
        out_file (str): Name of the output virtual raster.
        rasters (list): List of rasters to be merged.

    Returns:
        str: Path to the VRT file.

    Examples:
        >>> tile1 = Raster.open("tile1.tif")
        >>> tile2 = Raster.open("tile2.tif")
        >>> generate_vrt("tiles.vrt", [tile1, tile2])
    """
    raster_files = [str(raster.filename) for raster in rasters]
    ds = gdal.BuildVRT(str(out_file), raster_files)
    ds.FlushCache()
    return out_file


def merge(out_file, in_file, driver="GTiff", compress="jpeg", photometric="ycbcr", tiled=True, **kwargs):
    command = ["gdal_translate"]
    if driver:
        command.extend(["-of", driver])
    if compress:
        command.extend(["-co", f"COMPRESS={compress.upper()}"])
    if photometric:
        command.extend(["-co", f"PHOTOMETRIC={compress.upper()}"])
    if tiled:
        command.extend(["-co", f"TILED={compress.upper()}"])
    command.extend([in_file, out_file])
    print(command)
    os.system(" ".join(command))
