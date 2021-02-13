# Encoding: UTF-8
# File: mapbox.py
# Creation: Friday February 12th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import shutil
from pathlib import Path
import requests
from osgeo import gdal

# Geolabel Maker
from geolabel_maker.logger import logger
from .functions import generate_vrt, merge
from .utils import bbox2xyz, xyz2bounds, latlon2xyz


class MapBoxAPI:

    def __init__(self, access_token):
        self.url = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}{res}.{format}?access_token={access_token}"
        self.access_token = access_token

    @staticmethod
    def georeference(x, y, z, tile_file, out_file=None):
        """Georeference a slippy tile image.

        Args:
            x (int): X coordinate of the slippy tile.
            y (int): Y coordinate of the slippy tile.
            z (int): Zoom level.
            tile_file (str): Name of the slippy tile image.
            out_file (str, optional): Name of the output georeferenced image. 
                If ``None``, will have the same name as the slippy image. Defaults to ``None``.
        """
        bounds = xyz2bounds(x, y, z)
        slippy_file_ = Path(tile_file).with_suffix("")
        out_file = out_file or Path(slippy_file_).with_suffix(".tif")
        gdal.Translate(
            str(out_file),
            str(tile_file),
            outputSRS="EPSG:4326",
            outputBounds=bounds
        )
        return out_file

    @staticmethod
    def get_tile(x, y, z, slippy_maps=True, tile_dir=".", tile_format="png"):
        if slippy_maps:
            return Path(tile_dir) / f"{z}/{x}/{y}.{tile_format}"
        else:
            return Path(tile_dir) / f"MAPBOX_{z}_{x}_{y}.{tile_format}"

    def download_tile(self, x, y, z, high_res=True, out_file="mapbox.png"):
        res = "@2x" if high_res else ""
        url = self.url.format(z=z, x=x, y=y, res=res, format="png", access_token=self.access_token)
        response = requests.get(url)
        out_tile = Path(out_file).with_suffix(".png")
        out_tile.parent.mkdir(parents=True, exist_ok=True)
        with open(out_tile, "wb") as output:
            output.write(response.content)

        # Geolocalize the image
        if Path(out_file).suffix.lower() in [".tif", ".tiff"]:
            self.georeference(x, y, z, out_tile)
            out_tile.unlink()

        return out_file

    def download_image(self, lat, lon, zoom, **kwargs):
        x, y = latlon2xyz(lat, lon, zoom)
        return self.download_tile(x, y, zoom, **kwargs)

    def download(self, bbox, zoom, width=256, height=256, high_res=True, slippy_maps=False,
                 out_format="tif", out_dir="mapbox", compress="jpeg", photometric="ycbcr", tiled=True):
        """Download satellite images from `MapBox` API.

        Args:
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            zoom (int): Zoom level.
            width (int, optional): Width of the downloaded image. The width must be a multiple of ``256``.
                Defaults to ``256``.
            height (int, optional): height of the downloaded image. The height must be a multiple of ``256``. 
                Defaults to ``256``.
            high_res (bool, optional): If ``True`` will save slippy maps as image of shape :math:`(512, 512)`. *
                If not, the shape is :math:`(256, 256)`. Defaults to ``True``. 
            slippy_maps (bool, optional): If ``True``, save the images as slippy maps. Defaults to ``False``.
            out_format (str, optional): Output format of the files. Options are ``"png"`` or ``"tif"``. Defaults to ``"png"``.
            out_dir (str, optional): Path to the output directory. Defaults to ``"mapbox"``.
            compress (str, optional): Compression mode used by `GDAL`. Defaults to ``None``.
            photometric (str, optional): Pixel format used by `GDAL`. Defaults to ``"ycbcr"``.
            tiled (bool, optional): If ``True``, will compress the image as tiles. Defaults to ``True``.
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        lon_min, lat_min, lon_max, lat_max = bbox
        x_min, y_min, x_max, y_max = bbox2xyz(lon_min, lat_min, lon_max, lat_max, zoom)
        logger.info(f"Generate {(x_max - x_min + 1) * (y_max - y_min + 1):,} satellite images at zoom level {zoom}")

        x_range = max(width // (256 * (1 + int(high_res))), 1)
        y_range = max(height // (256 * (1 + int(high_res))), 1)
        for x_mosaic in range(x_min, x_max + 1, x_range):
            for y_mosaic in range(y_min, y_max + 1, y_range):

                # Store the image that will be merged to create a single mosaic
                mosaic_files = []
                for x in range(x_mosaic, min(x_mosaic + x_range, x_max + 1)):
                    for y in range(y_mosaic, min(y_mosaic + y_range, y_max + 1)):
                        # Download slippy image in png format
                        tile_image = self.get_tile(x, y, zoom, slippy_maps=slippy_maps, tile_dir=out_dir, tile_format="png")
                        self.download_tile(x, y, zoom, high_res=high_res, out_file=tile_image)
                        # Georeference the image
                        if out_format.lower() in ["tif", "tiff"]:
                            tile_geotiff = self.get_tile(x, y, zoom, slippy_maps=False, tile_dir=out_dir, tile_format=out_format)
                            tile_geotiff = self.georeference(x, y, zoom, tile_image, tile_geotiff)
                            mosaic_files.append(str(tile_geotiff))
                        # Remove the slippy image
                        if not slippy_maps:
                            tile_image.unlink()

                # Merge the georeferenced tiles
                if out_format.lower() in ["tif", "tiff"]:
                    # Merge the tiles for each mosaic
                    if len(mosaic_files) > 1:
                        out_mosaic = Path(out_dir) / f"MAPBOX_MOSAIC_{zoom}_{x}_{y}.tif"
                        mosaic_vrt = out_mosaic.with_suffix(".vrt")
                        mosaic_vrt = generate_vrt(mosaic_vrt, mosaic_files)
                        merge(out_mosaic, mosaic_vrt, compress=compress, photometric=photometric, tiled=tiled)
                        Path(mosaic_vrt).unlink()
                        # Remove the georeferenced
                        for mosaic_file in mosaic_files:
                            Path(mosaic_file).unlink()
