# Encoding: UTF-8
# File: download.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


from sentinelsat import SentinelAPI
from shutil import copyfile
from pathlib import Path
import zipfile
import datetime

# Geolabel Maker
from geolabel_maker.logger import logger


class SentinelHubAPI:

    def __init__(self, username, password):
        self.url = "https://scihub.copernicus.eu/dhus"
        self.username = username
        self.password = password

    def download(self, bbox, date_min=None, date_max=None, outdir="sentinel", resolution=10, bandname="TCI", **kwargs):
        """Download Sentinel image from a bounding box.

        .. note::
            This method will download, extract and keep only relevant images from Sentinel Hub.

        .. seealso::
            Read `SentinelHub <https://docs.sentinel-hub.com/api/latest/>`__ API documentation for further details.

        Args:
            bbox (tuple): A bounding box in the format :math:`(lat_{min}, lon_{min}, lat_{max}, lon_{max})`.
            date (str, datetime or tuple, optional): The date (range) to download images. Defaults to ``None``.
            outdir (str, optional): Output directory where the retrieved images will be saved. Defaults to ``"sentinel"``.
            resolution (int, optional): The level of resolution. Options available are: ``10``, ``20``, ``60``.
                Defaults to ``10``.
            bandname (str, optional): The name of the band to pick. See Sentinel documentation for more details. 
                Defaults to ``"TCI"``.
            kwargs: Other arguments from `SentinelHub <https://docs.sentinel-hub.com/api/latest/>`__ API.

        Returns:
            list: List of downloaded files.

        Examples:
            >>> # Connect to the API
            >>> username = "your_username"
            >>> password = "your_password"
            >>> api = SentinelHubAPI(username, password)
            >>> # Download images within a bounding box
            >>> bbox = (50, 7, 51, 8)
            >>> date_min = "20200920"
            >>> date_max = "20200925"
            >>> files = api.download(bbox, date_min=date_min, date_max=date_max)
        """
        # Connect to the main API
        logger.info(f"Connecting to SentinelHub API...")
        api = SentinelAPI(self.username, self.password, self.url)
        logger.info("Successfully connected.")

        # Retrieve the area of interest in WKT format
        lat_min, lon_min, lat_max, lon_max = bbox
        footprint = f"POLYGON(({lon_max} {lat_min},{lon_min} {lat_min},{lon_min} {lat_max},{lon_max} {lat_max},{lon_max} {lat_min}))"

        # Make date range
        date_min = date_min or datetime.now().strftime("%Y%m%d")
        date_max = date_max or datetime.now().strftime("%Y%m%d")

        # Make a request
        query_string = f"footprint={footprint}, date={date_min, date_max}, " + ", ".join([f"{key}={value}" for key, value in kwargs.items()])
        logger.info(f"Retrieving products for the query: {query_string}.")
        products = api.query(
            footprint,
            date=(date_min, date_max),
            **kwargs
        )
        logger.info("Products successfully retrieved.")
        products_gdf = api.to_geodataframe(products)
        logger.info(f"There are {len(products_gdf)} products found.")

        # Create the output directory if it does not exist
        outdir_cache = Path(outdir).parent / f".{Path(outdir).name}"
        Path(outdir_cache).mkdir(parents=True, exist_ok=True)
        Path(outdir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading the products to cache directory {outdir_cache}.")

        # Download all results from the search in a cache folder
        for product_id in products_gdf.index:
            api.download(product_id, outdir_cache)

        # Unzip the image folders
        logger.info(f"Extracting the products to directory {outdir_cache}.")
        self.extract_all(outdir_cache, outdir_cache)

        # Move the images at `resolution`
        files = []
        logger.info(f"Transferring the images at resolution={resolution}, bandname={bandname} to directory {outdir}.")
        for product_name in products_gdf.title:
            product_path = Path(outdir_cache) / product_name
            image_file = self.find_image(product_path, resolution=resolution, bandname=bandname)
            # Move/copy the image to the main directory
            out_image = Path(outdir) / Path(image_file).name
            copyfile(str(image_file), str(out_image))
            files.append(out_image)

        return files

    @staticmethod
    def extract_all(indir, outdir=None):
        outdir = outdir or indir
        # Extract all files in a directory
        for file in Path(indir).iterdir():
            filename = str(file)
            if zipfile.is_zipfile(filename):
                zipfile.ZipFile(filename, 'r').extractall(outdir)
            # Delete the zip file to keep only the content
            file.unlink()

    @staticmethod
    def find_image(product_path, resolution=10, bandname="TCI"):

        product_dir = Path(product_path).parent
        product_name = Path(product_path).name
        granule_dir = product_dir / f"{product_name}.SAFE" / "GRANULE"

        for res_dir in granule_dir.iterdir():
            image_dir = res_dir / "IMG_DATA" / f"R{resolution}m"
            for image_file in image_dir.iterdir():
                if image_file.stem.endswith(f"{bandname.upper()}_{resolution}m"):
                    return image_file
