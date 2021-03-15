# Encoding: UTF-8
# File: utils.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
import os.path
from pathlib import Path


def relative_path(path, root=None):
    """Get the relative path between two paths.

    Args:
        path (str): Main path.
        root (str, optional): Root path. Defaults to ``None``.

    Returns:
        str: The relative path ``path`` from ``root``.
        
    Examples:
        >>> path = "some/other/directory/dataset.json"
        >>> root = "some/other"
        >>> relative_path(path, root=root)
            "directory/dataset.json"
    """
    if not path:
        return None
    root = root or "."
    root_abs = Path(root).resolve()
    path_abs = Path(path).resolve()
    return os.path.relpath(path_abs, start=root_abs)


def retrieve_path(path, root=None):
    """Retrieve a path from a root directory.
    This method is the inverse of ``relative_paths``.

    Args:
        path (str): Path to retrieve.
        root (str, optional): Root directory. If ``None``, the root is the working direcotry. 
            Defaults to ``None``.

    Returns:
        str: The relative path ``path`` from the working directory.
        
    Examples:
        >>> path = "directory/dataset.json"
        >>> root = "some/other"
        >>> retrieve_path(path, root=root)
            "some/other/directory/dataset.json"
    """
    root = root or "."
    if not path:
        return None
    elif Path(path).is_absolute():
        return str(Path(path))
    else:
        return relative_path(Path(root) / path, root=Path(".").resolve())