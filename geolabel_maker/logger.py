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


class LoggerFormatter(logging.Formatter):
    r"""
    A custom ``Formatter``. Used to display a log as:
    ``2020-07-14 15:54:40,763 :: geolabel_maker         :: [DEBUG   ] :: debug message``.
    .. note::
        This formatter will align the logs.
    Examples:
        >>> logger = Logger()
        >>> logger.debug('debug message')
        >>> logger.info('info message')
        >>> logger.warning('warn message')
        >>> logger.error('error message')
        >>> logger.critical('critical message')
            2020-07-14 15:54:40,763 :: geolabel_maker :: [DEBUG   ] :: debug message
            2020-07-14 15:54:40,766 :: geolabel_maker :: [INFO    ] :: info message
            2020-07-14 15:54:40,767 :: geolabel_maker :: [WARNING ] :: warn message
            2020-07-14 15:54:40,769 :: geolabel_maker :: [ERROR   ] :: error message
            2020-07-14 15:54:40,772 :: geolabel_maker :: [CRITICAL] :: critical message
    """

    # From https://stackoverflow.com/questions/36763438/how-to-add-alignment-to-python-standart-logger-if-i-use-loglevel/36807267
    levelwidth = 8

    def format(self, record):
        """Format a log message.

        Args:
            record (logging.Record): a record from a specific log.

        Returns:
            str: pretty log.
        """
        # Format the logger's name
        name = record.name
        # Format the log's level
        levelname = record.levelname
        levelpad = "".ljust(self.levelwidth - len(levelname))
        # Add time
        time = self.formatTime(record, self.datefmt)
        message = record.getMessage()
        # Return a padded / aligned log
        return f"{time} :: {name} :: [{levelname}{levelpad}] :: {message}"


class Logger(logging.Logger):
    r"""
    A ``Logger`` is a custom logging used to display / save pretty log message.
    It extends the ``logging.Logger`` class.

    """

    def __init__(self, name="geolabel_maker", level=10, **kwargs):
        r"""Extends the ``Logger`` class from ``logging`` package.

        Args:
            name (str): logger's name.
            level (int): level of log (debug, info, warning, error, critical).
        """
        super().__init__(name, level=level, **kwargs)
        # Log in the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        # Pretty logs
        formatter = LoggerFormatter()
        console_handler.setFormatter(formatter)
        # Add it to the logger
        self.addHandler(console_handler)

logging.basicConfig(filename='geolabel_maker.log')
logger = Logger("geolabel_maker", level=10)
