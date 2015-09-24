# examples/game.py
# Lillian Lemmer <lillian.lynn.lemmer@gmail.com>
#
# This module is part of Hypatia and is released under the
# MIT license: http://opensource.org/licenses/MIT

"""This is a game demo which showcases Hypatia's features.

"""

from hypatia import game

__author__ = "Lillian Lemmer"
__copyright__ = "Copyright 2015, Lillian Lemmer"
__credits__ = ["Lillian Lemmer"]
__license__ = "MIT"
__maintainer__ = "Lillian Lemmer"
__email__ = "lillian.lynn.lemmer@gmail.com"
__status__ = "Development"


# should be in settings.ini?
VIEWPORT_X, VIEWPORT_Y = 100, 70


# init
viewport_size = (VIEWPORT_X, VIEWPORT_Y)
scene = game.Scene.from_tmx_resource('debug')
game = game.Game(scene=scene, viewport_size=viewport_size)
game.start_loop()
