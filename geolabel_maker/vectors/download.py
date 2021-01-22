# Encoding: UTF-8
# File: download.py
# Creation: Sunday January 3rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import requests
import osmtogeojson
import json


__all__ = [
    "OverpassAPI"
]


class OverpassAPI:

    def __init__(self):
        self.url = "http://overpass-api.de/api/interpreter"

    def download(self, bbox, selector="building", outfile="map.geojson", tags="buildings"):
        """Download OSM data from `Overpas API <http://overpass-api.de/api/interpreter>`__.

        Args:
            bbox (tuple): Bounding box in the format :math:`(lat_{min}, lon_{min}, lat_{max}, lon_{max})`.
            selector (str): Seclector used to retrieve parts of data. This could be buildings, offices, farms etc.
                See the OSM documentation for more details of the available options.
            outfile (str): Name of the downloaded file (in ``json`` / ``geojson`` extension).

        Returns:
            dict: GeoJson of feature collections.

        Examples:
            >>> from geolabel_maker.vectors import OverpassAPI
            >>> api = OverpassAPI()
            >>> api.download((48.0, 2.0, 48.1, 2.1), selector="building", outfile="buildings.json")
        """
        lat_min, lon_min, lat_max, lon_max = bbox
        query = f"""
            [out:json][timeout:25];
            (relation[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            way[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            node[{selector}]({lat_min},{lon_min},{lat_max},{lon_max});
            );
            out body;
            >;
            out skel qt;
        """
        # Connect to Overpass API
        response = requests.get(
            self.url,
            params={'data': query}
        )
        # Return the response as a geojson dict
        geojson = osmtogeojson.process_osm_json(response.json())
        with open(outfile, "w") as f:
            json.dump(geojson, f, indent=4)
