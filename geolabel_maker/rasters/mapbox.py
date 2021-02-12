# Encoding: UTF-8
# File: mapbox.py
# Creation: Friday February 12th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import os
from pathlib import Path
import requests
from osgeo import gdal
import pandas as pd

# Geolabel Maker
from geolabel_maker.logger import logger
from .utils import bbox2xyz, xyz2bounds


class MapBoxAPI:

    def __init__(self, access_token):
        self.url = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}{res}.{format}?access_token={access_token}"
        self.access_token = access_token

    @staticmethod
    def merge(out_file, in_pattern, delete=False):
        """
        Merge raster files in a single geoTIFF
        :param input_pattern: input folder containing raster files (starting with the suffix SAT_) as Path object
        :param output_path: output filename
        """
        merge_command = ["gdal_merge.py", "-o", str(out_file)]

        for file_path in Path(in_pattern).rglob("*.tif"):
            merge_command.append(str(file_path))

        os.system(" ".join(merge_command))

        # Remove little images
        if delete:
            for file_path in Path(in_pattern).rglob("*.tif"):
                file_path.unlink()

    @staticmethod
    def georeference(x, y, z, slippy_file, out_file=None):
        """Georeference a slippy tile image.

        Args:
            x (int): X coordinate of the slippy tile.
            y (int): Y coordinate of the slippy tile.
            z (int): Zoom level.
            slippy_file (str): Name of the slippy tile image.
            out_file (str, optional): Name of the output georeferenced image. 
                If ``None``, will have the same name as the slippy image. Defaults to ``None``.
        """
        bounds = xyz2bounds(x, y, z)
        slippy_file_ = Path(slippy_file).with_suffix("")
        out_file = out_file or Path(slippy_file_).with_suffix(".tif")
        gdal.Translate(
            str(out_file),
            str(slippy_file),
            outputSRS="EPSG:4326",
            outputBounds=bounds
        )

    def download(self, bbox, zoom, high_res=True, slippy_maps=False, out_format="tif", out_dir="mapbox"):
        """Download satellite images from `MapBox` API.

        Args:
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            zoom (int): Zoom level.
            high_res (bool, optional): If ``True`` will save slippy maps as image of shape :math:`(512, 512)`. 
                If not, the shape is :math:`(256, 256)`. Defaults to ``True``.
            slippy_maps (bool, optional): If ``True``, save the images as slippy maps. Defaults to ``False``.
            out_format (str, optional): Output format of the files. Options are ``"png"`` or ``"tif"``. Defaults to ``"png"``.
            out_dir (str, optional): Path to the output directory. Defaults to ``"mapbox"``.
        """
        res = "@2x" if high_res else ""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        lon_min, lat_min, lon_max, lat_max = bbox
        x_min, y_min, x_max, y_max = bbox2xyz(lon_min, lat_min, lon_max, lat_max, zoom)
        logger.info(f"Generate {(x_max - x_min + 1) * (y_max - y_min + 1):,} satellite images at zoom level {zoom}")

        # Generate an image for each position on the grid
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                # Create the satellite image name
                if slippy_maps:
                    out_file = Path(out_dir) / f"{zoom}" / f"{x}" / f"{y}.png"
                    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
                else:
                    out_file = Path(out_dir) / f"MAPBOX_{zoom}_{x}_{y}.png"

                url = self.url.format(z=zoom, x=x, y=y, res=res, format="png", access_token=self.access_token)
                response = requests.get(url)
                # Save the content in nested directories
                with open(out_file, "wb") as output:
                    output.write(response.content)

                # Geolocalize the image
                if not slippy_maps or out_format.lower() in ["tif", "tiff", "gtiff", "gtiff_m"]:
                    self.georeference(x, y, zoom, out_file)
                    out_file.unlink()
