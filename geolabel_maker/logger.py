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


# GLobal variables
FORMATTER = logging.Formatter("%(asctime)s :: %(name)-20s :: [%(levelname)-7s] :: %(message)s")


def setup_logger(name, logfile, level=logging.INFO):

    handler = logging.FileHandler(logfile)        
    handler.setFormatter(FORMATTER)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logger("geolabel_maker", "geolabel_maker.log")
