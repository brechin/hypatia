"""Interactive map entities/players!

Note:
  Could even be something like a sign! Or the human player.

"""

import pygame

from hypatia import constants
from hypatia import actor


class HumanPlayer(actor.Actor):

    def __init__(self, *args, **kwargs):
        actor.Actor.__init__(self, *args, **kwargs)

    # NOTE: outdated/needs to be updated for velocity
    def move(self, game, direction):
        """Modify human player's positional data legally (check
        for collisions).
        Note:
          Will round down to nearest probable step
          if full step is impassable.
          Needs to use velocity instead...
        Args:
          direction (constants.Direction):

        """

        self.walkabout.active_direction = direction

        # hack for incorporating new velocity system, will update later
        if direction in (constants.Direction.north, constants.Direction.south):
            planned_movement_in_pixels = self.velocity.y
        else:
            planned_movement_in_pixels = self.velocity.x

        adj_speed = game.screen.time_elapsed_milliseconds / 1000.0
        iter_pixels = max([1, int(planned_movement_in_pixels)])

        # test a series of positions
        for pixels in range(iter_pixels, 0, -1):
            # create a rectangle at the new position
            new_topleft_x = self.walkabout.absolute_position.float_x
            new_topleft_y = self.walkabout.absolute_position.float_y

            # what's going on here
            if pixels == 2:
                adj_speed = 1

            if direction == constants.Direction.north:
                new_topleft_y -= pixels * adj_speed
            elif direction == constants.Direction.east:
                new_topleft_x += pixels * adj_speed
            elif direction == constants.Direction.south:
                new_topleft_y += pixels * adj_speed
            elif direction == constants.Direction.west:
                new_topleft_x -= pixels * adj_speed

            destination_rect = pygame.Rect((new_topleft_x, new_topleft_y),
                                           self.walkabout.rect.size)
            collision_rect = self.walkabout.rect.union(destination_rect)

            # needs sprite group collide check?
            if not game.scene.collide_check(collision_rect):
                # we're done, we can move!
                self.walkabout.active_action = constants.Action.walk
                self.walkabout.absolute_position.float_x = new_topleft_x
                self.walkabout.absolute_position.float_y = new_topleft_y

                return True

        # never found an applicable destination
        self.walkabout.active_action = constants.Action.stand

        return False


class Npc(actor.Actor):

    def __init__(self, *args, **kwargs):
        actor.Actor.__init__(self, *args, **kwargs)
