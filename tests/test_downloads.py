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
from geolabel_maker.downloads import SentinelHubAPI, MapBoxAPI, OverpassAPI


# Global variables
# USERNAME = getpass("SciHub Username: ")
# PASSWORD = getpass("SciHub Password: ")
# MAPBOX_TOKEN = getpass("MapBox Token: ")
BBOX = (50.9, 7.9, 51, 8)
DATE = ("20200920", "20200925")


class SentinelHubAPITests(unittest.TestCase):

    def test_01_connect(self):
        pass

    def test_02_download(self):
        pass


class MapBoxAPITests(unittest.TestCase):

    def test_01_connect(self):
        pass

    def test_02_download(self):
        pass


class OverpassAPITests(unittest.TestCase):

    def test_01_connect(self):
        pass

    def test_02_download(self):
        pass


if __name__ == '__main__':
    unittest.main()
