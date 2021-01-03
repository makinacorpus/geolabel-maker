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
from osgeo import gdal
import rasterio
import rasterio.merge
from shutil import copyfile
import gdal2tiles
from pathlib import Path

# Geolabel Maker
from .raster import to_raster


def generate_tiles(raster, dir_tiles, **kwargs):
    r"""Create tiles from a raster file (using GDAL)

    Args:
        raster (Raster): The raster used to generate tiles.
        dir_tiles (str): The path to the directory where the tiles will be saved

    Examples:
        >>> raster = Raster.open("raster.tif")
        >>> generate_tiles(raster, "tiles")
    """
    Path(dir_tiles).mkdir(parents=True, exist_ok=True)
    # Generate tiles with `gdal2tiles`
    file_raster = to_raster(raster).data.name
    gdal2tiles.generate_tiles(file_raster, dir_tiles, **kwargs)


def generate_vrt(outfile, rasters):
    """Builds a virtual raster from a list of rasters.

    Args:
        dir_rasters (str): The images directory path.
        out_name (str): The name of the output virtual raster. Default value is ``out.vrt``.

    Returns:
        str: Path to the VRT file.

    Examples:
        >>> tile1 = Raster.open("tile1.tif")
        >>> tile2 = Raster.open("tile2.tif")
        >>> generate_vrt("tiles.vrt", [tile1, tile2])
    """
    raster_files = [to_raster(raster).data.name for raster in rasters]
    ds = gdal.BuildVRT(outfile, raster_files)
    ds.FlushCache()
    return outfile


def merge_rasters(outfile, rasters):
    """Merge raster files from a specific directory to a single geotiff.

    Args:
        rasters (str): The images directory path.
        output_file (str): The name of the final raster. Default value is ``"merged.tif"``.

    Returns:
        str: The name of the final raster.

    Examples:
        >>> tile1 = Raster.open("tile1.tif")
        >>> tile2 = Raster.open("tile2.tif")
        >>> merge_rasters("tiles.tif", [tile1, tile2])
    """
    out_path = None
    if len(rasters) > 0:
        img_path = rasters[0].parent
        out_path = img_path / outfile

        if len(rasters) > 1:
            # open raster files
            rasters_data = []
            for raster in rasters:
                raster_data = raster.data
                rasters_data.append(raster_data)

            # merge raster images
            mosaic, out_transform = rasterio.merge.merge(rasters_data)

            # create metadata for the merged raster
            out_profile = raster_data.profile.copy()
            out_profile.update(
                {
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_transform,
                }
            )

            # write the merged raster
            with rasterio.open(out_path, "w", **out_profile) as dest:
                dest.write(mosaic)

        elif len(rasters) == 1:
            copyfile(rasters[0], out_path)

    return out_path
