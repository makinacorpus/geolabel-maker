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
from pathlib import Path
from osgeo import gdal
import gdal2tiles


def generate_tiles(filename, out_dir="tiles", **kwargs):
    r"""Create tiles from a raster file (using GDAL)

    .. note::
        If the output directory ``out_dir`` does not exist,
        it will be created.

    Args:
        filename (str): Name of the raster file used to generate tiles.
        out_dir (str, optional): Path to the directory where the tiles will be saved.

    Examples:
        >>> generate_tiles("raster.tif", out_dir="tiles")
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    gdal2tiles.generate_tiles(str(filename), out_dir, **kwargs)


def generate_vrt(filename, rasters):
    """Builds a virtual raster from a list of rasters.

    Args:
        filename (str): Name of the output virtual raster.
        rasters (list): List of rasters to be merged.

    Returns:
        str: Path to the VRT file.

    Examples:
        >>> tile1 = Raster.open("tile1.tif")
        >>> tile2 = Raster.open("tile2.tif")
        >>> generate_vrt("tiles.vrt", [tile1, tile2])
    """
    raster_files = [str(raster.filename) for raster in rasters]
    ds = gdal.BuildVRT(str(filename), raster_files)
    ds.FlushCache()
    return filename
