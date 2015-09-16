# This module is part of Hypatia and is released under the
# MIT license: http://opensource.org/licenses/MIT

"""These are utilities which are commonly utilized
by all modules in Hypatia. It serves for the ugly,
underlying components of miscellaneous actions which
assist other modules, and does not do much on its own.

"""

import os
import zipfile
from io import BytesIO

try:
    import ConfigParser as configparser
    from cStringIO import StringIO

except ImportError:
    import configparser
    from io import StringIO

import pygame
from animatedsprite import AnimatedSprite


class Resource(object):
    """A zip archive in the resources directory, located by
    supplying a resource category and name. Files are stored
    as a str, BytesIO, PygAnimation, or ConfigParser, in a
    dictionary. Files are referenced by filepath/filename.

    Attributes:
        files (dict): Key is file name, value can be one of str,
            BytesIO, PygAnim, or ConfigParser objects.

    Example:
        >>> import pyganim
        >>> resource = Resource('walkabouts', 'debug')
        >>> 'walk_north.gif' in resource
        True
        >>> isinstance(resource['walk_north.gif'], pyganim.PygAnimation)
        True
        >>> resource = Resource('scenes', 'debug')
        >>> resource['tilemap.txt'].startswith('debug')
        True

    """

    def __init__(self, resource_category, resource_name):
        """Load a resource ZIP using a category and zip name.

        Args:
            resource_category (str): E.g., tilesheets, walkabouts.
            resource_name (str): E.g., debug.

        """

        path = os.path.join(
                            'resources',
                            resource_category,
                            resource_name
                           )

        file_handlers = {
                         '.ini': configparser_fromfp,
                         '.gif': load_gif,
                         '.png': load_png,
                        }

        files = {}

        # choose between loading as an unpacked directory, or a zip file.
        # unpacked takes priority.
        if os.path.isdir(path):

            # go through each file in the supplied path, making an
            # entry in the files dictionary, whose value is the
            # file data (bytesio) and key is file name.
            for file_name in os.listdir(path):
                file_data = open(os.path.join(path, file_name)).read()
                files[file_name] = file_data

        # we're dealing with a zip file for our resources
        else:

            with zipfile.ZipFile(path + ".zip") as zip_file:

                for file_name in zip_file.namelist():

                    # because namelist will also generate
                    # the directories
                    if not file_name:

                        continue

                    file_data = zip_file.open(file_name).read()
                    files[file_name] = file_data

        # Pass the file name and the files dictionary to
        # a function which corresponds to the file name's
        # extension.
        for file_name in files.keys():
            file_data = files[file_name]

            # NOTE: should i leave this up to the parsers?
            """
            try:
                file_data = file_data.decode('utf-8')
            except ValueError:
                file_data = BytesIO(file_data)
            """

            file_extension = os.path.splitext(file_name)[1]

            # if there is a known "handler" for this extension,
            # we want the file data for this file to be the output
            # of said handler
            if file_extension in file_handlers:
                file_data = file_handlers[file_extension](files, file_name)

            files[file_name] = file_data

        self.files = files

    def __getitem__(self, file_name):

        return self.files[file_name]

    def __contains__(self, item):

        return item in self.files

    def get_type(self, file_extension):
        """Return a dictionary of files which have the file extension
        specified. Remember to include the dot, e.g., ".gif"!

        Arg:
            file_extension (str): the file extension (including dot) of
                the files to return.

        Warning:
            Remember to include the dot in the file extension, e.g., ".gif".

        Returns:
            dict|None: {file name: file content} of files which have the
                file extension specified. If no files match,
                None is returned.

        """

        matching_files = {}

        for file_name, file_content in self.files.items():

            if os.path.splitext(file_name)[1] == file_extension:
                matching_files[file_name] = file_content

        return matching_files or None


def load_png(files, file_name):
    """Return an BytesIO object based on supplied file. This is
    a file handler for Resource.

    Args:
        files (dict): Resources files, whereas key is the file name,
            and the value is the untouched file contents itself.
        file_name (str): File from "files" to use for making an
            AnimatedSprite object.

    Returns:
        AnimatedSprite: --

    See Also:
        * Resources.__init__()
        * animations.AnimatedSprite

    """

    return BytesIO(files[file_name])


def load_gif(files, file_name):
    """Return an AnimatedSprite object based on a bytesio
    object. This is a file handler.

    Args:
        files (dict): Resources files, whereas key is the file name,
            and the value is the untouched file contents itself.
        file_name (str): File from "files" to use for making an
            AnimatedSprite object.

    Returns:
        AnimatedSprite: --

    See Also:
        * Resources.__init__()
        * animations.AnimatedSprite

    """

    file_data = files[file_name]

    # NOTE: i used to handle this just in
    # Resources.__init__()
    gif_bytesio = BytesIO(file_data)

    # get the corersponding INI which configures our anchor points
    # for this gif, from the files
    gif_name_no_ext = os.path.splitext(file_name)[0]

    try:
        anchor_ini_name = gif_name_no_ext + '.ini'
        anchor_config_ini = files[anchor_ini_name]

        # if the INI file has not already been parsed into
        # ConfigParser object, we'll do that now, so we
        # can accurately construct our AnimatedSprite.
        try:
            anchor_config_ini.sections()
        except AttributeError:
            anchor_config_ini = configparser_fromfp(files, anchor_ini_name)

    except KeyError:
        anchor_config_ini = None

    return AnimatedSprite.from_file(gif_bytesio, anchor_config_ini)


def configparser_fromfp(files, file_name):
    """Return a ConfigParser object based on a bytesio
    object. This is a file handler.

    Args:
        files (dict): Resources files, whereas key is the file name,
            and the value is a BytesIO object of said file.
        file_name (str): File from "files" to use for making a
            ConfigParser object.

    Returns:
        ConfigParser: --

    See Also:
        Resources.__init__()

    """

    file_data = files[file_name]

    # i used to do this in Resources.__init__()
    file_data = file_data.decode('utf-8')

    file_data = StringIO(file_data)
    config = configparser.ConfigParser()

    # NOTE: this still works in python 3, though it was
    # replaced by config.read_file()
    config.readfp(file_data)

    return config
