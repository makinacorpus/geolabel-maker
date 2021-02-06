# Encoding: UTF-8
# File: utils.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path


def retrieve_path(path, root=None):
    root = root or "."
    if not path:
        return None
    elif Path(path).is_absolute():
        return str(Path(root))
    else:
        return str(Path(root) / path)
