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
from geolabel_maker.rasters import Raster
from geolabel_maker.rasters.download import SentinelHubAPI
from geolabel_maker.vectors import Category
from geolabel_maker.vectors.download import OverpassAPI


# Global variables
USERNAME = getpass("SciHub Username: ")
PASSWORD = getpass("SciHub Password: ")
BBOX = (50, 7, 51, 8)
DATE_MIN = "20200920"
DATE_MAX = "20200925"


class DownloadTests(unittest.TestCase):

    def test_0_sentinelhub(self):
        api = SentinelHubAPI(USERNAME, PASSWORD)
        rasters = api.download(BBOX)

    def test_1_raster(self):
        rasters = Raster.download(USERNAME, PASSWORD, BBOX, date_min=DATE_MIN, date_max=DATE_MAX)

    def test_2_overpass(self):
        api = OverpassAPI()
        geometry = api.download(BBOX)

    def test_3_category(self):
        geometry = Category.download(BBOX)


if __name__ == '__main__':
    unittest.main()
