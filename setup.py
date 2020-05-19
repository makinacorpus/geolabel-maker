#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from importlib import import_module

VERSION = import_module("geolabel_maker").__version__

setup(
    name='geolabel_maker',
    keywords=[
        "geospatial artificial intelligence",
        "deep learning",
        "convolutional neural networks",
        "image",
        "ground truth"
    ],
    version=VERSION,
    packages=find_packages(),
    author="Makina Corpus",
    author_email="contact@makina-corpus.com",
    maintainer="Makina Corpus",
    description="Data preparation for geospatial artificial intelligence",
    long_description=open('README.md').read(),
    include_package_data=True,
    url='https://github.com/makinacorpus',
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
            "geolabels = geolabel_maker.geolabels:main.start",
        ]
    },
    python_requires='>=3.6',
    install_requires=[
        'begins==0.9',
        'numpy==1.18.1',
        'gdal2tiles==0.1.6',
        'geopandas==0.6.1',
        'rasterio==1.1.3',
        'matplotlib==3.1.3',
        'scikit-image==0.16.2',
    ],
)
