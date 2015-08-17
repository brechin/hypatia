#!/bin/sh

py -3 -m pip uninstall hypatia_engine -y
py -3 -m pip install --user --no-cache-dir .
cd demo
py -3 game.py
cd ..
