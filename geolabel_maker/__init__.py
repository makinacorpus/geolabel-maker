import os

from geolabel_maker.geolabels import (
    make_all,
    make_labels,
    make_rasters,
    make_tiles,
    make_annotations,
)

HERE = os.path.abspath(os.path.dirname(__file__))

__version__ = open(os.path.join(HERE, "VERSION.md")).read().strip()
__all__ = (make_all, make_labels, make_rasters, make_tiles, make_annotations)
