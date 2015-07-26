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
from PIL import Image


# NOTE: needs to be updated 'cause new animation format
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

        zip_path = os.path.join(
                                'resources',
                                resource_category,
                                resource_name + '.zip'
                               )
        file_handlers = {
                         '.ini': configparser_fromfp,
                         #'.gif': load_gif
                        }

        files = {}

        with zipfile.ZipFile(zip_path) as zip_file:

            for file_name in zip_file.namelist():
                file_data = zip_file.open(file_name).read()

                # because namelist will also generate
                # the directories
                if not file_name:

                    continue

                try:
                    file_data = file_data.decode('utf-8')
                except ValueError:
                    file_data = BytesIO(file_data)

                # then we do the file handler call ehre
                file_extension = os.path.splitext(file_name)[1]

                if file_extension in file_handlers:
                    file_data = file_handlers[file_extension](file_data)

                files[file_name] = file_data

        self.files = files
        self.name = resource_name
        self.category = resource_category

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


def configparser_fromfp(file_data):
    file_data = StringIO(file_data)
    config = configparser.ConfigParser()

    # NOTE: this still works in python 3, though it was
    # replaced by config.read_file()
    config.readfp(file_data)

    return config
