# Encoding: UTF-8
# File: test_dataset.py
# Creation: Monday January 4th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


from pathlib import Path


def rm_tree(dirname):
    """Remove recursively all files and folders in a directory path.

    Args:
        dirname (str or Path): Path to the directory to remove.
    """
    if Path(dirname).is_dir():
        for child in Path(dirname).iterdir():
            if child.is_file():
                child.unlink()
            else:
                rm_tree(child)
        Path(dirname).rmdir()
