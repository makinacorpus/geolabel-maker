#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

setup(
    name='geolabel_maker',
    keywords=[
        "geospatial artificial intelligence",
        "deep learning",
        "convolutional neural networks",
        "image",
        "ground truth"
    ],
    version=open(os.path.join(HERE, "geolabel_maker", "VERSION.md")).read().strip(),
    packages=find_packages(),
    author="Makina Corpus",
    author_email="contact@makina-corpus.com",
    maintainer="Makina Corpus",
    description="Data preparation for geospatial artificial intelligence",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    url='https://github.com/makinacorpus/geolabel-maker/',
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
        'numpy',
        'gdal2tiles',
        'shapely',
        'geopandas',
        'rasterio',
        'pillow',
        'scikit-image',
        'requests',
        'sentinelsat'
    ],
)
