# Encoding: UTF-8
# File: sentinelhub.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handles the download process with `SentinelHub` API.

.. code-block:: python

    from geolabel_maker.rasters.downloads import SentinelHubAPI
    
    username, password = "username", "password"
    bbox = (30, 40, 31, 41)
    
    api = SentinelHubAPI(username, password)
    files = api.download(bbox, out_dir="images")
"""


from sentinelsat import SentinelAPI
from shutil import copyfile
from pathlib import Path
import zipfile
from datetime import datetime

# Geolabel Maker
from .downloader import Downloader
from geolabel_maker.logger import logger


class SentinelHubAPI(Downloader):
    r"""
    Defines automatic downloads using the `SentinelHub <https://docs.sentinel-hub.com/api/latest/>`__ API.

    * :attr:`url` (str): URL used to connect to the API.

    * :attr:`username` (str): SciHub username.

    * :attr:`password` (str): SciHub password.

    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        url = "https://scihub.copernicus.eu/dhus"
        super().__init__(url)

    def download(self, bbox, date=None, platformname="Sentinel-2", 
                 processinglevel='Level-2A', cloudcoverpercentage=(0, 10), 
                 resolution=10, bandname="TCI", out_dir="sentinel", **kwargs):
        r"""Download Sentinel image from a bounding box.

        .. note::
            This method will download, extract and keep only relevant images from Sentinel Hub.

        .. seealso::
            Read `SentinelHub <https://docs.sentinel-hub.com/api/latest/>`__ API documentation for further details.

        Args:
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            date (str, datetime or tuple, optional): The date (range) to download images. Defaults to ``None``.
            platformname (str, optional): Name of the satellite constellation. Default to ``"Sentinel-2"``.
            processinglevel (str, optional): Level of processing, product quality. Default to ``"Level-2A"``.
            cloudcoverpercentage (str, optional): Range of cloud percentage. Default to ``(0, 10)``.
            resolution (int, optional): The level of resolution. Options available are: ``10``, ``20``, ``60``.
                Defaults to ``10``.
            bandname (str, optional): The name of the band to pick. See Sentinel documentation for more details. 
                Defaults to ``"TCI"``.
            out_dir (str, optional): Output directory where the retrieved images will be saved. Defaults to ``"sentinel"``.
            kwargs: Other options from `SentinelHub <https://docs.sentinel-hub.com/api/latest/>`__ API.

        Returns:
            list: List of path corresponding to downloaded files.

        Examples:
            First, connect to the API with your ``username`` and ``password``:

            >>> api = SentinelHubAPI(username, password)
            
            Then, download images within a bounding box and a a time range:
            
            >>> bbox = (50, 7, 51, 8)
            >>> date = ("20200920", "20200925")
            >>> files = api.download(bbox, date=date)
        """
        # Connect to the main API
        logger.info(f"Connecting to SentinelHub API...")
        api = SentinelAPI(self.username, self.password, self.url)
        logger.info("Successfully connected.")

        # Retrieve the area of interest in WKT format
        lon_min, lat_min, lon_max, lat_max = bbox
        footprint = f"POLYGON(({lat_max} {lon_min},{lat_min} {lon_min},{lat_min} {lon_max},{lat_max} {lon_max},{lat_max} {lon_min}))"

        # Make date range
        if date is None:
            datemin = datetime.now().strftime("%Y%m%d")
            datemax = datetime.now().strftime("%Y%m%d")
        elif isinstance(date, (tuple, list)):
            datemin, datemax = date
        else:
            datemin = date
            datemax = date

        # Make a request
        query_string = f"footprint={footprint}, date={datemin, datemax}, " + ", ".join([f"{key}={value}" for key, value in kwargs.items()])
        logger.info(f"Retrieving products for the query: {query_string}.")
        products = api.query(
            footprint,
            date=(datemin, datemax),
            platformname=platformname,
            processinglevel=processinglevel,
            cloudcoverpercentage=cloudcoverpercentage,
            **kwargs
        )
        logger.info("Products successfully retrieved.")
        products_gdf = api.to_geodataframe(products)
        logger.info(f"There are {len(products_gdf)} products found.")
        if products_gdf.empty:
            return None

        # Create the output directory if it does not exist
        out_dir_cache = Path(out_dir).parent / f".{Path(out_dir).name}"
        Path(out_dir_cache).mkdir(parents=True, exist_ok=True)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading the products to cache directory {out_dir_cache}.")

        # Download all results from the search in a cache folder
        for product_id in products_gdf.index:
            api.download(product_id, out_dir_cache)

        # Unzip the image folders
        logger.info(f"Extracting the products to directory {out_dir_cache}.")
        self.extract_all(out_dir_cache, out_dir_cache)

        # Move the images at `resolution`
        out_files = []
        logger.info(f"Transferring the images at resolution={resolution}, bandname={bandname} to directory {out_dir}.")
        for product_name in products_gdf.title:
            product_path = Path(out_dir_cache) / product_name
            image_file = self.find_image(product_path, resolution=resolution, bandname=bandname)
            # Move/copy the image to the main directory
            out_image = Path(out_dir) / Path(image_file).name
            copyfile(str(image_file), str(out_image))
            out_files.append(str(out_image))

        return out_files

    @staticmethod
    def extract_all(in_dir, out_dir=None):
        """Extract all downloaded zipped files in a directory.

        Args:
            in_dir (str): Path to the directory containing compressed files.
            out_dir (str, optional): Path to the output directory, containing uncompressed files. 
                Defaults to ``None``.
        """
        out_dir = out_dir or in_dir
        # Extract all files in a directory
        for file in Path(in_dir).iterdir():
            filename = str(file)
            if zipfile.is_zipfile(filename):
                zipfile.ZipFile(filename, 'r').extractall(out_dir)
            # Delete the zip file to keep only the content
            file.unlink()

    @staticmethod
    def find_image(product_path, resolution=10, bandname="TCI"):
        """Retrieve an image from a Sentinel product.

        Args:
            product_path (str): Path to the product folder. This folder must be unzipped.
            resolution (int, optional): Resolution of the image. Options are ``10``, ``20`` or ``60``. 
                Defaults to ``10``.
            bandname (str, optional): Name of the band. Multiple options are available, please refers to Sentinel documentation.
                Defaults to ``"TCI"``.

        Returns:
            str: Path to the image.
        """
        product_dir = Path(product_path).parent
        product_name = Path(product_path).name
        granule_dir = product_dir / f"{product_name}.SAFE" / "GRANULE"

        for res_dir in granule_dir.iterdir():
            image_dir = res_dir / "IMG_DATA" / f"R{resolution}m"
            for image_file in image_dir.iterdir():
                if image_file.stem.endswith(f"{bandname.upper()}_{resolution}m"):
                    return str(image_file)
