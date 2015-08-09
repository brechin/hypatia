#!/bin/sh
#
# This script file is used by all Python 2 installation
# scripts, because it is assumed that "pip" refers to a
# Python 2 installation, considering we're installing
# for Python 2.
#
# This script uses pip to install two requirements files
# and the setup.py for Hypatia. The --user flag installs
# the package to the user's site packages.
#
# This script also FORCES the reinstallation of all
# dependencies, including Hypatia itself.
#
# Does not require root.

pip install --upgrade --force-reinstall --user -r requirements/python2.txt .
