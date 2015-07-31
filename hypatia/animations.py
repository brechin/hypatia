# This module is part of Hypatia and is released under the
# MIT license: http://opensource.org/licenses/MIT

"""Tools for animation. Animation sources are GIFs from disk, which
have been made into a PygAnimation [1]_ object. Stateful animations
which represent objects, e.g., :class:`Walkabout` represents an
:class:`actor.Actor`.

Examples of "tools":

  * functions for creating an animation from a single suface
  * loading animations from disk
  * adding frame-dependent positional data
  * contextually-aware sprites

References:
    .. [1] PygAnim:
       http://inventwithpython.com/pyganim/

Warning:
    Sometimes an "animation" can consist of one frame.

Note:
    I wanna add support for loading character animations
    from sprite sheets.

See Also:

    * :mod:`util`
    * :mod:`actor`
    * :class:`Walkabout`

"""

import os
import copy
import glob
import itertools
import collections

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

import pygame
import pyganim
from PIL import Image

from hypatia import util
from hypatia import render
from hypatia import physics
from hypatia import constants


class BadWalkabout(Exception):
    """The supplied directory has no files which match ``*.gif.`` The
    walkabout resource specified does not contain any GIFs.

    See Also:
        :meth:`Walkabout.__init__`

    """

    def __init__(self, supplied_archive):
        """

        Args:
            supplied_archive (str): :class:`Walkabout` resource archive
                which *should* have contained files of pattern
                ``*.gif,`` but didn't.

        """

        super(BadWalkabout, self).__init__(supplied_archive)


class Anchor(object):
    """A coordinate on a surface which is used for pinning to another
    surface Anchor. Used when attempting to afix one surface to
    another, lining up their corresponding anchors.

    Attributes:
        x (int): x-axis coordinate on a surface to place anchor at
        y (int): x-axis coordinate on a surface to place anchor at

    Example:
        >>> anchor = Anchor(5, 3)
        >>> anchor.x
        5
        >>> anchor.y
        3

    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other_anchor):
        """Adds the x, y values of this and another anchor.

        Args:
            other_anchor (Anchor): The Anchor coordinates
                to add to this Anchor's coordinates.

        Returns:
            (x, y) tuple: the new x, y coordinate

        Example:
            >>> anchor_a = Anchor(4, 1)
            >>> anchor_b = Anchor(2, 0)
            >>> anchor_a + anchor_b
            (6, 1)

        """

        return (self.x + other_anchor.x,
                self.y + other_anchor.y)

    def __sub__(self, other_anchor):
        """Find the difference between this anchor and another.

        Args:
            other_anchor (Anchor): the Anchor
                coordinates to subtract from this
                AnchorPoint's coordinates.

        Returns:
            tuple: the (x, y) difference between this
                anchor and the other supplied.

        Example:
            >>> anchor_a = Anchor(4, 1)
            >>> anchor_b = Anchor(2, 0)
            >>> anchor_a - anchor_b
            (2, 1)

        """

        return (self.x - other_anchor.x,
                self.y - other_anchor.y)


class LabeledSurfaceAnchors(object):
    """Labeled anchors for a surface.

    """

    def __init__(self, anchors_config, frame_index):
        """The default is to simply load the anchors from
        the GIF's anchor config file.

        """

        self.labeled_anchors = {}

        for section in anchors_config.sections():
            anchor_for_frame = anchors_config.get(section, str(frame_index))
            x, y = anchor_for_frame.split(',')
            self.labeled_anchors[section] = Anchor(int(x), int(y))

    def __getitem__(self, label):

        return self.labeled_anchors[label]


class AnimatedSpriteFrame(object):
    """A frame of an AnimatedSprite animation.

    See Also:
        :method:`AnimatedSprite.frames_from_gif()`

    """


    def __init__(self, surface, start_time, duration, anchors=None):
        """

        Args:
            surface (pygame.Surface): The surface/image for this
                frame.
            duration (integer): Milleseconds this frame lasts.
            anchors (LabeledSurfaceAnchors): --

        """

        self.surface = surface
        self.duration = duration
        self.start_time = start_time
        self.end_time = start_time + duration
        self.anchors = anchors or None


class AnimatedSprite(pygame.sprite.Sprite):
    """Animated sprite with mask, loaded from GIF.

    Supposed to be mostly uniform with the Sprite API.

    Notes:
        This is replacing pyganim as a dependency. Currently,
        does not seem to draw. I assume this is a timedelta
        or blending problem. In elaboration, this could also
        be related to the fact that sprites are rendered
        one-at-a-time, but they SHOULD be rendered through
        sprite groups.

        The rect attribute is useless; should not be used,
        should currently be avoided. This is a problem
        for animated tiles...

    Attributes:
        start_times
        surfaces
        durations
        image
        rect

    See Also:
        :class:`pygame.sprite.Sprite`

    """

    def __init__(self, frames):
        pygame.sprite.Sprite.__init__(self)  # should use super()?
        self.frames = frames
        self.total_duration = self.total_duration(self.frames)
        self.active_frame_index = 0

        # animation position in milliseconds
        self.animation_position = 0

        # this gets updated depending on the frame/time
        # needs to be a surface.
        self.image = self.frames[0].surface

        # never used.
        self.rect = self.image.get_rect()

    def __getitem__(self, frame_index):

        return self.frames[frame_index]

    @staticmethod
    def from_surface_duration_list(surface_duration_list):
        """Support PygAnimation-style frames.

        A list like [(surface, duration in ms)]

        """

        running_time = 0
        frames = []

        for surface, duration in surface_duration_list:
            frame = AnimatedSpriteFrame(surface, running_time, duration)
            frames.append(frame)

        return AnimatedSprite(frames)

    @classmethod
    def from_file(cls, path_or_readable, anchors_config=None):
        """The default is to create from gif bytes, but this can
        also be done from other methods...

        """

        frames = cls.frames_from_gif(path_or_readable, anchors_config)

        return AnimatedSprite(frames)

    def active_frame(self):

        return self.frames[self.active_frame_index]

    def update(self, clock, absolute_position, viewport):
        self.animation_position += clock.tick()

        if self.animation_position >= self.total_duration:
            self.animation_position = (self.animation_position %
                                       self.total_duration)
            self.active_frame_index = 0

        while (self.animation_position >
               self.frames[self.active_frame_index].end_time):

            self.active_frame_index += 1

        self.image = self.frames[self.active_frame_index - 1].surface

        image_size = self.image.get_size()
        relative_position = absolute_position.relative(viewport)
        self.rect = pygame.rect.Rect(relative_position, image_size)

    @staticmethod
    def total_duration(frames):
        """Return the total duration of the animation in milliseconds,
        milliseconds, from animation frame durations.

        Args:
            frames (List[AnimatedSpriteFrame]): --

        Returns:
            int: The sum of all the frame's "duration" attribute.

        """

        return sum([frame.duration for frame in frames])

    @classmethod
    def frames_from_gif(cls, path_or_readable, anchors_config=None):
        """Create a list of surfaces (frames) and a list of their
        respective frame durations from an animated GIF.

        Args:
            path_or_readable (str|file-like-object): Path to
                an animated-or-not GIF.
            anchors_config (configparser): The anchors ini file
                associated with this GIF.

        Returns
            (List[pygame.Surface], List[int]): --

        """

        pil_gif = Image.open(path_or_readable)

        frame_index = 0
        frames = []
        time_position = 0

        try:

            while True:
                duration = pil_gif.info['duration']
                frame_sprite = cls.pil_image_to_pygame_surface(pil_gif, "RGBA")

                if anchors_config:
                    frame_anchors = LabeledSurfaceAnchors(
                                                          anchors_config,
                                                          frame_index
                                                         )
                else:
                    frame_anchors = None

                frame = AnimatedSpriteFrame(
                                            surface=frame_sprite,
                                            start_time=time_position,
                                            duration=duration,
                                            anchors=frame_anchors
                                           )
                frames.append(frame)
                frame_index += 1
                time_position += duration
                pil_gif.seek(pil_gif.tell() + 1)

        except EOFError:

            pass  # end of sequence

        return frames

    @staticmethod
    def pil_image_to_pygame_surface(pil_image, encoding):
        """Convert PIL Image() to pygame Surface.

        Args:
            pil_image (Image): image to convert to pygame.Surface().
            encoding (str): image encoding, e.g., RGBA

        Returns:
            pygame.Surface: the converted image

        Example:
            >>> from PIL import Image
            >>> path = 'resources/walkabouts/debug.zip'
            >>> file_name = 'walk_north.gif'
            >>> sample = zipfile.ZipFile(path).open(file_name).read()
            >>> gif = Image.open(BytesIO(sample))
            >>> pil_to_pygame(gif, "RGBA")
            <Surface(6x8x32 SW)>

        """

        image_as_string = pil_image.convert('RGBA').tostring()

        return pygame.image.fromstring(
                                       image_as_string,
                                       pil_image.size,
                                       'RGBA'
                                      )


# redesign walkabout to be like AnimatedSprite, whereas image
# attrib holds a surface which is updated in... update
class Walkabout(pygame.sprite.Sprite):
    """The graphical representation of an actor. The animations
    associated with various actions and facing directions.

    See Also:
      * :class:`constants.Direction`
      * :class:`constants.Action`
      * :class:`AnimatedSprite`
      * :class:`WalkaboutAnchors`

    Attributes:
        absolute_position (physics.AbsolutePosition): --
        action_direction_animations (dict): --
        active_action (constants.Action): The current action this
            sprite is using.
        active_direction (constants.Direction): The current direction
            this sprite is using.

    """

    # i'm thinking about moving velocity from actor to here.
    # because position is best served here
    def __init__(self, action_direction_animations,
                absolute_position, children=None):

        """Construct a walkabout using the basic data constructs
        which comprise it. To automate the construction of said
        construct, refer to this class' ``from_`` class methods.

        Arguments:
            action_direction_animations (dict): A 2D dictionary; the
                first-level key is a constants.Action enumeration,
                the second level dictionary is a key
                (a constants.Direction enumeration) and a value being
                an AnimatedSprite. Here is an example:

                    >>> direction = constants.Direction
                    >>> sublevel = {d: None for d in direction.cardinal()}
                    >>> toplevel = {a: sublevel.copy()
                    ...             for a in action.yield_all()}

                The above will give you the data construct described,
                however, you'll want to define the animations, since
                the above example uses None in lieu of an animation.
            absolute_position (physics.AbsolutePosition): The
                position of this Walkabout.

        """

        pygame.sprite.Sprite.__init__(self)  # should use super()?
        self.children = children
        self.action_direction_animations = action_direction_animations
        self.absolute_position = absolute_position

        self.active_action = constants.Action.stand
        self.active_direction = constants.Direction.south

        # This is the render position, relative to the render
        # viewport. It will be set by update.
        self.rect = self.image.get_rect()

    def update(self, clock, viewport):

        self.active_animation().update(clock, self.absolute_position, viewport)

    @property
    def image(self):

        return self.active_animation().image

    def active_animation(self):
        """Return the current AnimatedSprite based on the active
        action and direction attributes.

        Returns:
            AnimatedSprite: --

        """

        action = self.active_action
        direction = self.active_direction

        return self.action_direction_animations[action][direction]

    @staticmethod
    def from_resource(resource_name, position=None, children=None):
        resource = util.Resource('walkabouts', resource_name)
        sprite_files = resource.get_type('.gif')

        # no sprites matching pattern!
        if not sprite_files:

            raise BadWalkabout(resource.name)

        # We presume any GIFs in the resource are action_direction
        # sprite animations.
        action_direction_animations = {}

        for sprite_path in sprite_files.keys():
            file_name, file_ext = os.path.splitext(sprite_path)
            file_name = os.path.split(file_name)[1]

            if file_name == 'only':
                # we ONLY want one frame
                action = constants.Action.stand
                direction = constants.Direction.south

            else:
                # we want to collect >1 action_direction
                # animated sprites
                action, direction = file_name.split('_', 1)
                direction = getattr(constants.Direction, direction)
                action = getattr(constants.Action, action)

            associated_config_name = file_name + '.ini'

            if associated_config_name in resource:
                anchors_config = resource[associated_config_name]
            else:
                anchors_config = None

            animation = AnimatedSprite.from_file(
                                                 sprite_files[sprite_path],
                                                 anchors_config=anchors_config
                                                )

            try:
                action_direction_animations[action][direction] = animation
            except KeyError:
                action_direction_animations[action] = {direction: animation}

        if position:
            position = physics.AbsolutePosition(*position)
        else:
            position = None

        return Walkabout(
                         action_direction_animations,
                         absolute_position=position,
                         children=children
                        )

    # NOTE:should use sprite update and spritelayers... will
    # get back to that concept later.
    def update_child_positions(self):
        """Change the position of the children to be relative to
        this Walkabout's absolute position.

        """

        # the rest of this is for children/anchors
        if self.children is None or self.anchors is None:

            return False

        parent_active_frame = self.active_animation().active_frame()
        parent_labeled_anchors = parent_active_frame.anchors
        parent_anchor = parent_labeled_anchors['head_anchor']

        absolute_x = self.absolute_position.int_x
        absolute_y = self.absolute_position.int_y
        parent_position_anchor = Anchor(
                                        absolute_x + frame_anchor.x,
                                        absolute_y + frame_anchor.y
                                       )

        for child in self.children:
            labeled_anchors = child.active_animation().active_frame().anchors
            child_anchor = labeled_anchors['head_anchor']
            new_child_position = parent_position_anchor - head_anchor
            child.absolute_position.set_position(*new_child_position)

        return True

    def get_actions_directions(self):

        if len(self.action_direction_animations) == 1:
            actions = (constants.Action.stand,)
            directions = (constants.Direction.south,)

        else:
            actions = (constants.Action.walk, constants.Action.stand)
            directions = (constants.Direction.north, constants.Direction.south,
                          constants.Direction.east, constants.Direction.west)

        return actions, directions

    def convert(self):
        actions, directions = self.get_actions_directions()

        for action in actions:

            for direction in directions:
                animation = self.action_direction_animations[action][direction]

                for frame in animation.frames:
                    frame.surface = frame.surface.convert_alpha()

    # this is bad
    def runtime_setup(self):
        """Perform actions to setup the walkabout. Actions performed
        once pygame is running and walkabout has been initialized.

        Convert and play all the animations, run init for children.

        Note:
            It MAY be bad to leave the sprites in play mode in startup
            by default.

        """

        self.convert()

        if self.children:

            for walkabout_child in self.children:
                walkabout_child.runtime_setup()


class OldWalkabout(object):
    """Sprite animations for a character which walks around.

    Contextually-aware graphical representation.

    The walkabout sprites specified to be therein
    walkabout_directory, are files with an action__direction.gif
    filename convention.

    Blits its children relative to its own anchor.

    """

    def runtime_setup(self):
        """Perform actions to setup the walkabout. Actions performed
        once pygame is running and walkabout has been initialized.

        Convert and play all the animations, run init for children.

        Note:
            It MAY be bad to leave the sprites in play mode in startup
            by default.

        """

        if len(self.animations) == 1:
            actions = (constants.Action.stand,)
            directions = (constants.Direction.south,)

        else:
            actions = (constants.Action.walk, constants.Action.stand)
            directions = (constants.Direction.north, constants.Direction.south,
                          constants.Direction.east, constants.Direction.west)

        for action in actions:

            for direction in directions:
                animated_sprite = self.animations[action][direction]
                animated_sprite.convert_alpha()
                animated_sprite.play()

        for walkabout_child in self.child_walkabouts:
            walkabout_child.runtime_setup()


def palette_cycle(surface):
    """get_palette is not sufficient; it generates superflous colors.

    Note:
      Need to see if I can convert 32bit alpha to 8 bit temporarily,
      to be converted back at end of palette/color manipulations.

    Args:
        surface (pygame.Surface): --

    Returns:
        AnimatedSprite

    """

    original_surface = surface.copy()  # don't touch! used for later calc
    width, height = surface.get_size()
    ordered_color_list = []
    seen_colors = set()

    for coordinate in itertools.product(range(0, width), range(0, height)):
        color = surface.get_at(coordinate)
        color = tuple(color)

        if color in seen_colors:

            continue

        ordered_color_list.append(color)
        seen_colors.add(color)

    # reverse the color list but not the pixel arrays, then replace!
    old_color_list = collections.deque(ordered_color_list)
    new_surface = surface.copy()
    frames = []
    time_position = 0

    for rotation_i in range(len(ordered_color_list)):
        new_surface = new_surface.copy()

        new_color_list = copy.copy(old_color_list)
        new_color_list.rotate(1)

        color_translations = dict(zip(old_color_list, new_color_list))

        # replace each former color with the color from newcolor_list
        for coordinate in itertools.product(range(0, width), range(0, height)):
            color = new_surface.get_at(coordinate)
            color = tuple(color)
            new_color = color_translations[color]
            new_surface.set_at(coordinate, new_color)

        frame = AnimatedSpriteFrame(new_surface.copy(), time_position, 1000)
        frames.append(frame)
        old_color_list = copy.copy(new_color_list)
        time_position += 1000

    return AnimatedSprite(frames)
