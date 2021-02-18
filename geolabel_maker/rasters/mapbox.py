# Encoding: UTF-8
# File: mapbox.py
# Creation: Friday February 12th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
Defines the `MapBox` API, used to retrieve tiles from their services 
and convert slippy maps to georeferenced images.

.. code-block:: python

    from geolabel_maker.rasters.mapbox import MapBoxAPI
    
    # Visit MapBox API to get your user token
    ACCESS_TOKEN = "pk.[...]"
    
    api = MapBoxAPI(ACCESS_TOKEN)
    
    # Download a tile from it's XYZ coordinates
    api.download_tile(x=66391, y=45088, z=17)
    
    # Download a georeferenced image from it's geographic coordinates
    api.download_image(lat=48.8520, lon=2.3483, zoom=17)
    
    # Download multiple georeferenced images from a bounding box
    bbox = (2.3483, 48.8520, 2.3693, 48.8638)
    api.download(bbox, zoom=17, width=1024, height=1024, slippy_maps=True)
"""

# Basic imports
from tqdm import tqdm
from pathlib import Path
import requests
from osgeo import gdal

# Geolabel Maker
from geolabel_maker.logger import logger
from .functions import generate_vrt, merge
from .utils import bbox2xyz, xyz2bounds, latlon2xyz


class MapBoxAPI:
    r"""
    Connect to `MapBox` API.
    This class is equivalent to ``mapbox.Static``, but provide more options for georefencing satellite images.
    
    * :attr:`url` (str): URL used to retrieve static images.
    
    * :attr:`access_token` (str): User token.
    
    """

    def __init__(self, access_token):
        self.url = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}{res}.{format}?access_token={access_token}"
        self.access_token = access_token

    @staticmethod
    def georeference(x, y, z, tile_file, out_file):
        r"""Georeference a slippy tile image.

        Args:
            x (int): X coordinate of the slippy tile.
            y (int): Y coordinate of the slippy tile.
            z (int): Zoom level.
            tile_file (str): Name of the slippy tile image.
            out_file (str): Name of the output georeferenced image. 
            
        Examples:
            api = MapBoxAPI(ACCESS_TOKEN)
            api.georeference(x=190, y=198, z=17, "17/190/198.png", "tile.tif")
        """
        bounds = xyz2bounds(x, y, z)
        gdal.Translate(
            str(out_file),
            str(tile_file),
            outputSRS="EPSG:4326",
            outputBounds=bounds
        )
        return str(out_file)

    @staticmethod
    def get_tile(x, y, z, slippy_maps=False, tile_dir=".", tile_format="png"):
        r"""Method used to generate a tile name depending on different options.

        Args:
            x (int): X coordinate of the tile.
            y (int): Y coordinate of the tile.
            z (in): Zoom level.
            slippy_maps (bool, optional): If ``True``, the tile name will follow the slippy map format. 
                Defaults to ``False``.
            tile_dir (str, optional): Name of the directory containing the tiles. Defaults to ".".
            tile_format (str, optional): Format of the file. Defaults to ``"png"``.

        Returns:
            str
        """
        if slippy_maps:
            return str(Path(tile_dir) / f"{z}/{x}/{y}.{tile_format}")
        else:
            return str(Path(tile_dir) / f"MAPBOX_{z}_{x}_{y}.{tile_format}")

    def download_tile(self, x, y, z, high_res=True, out_file="mapbox.png"):
        r"""Download a tile in ``"png"`` format from `MapBox` API.

        Args:
            x (int): X coordinate of the tile.
            y (int): Y coordinate of the tile.
            z (in): Zoom level.
            high_res (bool, optional): If ``True`` will request high resolution slippy maps from `MapBox`. Defaults to ``True``.
            out_file (str, optional): Name of the output file. Defaults to ``"mapbox.png"``.

        Returns:
            str
        
        Examples:
            >>> api = MapBoxAPI(ACCESS_TOKEN)
            >>> api.download_tile(x=66391, y=45088, z=17)
        """
        # Request high resolution tiles
        res = "@2x" if high_res else ""
        url = self.url.format(z=z, x=x, y=y, res=res, format="png", access_token=self.access_token)
        response = requests.get(url)
        # Save the tile and make sure the parent directory exists
        out_tile = Path(out_file).with_suffix(".png")
        out_tile.parent.mkdir(parents=True, exist_ok=True)
        with open(out_tile, "wb") as output:
            output.write(response.content)
        return str(out_tile)

    def download_image(self, lat, lon, zoom, high_res=True, out_file="mapbox.tif"):
        r"""Download a georeferenced satellite image from `MapBox` API.

        Args:
            lat (float): Latitude of the image.
            lon (float): Longitude of the image.
            zoom (int): Zoom level.
            high_res (bool, optional): If ``True`` will request high resolution slippy maps from `MapBox`. Defaults to ``True``.
            out_file (str, optional): Name of the output file. Defaults to ``"mapbox.tif"``.

        Returns:
            str
            
        Examples:
            >>> api = MapBoxAPI(ACCESS_TOKEN)
            >>> api.download_image(lat=48.8520, lon=2.3483, zoom=17)
        """
        x, y = latlon2xyz(lat, lon, zoom)
        out_tile = self.download_tile(x, y, zoom, high_res=high_res, out_file=out_file)
        # Geolocalize the image
        if Path(out_file).suffix.lower() in [".tif", ".tiff"]:
            out_file = self.georeference(x, y, zoom, out_tile, out_file)
            Path(out_tile).unlink()
        return str(out_file)

    def download(self, bbox, zoom, width=10_240, height=10_240, high_res=True, slippy_maps=False,
                 out_format="tif", out_dir="mapbox", compress="jpeg", photometric="ycbcr", tiled=True):
        r"""Download georeferenced satellite images from `MapBox` API.

        Args:
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            zoom (int): Zoom level.
            width (int, optional): Width of the downloaded image. The width must be a multiple of ``256``. 
                Defaults to ``10_240``.    
            height (int, optional): Height of the downloaded image. The height must be a multiple of ``256``. 
                Defaults to ``10_240``.
            high_res (bool, optional): If ``True`` will request high resolution slippy maps from `MapBox`. Defaults to ``True``.
            slippy_maps (bool, optional): If ``True``, save the images as slippy maps. Defaults to ``False``.
            out_format (str, optional): Output format of the files. Options are ``"png"`` or ``"tif"``. Defaults to ``"png"``.
            out_dir (str, optional): Path to the output directory. Defaults to ``"mapbox"``.
            compress (str, optional): Compression mode used by `GDAL`. Defaults to ``None``.
            photometric (str, optional): Pixel format used by `GDAL`. Defaults to ``"ycbcr"``.
            tiled (bool, optional): If ``True``, will compress the image as tiles. Defaults to ``True``.
            
        Examples:
            >>> api = MapBoxAPI(ACCESS_TOKEN)
            >>> bbox = (2.3483, 48.8520, 2.3693, 48.8638)
            >>> api.download(bbox, zoom=17, width=1024, height=1024, high_res=True, slippy_maps=True)
        """
        # Track the downloaded files
        out_files = []
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        # Convert the bbox to xyz (slippy maps format)
        lon_min, lat_min, lon_max, lat_max = bbox
        x_min, y_min, x_max, y_max = bbox2xyz(lon_min, lat_min, lon_max, lat_max, zoom)
        logger.info(f"Generate {(x_max - x_min + 1) * (y_max - y_min + 1):,} satellite images at zoom level {zoom}")

        x_range = max(width // (256 * (1 + int(high_res))), 1)
        y_range = max(height // (256 * (1 + int(high_res))), 1)
        pbar = tqdm(total=((x_max - x_min + 1) * (y_max - y_min + 1)), desc="Downloading", leave=True, position=0)
        for x_mosaic in range(x_min, x_max + 1, x_range):
            for y_mosaic in range(y_min, y_max + 1, y_range):

                # Store the images that will be merged to create a single mosaic
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
                            mosaic_files.append(tile_geotiff)
                        # Remove the slippy image
                        if not slippy_maps:
                            Path(tile_image).unlink()
                        pbar.update(1)

                # Merge the georeferenced tiles
                if out_format.lower() in ["tif", "tiff"]:
                    # Merge the tiles for each mosaic
                    if len(mosaic_files) > 1:
                        out_mosaic = Path(out_dir) / f"MAPBOX_MOSAIC_{zoom}_{x}_{y}.tif"
                        out_file = merge(mosaic_files, out_mosaic, compress=compress, photometric=photometric, tiled=tiled)
                        out_files.append(str(out_file))
                        # Remove the georeferenced
                        for mosaic_file in mosaic_files:
                            Path(mosaic_file).unlink()
                # If the format was png
                else:
                    out_files.append(str(tile_image))
        return out_files