# Encoding: UTF-8
# File: test_dataset.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import unittest
from getpass import getpass

# Geolabel Maker
from geolabel_maker.download import OverpassAPI, SentinelHubAPI


# Global variables
USERNAME = getpass("SciHub Username: ")
PASSWORD = getpass("SciHub Password: ")
BBOX = (50.9, 7.9, 51, 8)
DATE = ("20200920", "20200925")


class DownloadTests(unittest.TestCase):

    def test_0_sentinelhub(self):
        api = SentinelHubAPI(USERNAME, PASSWORD)
        rasters = api.download(BBOX, date=DATE)

    def test_1_overpass(self):
        api = OverpassAPI()
        geometry = api.download(BBOX)


if __name__ == '__main__':
    unittest.main()
