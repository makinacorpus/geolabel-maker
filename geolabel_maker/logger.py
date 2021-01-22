# Encoding: UTF-8
# File: logger.py
# Creation: Sunday January 10th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handles log with the ``logging`` package.

.. note::
    The ``Logger`` class is just used to wrap the ``logging.Logger`` one,
    with predefined parameters.
"""

# Basic imports
import logging


logging.basicConfig(
    filename="geolabel_maker.log",
    filemode="a",
    format="%(asctime)s :: %(name)-20s :: [%(levelname)-7s] :: %(message)s",
    level=logging.INFO
)

logger = logging.getLogger("geolabel_maker")
