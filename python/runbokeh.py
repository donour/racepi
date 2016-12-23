#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import logo
from sys import argv
from os.path import dirname
from bokeh.command.bootstrap import main

d = dirname(argv[0])
args = [
    argv[0],
    'serve',
    '--host', "*:5006",
    '--allow-websocket-origin', "*:5006",
    d
]

main(args)

# profiling example

#from cProfile import run
#run('main(args)', sort='tottime')
