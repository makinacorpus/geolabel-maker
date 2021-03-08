# Encoding: UTF-8
# File: logger.py
# Creation: Sunday January 10th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handles log with the ``logging`` package.

.. note|
    The ``Logger`` class is just used to wrap the ``logging.Logger`` one,
    with predefined parameters.
"""

# Basic imports
import logging
import sys


# GLobal variables
FILE_FORMATTER = logging.Formatter("%(asctime)s :: %(name)s :: [%(levelname)-7s] :: %(filename)s:%(lineno)s :: %(funcName)s() :: %(message)s")
STREAM_FORMATTER = logging.Formatter("[%(levelname)-7s] %(message)s")


def get_logger(name, logfile=None, level=10, stream_level=20, file_level=0):
    # Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(stream_level)

    # Add logs to the file at level `file_level`
    logfile = logfile or f"{name}.log"
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(FILE_FORMATTER)
    file_handler.setLevel(file_level)
    
    # Add logs to the console at level `stream_level`
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)
    stream_handler.setFormatter(STREAM_FORMATTER)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = get_logger("geolabel_maker")
