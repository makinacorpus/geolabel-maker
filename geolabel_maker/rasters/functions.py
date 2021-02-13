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
    generate_tiles("raster.tif", out_dir="tiles")
    
    # Generate virtual raster(s)
    generate_vrt("tiles.vrt", ["tile1.tif", "tile2.tif"])
    
    # Merge raster(s)
    merge("tiles.tif", ["tile1.tif", "tile2.tif"])
"""

# Basic imports
import os
from pathlib import Path
from osgeo import gdal
import gdal2tiles
import rasterio


__all__ = [
    "generate_tiles",
    "generate_vrt"
]


def generate_tiles(in_file, out_dir, **kwargs):
    r"""Create tiles from a raster file (using GDAL)

    .. note::
        If the output directory ``out_dir`` does not exist,
        it will be created.

    Args:
        in_file (str): Name of the raster file used to generate tiles.
        out_dir (str, optional): Path to the directory where the tiles will be saved.

    Examples:
        >>> generate_tiles("raster.tif", out_dir="tiles")
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    gdal2tiles.generate_tiles(str(in_file), str(out_dir), **kwargs)


def generate_vrt(in_files, out_file):
    r"""Builds a virtual raster from a list of rasters.

    Args:
        out_file (str): Name of the output virtual raster.
        in_files (list): List of rasters paths to be merged.

    Returns:
        str: Path to the VRT file.

    Examples:
        >>> generate_vrt("tiles.vrt", ["tile1.tif", "tile2.tif"])
    """
    in_files = list(map(str, in_files))
    ds = gdal.BuildVRT(str(out_file), in_files)
    ds.FlushCache()
    return out_file


def merge(in_files, out_file, driver="GTiff", compress="jpeg", photometric="ycbcr", tiled=True):
    r"""Merge multiple raster files with `GDAL`.

    Args:
        in_files (str): Path of the raster files to merge.
        out_file (str): Name of the output file.
        driver (str, optional): Name of the `GDAL` driver. Defaults to ``"GTiff"``.
        compress (str, optional): Name of the `GDAL` compression mode. Defaults to ``"jpeg"``.
        photometric (str, optional): Name of the `GDAL` pixel format. Defaults to ``"ycbcr"``.
        tiled (bool, optional): If ``True``, tile the output raster to decrease file size. Defaults to ``True``.
        
    Examples:
        >>> merge("tiles.tif", ["tile1.tif", "tile2.tif"])
    """
    # Create a virtual image of the files to be merged
    out_vrt = Path(out_file).with_suffix(".vrt")
    out_vrt = generate_vrt(in_files, out_vrt)

    # Create a raster from the virtual image
    command = ["gdal_translate"]
    if driver:
        command.extend(["-of", driver])
    if compress:
        command.extend(["-co", f"COMPRESS={compress.upper()}"])
    if photometric:
        command.extend(["-co", f"PHOTOMETRIC={photometric.upper()}"])
    if tiled:
        command.extend(["-co", f"TILED=YES"])
    command.extend([str(out_vrt), str(out_file)])
    os.system(" ".join(command))
    # Delete the virtual image
    Path(out_vrt).unlink()
