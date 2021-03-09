# Encoding: UTF-8
# File: color.py
# Creation: Saturday January 9th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
This module handle color conversion and manipulation.

.. code-block:: python

    from geolabel_maker.vectors import Color
    
    # 1. Create a RGB color
    color = Color(red=200, green=23, blue=156)
    
    # 2. Create a color from another format
    color = Color.get("green")
    color = Color.get((0, 255, 0))
    color = Color.get("#fcfcfc")
    # etc...

    # 3. Convert a color to RGB
    rgb = color.to_rgb()

    # 4. Convert a color to hex
    hex = color.to_hex()
"""


# Basic imports
from PIL import ImageColor
import random

# Global variables
SEED = 2021
random.seed(SEED)


__all__ = [
    "Color"
]


class Color:
    r"""
    A color is a radiometry in RGB format :math:`(R, G, B)`. 
    The red, green, blue values must be in the range :math:`[0, 255]`.
    This class is mainly used to store and process colors from other formats (e.g. strings, hex codes, alphas etc).

    * :attr:`red` (int): Value for the :math:`R` channel.

    * :attr:`green` (int): Value for the :math:`G` channel.

    * :attr:`blue` (int): Value for the :math:`B` channel.

    .. note::
        If you are not sure how to create a ``Color`` object, 
        you may want to use the ``Color.get()`` method, which format various types of colors.

    """

    def __init__(self, red, green, blue):
        # Make sure the given values follow RGB format
        if (not isinstance(red, int)) or (not isinstance(green, int)) or (not isinstance(blue, int)):
            raise ValueError(f"Cannot convert RGB Color from not integer values. Got {red, green, blue}")
        elif (red > 255 or red < 0) or (green > 255 or green < 0) or (blue > 255 or blue < 0):
            raise ValueError(f"RGB values must be in the range [0, 255]. Got {red, green, blue}.")

        self.red = red
        self.green = green
        self.blue = blue

    @classmethod
    def get(cls, element):
        """Creates a color object from different input types. 
        The accepted formats are name, hexvalues, or RGBA.
        
        .. seealso::
            This method relies on ``PIL.ImageColor.getcolor()`` method.

        Args:
            element (any): The object used to create the color.

        Returns:
            Color: The color in RGB format.
            
        Examples:
            >>> color = Color.get("green")
            >>> color = Color.get("skyblue")
            >>> color = Color.get("#2f2f2f")
            >>> color = Color.get((.2, .4, .8))
            >>> color = Color.get((.2, .4, .8, 1.))
            >>> color = Color.get((23, 34, 139))
        """
        if isinstance(element, str):
            red, green, blue = ImageColor.getcolor(element, "RGB")
            return Color(red, green, blue)

        elif isinstance(element, (list, tuple, Color)):
            assert len(element) >= 3, f"Not enough values to unpack RGB elements. Got {element}."
            red, green, blue = element[:3]

            # If the RGB values are given in the range [0, 1] scale them to [0, 255]
            is_red_float = isinstance(red, float) and red <= 1
            is_green_float = isinstance(green, float) and green <= 1
            is_blue_float = isinstance(blue, float) and blue <= 1
            if is_red_float and is_green_float and is_blue_float:
                red = red * 255
                green = green * 255
                blue = blue * 255

            # Make sure the values are between 0-255
            red = max(min(int(red), 255), 0)
            green = max(min(int(green), 255), 0)
            blue = max(min(int(blue), 255), 0)
            return Color(red, green, blue)

        else:
            raise ValueError(f"Cannot convert the element of type {type(element)} to RGB Color.")

    @classmethod
    def random(cls):
        """Generates a random color.
        
        .. seealso::
            This method relies on ``random`` package. To control the generated colors,
            please refer to ``random.seed()`` function.

        Returns:
            Color: The random color.
        """
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return Color(red, green, blue)

    def to_rgb(self):
        """Converts the color to a tuple of RGB values.

        Returns:
            tuple: The red, green and blue values.
            
        Examples:
            >>> color = Color.get("green")
            >>> rgb = color.to_rgb()
        """
        return (self.red, self.green, self.blue)

    def to_hex(self):
        """Converts a color to a hex format.

        Returns:
            str: The color in a hex representation.
            
        Examples:
            >>> color = Color.get("green")
            >>> hex = color.to_hex()
        """
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"

    def __iter__(self):
        yield from self.to_rgb()

    def __getitem__(self, index):
        return self.to_rgb()[index]

    def __len__(self):
        return len(self.to_rgb())

    def __repr__(self):
        return f"Color(red={self.red}, green={self.green}, blue={self.blue})"
