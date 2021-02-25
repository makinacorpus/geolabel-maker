# Encoding: UTF-8
# File: utils.py
# Creation: Tuesday February 23rd 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from math import log, tan, radians, cos, pi, floor, degrees, atan, sinh


def sec(radian):
    """Get the seconds from a radian angle.

    Args:
        radian (float): Angle (latitude, longitude) in radians.

    Returns:
        float
    """
    return 1 / cos(radian)


def latlon2xyz(lat, lon, z):
    """Convert latitudes and longitudes (in degrees) to slippy maps coordinates.

    Args:
        lat (float): Latitude, in degrees.
        lon (float): Longitude, in degres.
        z (int): Zoom level.

    Returns:
        x, y
    """
    tile_count = 2 ** z
    x = (lon + 180) / 360
    y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return floor(tile_count * x), floor(tile_count * y)


def bbox2xyz(lon_min, lat_min, lon_max, lat_max, z):
    """Convert a bounding box in :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})` format
    to :math:`(x_{min}, y_{min}, x_{max}, y_{max})`.

    Args:
        lon_min (float): Minimum longitude, in degrees.
        lat_min (float): Minimum latitude, in degrees.
        lon_max (float): Maximum longitude, in degrees.
        lat_max (float): Maximum latitude, in degrees.
        z (int): Zoom level.

    Returns:
        tuple
    """
    x_min, y_max = latlon2xyz(lat_min, lon_min, z)
    x_max, y_min = latlon2xyz(lat_max, lon_max, z)
    return x_min, y_min, x_max, y_max


def mercator2lat(mercator_y):
    """Retrieve the latitude from a :math:`y` coordinate in the mercator projection.

    Args:
        mercator_y (float): Mercator vertical position.

    Returns:
        float
    """
    return degrees(atan(sinh(mercator_y)))


def yz2bounds(y, z):
    """Retrieve latitudes of the edges for a given tile.

    Args:
        y (int): Y coordinate for slippy maps systems.
        z (int): Zoom level.

    Returns:
        tuple: Latitudes of the edge.
    """
    tile_count = pow(2, z)
    unit = 1 / tile_count
    relative_y1 = y * unit
    relative_y2 = relative_y1 + unit
    lat1 = mercator2lat(pi * (1 - 2 * relative_y1))
    lat2 = mercator2lat(pi * (1 - 2 * relative_y2))
    return lat1, lat2


def xz2bounds(x, z):
    """Retrieve longitudes of the edges for a given tile.

    Args:
        x (int): X coordinate for slippy maps systems.
        z (int): Zoom level.

    Returns:
        tuple: Longitudes of the edge.
    """
    tile_count = pow(2, z)
    unit = 360 / tile_count
    lon1 = -180 + x * unit
    lon2 = lon1 + unit
    return lon1, lon2


def xyz2bounds(x, y, z):
    """Retrieve longitudes and latitudes of the edges for a given tile.

    Args:
        x (int): X coordinate for slippy maps systems.  
        y (int): Y coordinate for slippy maps systems.
        z (int): Zoom level.

    Returns:
        tuple
    """
    lat1, lat2 = yz2bounds(y, z)
    lon1, lon2 = xz2bounds(x, z)
    return lon1, lat1, lon2, lat2
