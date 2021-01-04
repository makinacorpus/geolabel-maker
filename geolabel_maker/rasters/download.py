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


def extract_to_dir(filename, outdir='.'):
    if zipfile.is_zipfile(filename):
        zipfile.ZipFile(filename, 'r').extractall(outdir)
    # Return the path where the file was extracted
    return str(Path(outdir) / Path(filename).stem)


def extract_all(indir, outdir='.'):
    # Extract all files in a directory
    for file in Path(indir).iterdir():
        extract_to_dir(str(file), outdir=outdir)
        # Delete the zip file to keep only the content
        file.unlink()


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
    extract_all(outdir, outdir)

    return outdir
