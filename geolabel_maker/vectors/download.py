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


def download(bbox, selector="building"):
    south, west, north, east = bbox
    query = f"""
        [out:json][timeout:25];
        (relation[{selector}]({south},{west},{north},{east});
        way[{selector}]({south},{west},{north},{east});
        node[{selector}]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
    """
    # Connect to Overpass API
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(
        url,
        params={'data': query}
    )
    # Return the response as a geojson dict
    return osmtogeojson.process_osm_json(response.json())
