# Encoding: UTF-8
# File: download.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handles geometries retrieval from the `Overpass` API.
It is part of the `Open Street Map` API, but for large queries and requests.

.. code-block:: python

    from geolabel_maker.vectors.download import OverpassAPI
    
    bbox = (40, 50, 41, 51)
    api = OverpassAPI()
    map = api.download(bbox, selector="buildings" outfile="buildings.json")
"""


# Basic imports
import requests
from datetime import datetime
from osmtogeojson import osmtogeojson
import geopandas as gpd

# Geolabel Maker
from geolabel_maker.logger import logger


__all__ = [
    "OverpassAPI"
]


class OverpassAPI:
    r"""
    Defines the `Overpass <http://overpass-api.de/api/interpreter>`__ API.

    * :attr:`url` (str): URL used to connect to the API.

    """

    def __init__(self):
        self.url = "http://overpass-api.de/api/interpreter"

    def download(self, bbox, selector='"building"', timeout=700, outfile=None):
        """Download OSM data from the API. 
        A ``selector`` can be used to retrieve specific areas / regions of interests.

        Args:
            bbox (tuple): Bounding box in the format :math:`(lat_{min}, lon_{min}, lat_{max}, lon_{max})`.
            selector (str, optional): Seclector used to retrieve parts of data. This could be buildings, offices, farms etc.
                See the OSM documentation for more details of the available options.
                Defaults to ``'"building"'``.
            outfile (str, optional): Name of the downloaded file (in ``json`` / ``geojson`` extension).
                If ``None``, the file will be named as ``map_{timestamp}.geojson``. Default to ``None``.

        Returns:
            str: Path to the downloaded file.

        Examples:
            >>> from geolabel_maker.vectors import OverpassAPI
            >>> api = OverpassAPI()
            >>> api.download((48.0, 2.0, 48.1, 2.1), selector="building", outfile="buildings.json")
        """
        lat_min, lon_min, lat_max, lon_max = bbox
        query = f"""
            [out:json][timeout:{timeout}];
            (relation[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            way[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            );
            out body;
            >;
            out skel qt;
        """
        logger.info(f"Making a query to overpass: {query}")

        # Connect to Overpass API
        response = requests.get(
            self.url,
            params={'data': query}
        )
        json_data = response.json()

        # Remove tags
        # TODO: only delete unwanted tags.
        for element in json_data['elements']:
            element.pop('tags', None)

        # Return the response as a geojson dict
        logger.info("Converting the features to GeoJSON.")
        features = osmtogeojson.process_osm_json(json_data)

        if outfile is None:
            date = int(datetime.now().timestamp())
            outfile = f"map_{date}.geojson"
        elif not outfile.lower().endswith(".json") or \
                not outfile.lower().endswith(".geojson"):
            outfile += ".json"

        # Save
        logger.info(f"Saving the data at '{outfile}'.")
        df = gpd.GeoDataFrame.from_features(features)
        df.to_file(outfile, driver="GeoJSON")
        logger.info("OSM geometries successfully saved.")
        return outfile
