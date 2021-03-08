# Encoding: UTF-8
# File: overpass.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handles geometries retrieval from the `Overpass` API.
It is part of the `Open Street Map` API, but for large queries and requests.

.. code-block:: python

    from geolabel_maker.vectors.downloads import OverpassAPI
    
    bbox = (40, 50, 41, 51)
    api = OverpassAPI()
    map = api.download(bbox, selector="buildings" out_file="buildings.json")
"""


# Basic imports
import re
import requests
from pathlib import Path
from osmtogeojson import osmtogeojson
import geopandas as gpd
from shapely.geometry import Polygon

# Geolabel Maker
from geolabel_maker.logger import logger
from .downloader import Downloader


__all__ = [
    "OverpassAPI"
]


class OverpassAPI(Downloader):
    r"""
    Defines the `Overpass <http://overpass-api.de/api/interpreter>`__ API.

    * :attr:`url` (str): URL used to connect to the API.

    """

    def __init__(self):
        url = "http://overpass-api.de/api/interpreter"
        super().__init__(url)

    def download(self, bbox, selector="building", timeout=700, out_file=None):
        """Download OSM data from the API. 
        A ``selector`` can be used to retrieve specific areas / regions of interests.

        Args:
            bbox (tuple): Bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            selector (str, optional): Seclector used to retrieve parts of data. This could be buildings, offices, farms etc.
                See the OSM documentation for more details of the available options.
                Defaults to ``'"building"'``.
            out_file (str, optional): Name of the downloaded file (in ``json`` / ``geojson`` extension).
                If ``None``, the file will be named as ``map_{timestamp}.geojson``. Default to ``None``.

        Returns:
            str: Path to the downloaded file.

        Examples:
            >>> api = OverpassAPI()
            >>> api.download((48.0, 2.0, 48.1, 2.1), selector="building", out_file="buildings.json")
        """
        logger.info(f"Downloading geometries for selector '{selector}'.")

        lon_min, lat_min, lon_max, lat_max = bbox
        query = f"""
            [out:json][timeout:{timeout}];
            (relation[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            way[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            );
            out body;
            >;
            out skel qt;
        """
        query_string = re.sub(" +", "", query.replace("\n", " "))
        logger.debug(f"Making a query to overpass: '{query_string}'.")

        # Connect to Overpass API
        response = requests.get(
            self.url,
            params={'data': query}
        )
        json_data = response.json()

        # TODO: only delete unwanted tags.
        for element in json_data['elements']:
            element.pop('tags', None)

        # Return the response as a geojson dict
        logger.debug("Converting the features to GeoJSON.")
        features = osmtogeojson.process_osm_json(json_data)

        if out_file is None:
            selector_unicode = re.sub("[^a-zA-Z_-]", "_", selector)
            out_file = f"{selector_unicode}_{int(lon_min)}_{int(lat_min)}_{int(lon_max)}_{int(lat_max)}.geojson"
        elif not Path(out_file).suffix.lower() in [".json", ".geojson"]:
            out_file = f"{out_file}.json"

        # Save
        df = gpd.GeoDataFrame.from_features(features)
        if df.empty:
            logger.debug(f"The data is empty. Skipping the saving process.")
            return None
        # Removing geometries other than polygons
        logger.debug("Removing geometries other than 'Polygon'.")
        df = df[df["geometry"].apply(lambda x: isinstance(x, Polygon))]
        # Saving
        Path(out_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_file(out_file, driver="GeoJSON")
        logger.debug(f"OSM geometries successfully saved at {out_file}.")
        return out_file
