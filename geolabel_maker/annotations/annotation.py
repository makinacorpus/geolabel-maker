# Encoding: UTF-8
# File: annotations.py
# Creation: Monday December 28th 2020
# Author: arthurdjn
# ------
# Copyright (c) 2020, Makina Corpus


r"""
Defines annotation datasets i.e. the final step of `geolabel-maker` workflow.    
"""

# Basic imports
from abc import ABC
import json
from pathlib import Path

# Geolabel Maker
from geolabel_maker.data import Data


class Annotation(Data):
    r""":badge:`abstract,badge-secondary badge-pill`
    Abstract class defining the structure of an annotation dataset.

    """

    def __init__(self):
        super().__init__()

    @classmethod
    def from_dataset(cls, dataset, *args, **kwargs):
        raise NotImplementedError

    def to_dict(self, **kwargs):
        r"""Convert the annotation to a dictionary (JSON encoded)."""
        raise NotImplementedError

    def save(self, outfile=None, encoding="utf-8", indent=4):
        r"""Save the annotation in JSON format.

        Args:
            outfile (str): Path to the output file.
            encoding (str, optional): Encoding mode. Defaults to ``"utf-8"``.
            indent (int, optional): Indent used to format the JSON file. Defaults to ``4``.

        Returns:
            str: Path to the saved file.
        """
        # Make sure the file is a JSON
        if not outfile:
            outfile = "annotation.json"
        if not str(outfile).endswith(".json"):
            outfile = str(outfile) + ".json"
        # Save the annotation
        with open(outfile, "w", encoding=encoding) as f:
            json.dump(self.to_dict(), f, indent=indent)
        return str(Path(outfile))
