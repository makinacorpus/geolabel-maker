# Encoding: UTF-8
# File: downloader.py
# Creation: Tuesday February 23rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from abc import ABC, abstractmethod


class Downloader(ABC):
    r"""
    Defines an abstract skeleton for all downloader.
    
    * :attr:`url` (str): The url of the API.

    """

    def __init__(self, url):
        super().__init__()
        self.url = url

    @abstractmethod
    def download(self, bbox, *args, **kwargs):
        """Download data from an API.

        Args:
            bbox (tuple): Bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
        """
        raise NotImplementedError
