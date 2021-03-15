# Encoding: UTF-8
# File: setup.py
# Creation: Monday December 28th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
from setuptools import setup, find_packages


# Global variables
from geolabel_maker.version import __version__


setup(
    name="geolabel_maker",
    keywords=[
        "geospatial artificial intelligence",
        "deep learning",
        "satellite images",
        "vector geometries",
        "annotations",
        "ground truth"
    ],
    version=__version__,
    packages=find_packages(),
    author="Arthur Dujardin, Lucie Camanez, Daphne Lercier",
    author_email="contact@makina-corpus.com",
    maintainer="Makina Corpus",
    description="Data preparation for geospatial artificial intelligence",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://github.com/makinacorpus/geolabel-maker/",
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    entry_points={
        "console_scripts": [
            "geolabel_maker = geolabel_maker.main:main",
        ]
    },
    python_requires=">=3.6",
    install_requires=[
        "gdal2tiles",
        "geopandas",
        "matplotlib",
        "numpy",
        "pandas",
        "sentinelsat",
        "osmtogeojson",
        "opencv-python",
        "pillow",
        "pyproj",
        "rasterio",
        "requests", 
        "shapely",
        "tqdm",
    ],
)
