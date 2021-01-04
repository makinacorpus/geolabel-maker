# Encoding: UTF-8
# File: download.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from pathlib import Path
import zipfile
import os


def unzip_all(dirname):
    # get the list of files
    for file in os.listdir(dirname):
        # if it is a zipfile, extract it
        if zipfile.is_zipfile(file):
            # treat the file as a zip
            with zipfile.ZipFile(file) as item:
                # extract it in the same directory
                item.extractall()


def download(username,
             email,
             bbox,
             date_min,
             date_max,
             platformname="Sentinel-2",
             cloudcoverpercentage=(0, 30),
             outdir="sentinel"):
    # Connect to the API
    api = SentinelAPI(username, email, 'https://scihub.copernicus.eu/dhus')
    footprint = f"{bbox}"
    products = api.query(footprint,
                         date=(date_min, date_max),
                         platformname=platformname,
                         cloudcoverpercentage=cloudcoverpercentage)
    products_gdf = api.to_geodataframe(products)
    print(f"There are {len(products_gdf)} products found.")
    # Create the output directory if it does not exist
    Path(outdir).mkdir(parents=True, exist_ok=True)
    # Download all results from the search
    api.download_all(products, outdir)
    # Unzip the images
    unzip_all(outdir)

    return True
