"""Physical attributes of things.

Right now, not much differs it from the constants
module, but there will surely be much more to do
with physics as time progresses.

See Also:
    :mod:`constants`

"""

import pygame

from hypatia import constants


class Velocity(object):
    """Eight-directional velocity."""

    def __init__(self, x=0, y=0):
        """Speed in pixels per second per axis. Values may be negative.

        Args:
          x (int|None): --
          y (int|None): --

        """

        self.x = x
        self.y = y


class AbsolutePosition(object):
    """The position of an object. This is the physical data
    representative of an object. A sprite's position for
    rendering is a separate concept.

    Uses floats for frame and pixel
    independent movement adjustments.

    Attributes:
        float_x (float): --
        float_y (float): --

    """

    def __init__(self, float_x, float_y):
        """Extrapolate position info from supplied info.

        Arguments:
          float_x (float): how many pixels from the left of the scene.
          float_y (float): how many pixels from the top of the scene.

        """

	# because people just manage to use integers anyway
	# i myself am guilty of wondering why a bug was
	# occuring when it was because i passed an int
        self.float_x = float(float_x)
        self.float_y = float(float_y)

    def x_y(self):

        return (self.float_x, self.float_y)

    # NOTE: may have a bug related to division in Python 2. No
    # such bug in python 3.
    def relative(self, viewport):
        """Return this absolute position's position relative
        to the viewport/screen, or anything else
        with the "rect.topleft" attribute.

        Arguments:
            viewport (render.Viewport): --

        Returns:
            tuple: (x, y) tuple representing this object's position
                relative to the screen.
        """

        offset_x, offset_y = viewport.rect.topleft
        new_float_x = self.float_x - offset_x
        new_float_y = self.float_y - offset_y

        return (new_float_x, new_float_y)
