# findsilence - Split long WAV files into tracks
# Copyright (C) 2008 Florian Mayer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

script_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(script_path, '..'))

from optparse import OptionParser

import findsilence
from findsilence import defaults

parser = OptionParser()

parser.add_option("-g", "--gui", action="store_true", 
                     dest="gui", default=False,
                     help="Run Graphical User Interface")

parser.add_option("-o", "--output", action="store", 
                     type="string", dest="output", metavar="DIRECTORY",
                     help="write output to DIRECTORY", default=None)

parser.add_option("-m", "--min", action="store", 
                     type="int", dest="min_", metavar="SECONDS",
                     help="drop tracks shorter than SECONDS", 
                     default=defaults.min_length)

parser.add_option("-p", "--pause", action="store", 
                     type="int", dest="pause", metavar="SECONDS",
                     help="find pauses that are more than SECONDS long",
                     default=defaults.pause_seconds)

parser.add_option('--verbose', '-v', action='count', dest='verbose',
                  help="Increase verbosity. Use -vv for very verbose")
parser.add_option('--quiet', '-q', action='store_const', dest='verbose', 
                  const=-1, default=0, help="Show only error messages")

options, args = parser.parse_args()

if options.gui:
    # Loading wx when it is not needed would be a waste of resources,
    # as you can observe it starting up slower when the import is module-level.
    from gui import create_gui
    create_gui()
else:
    tracks = len(args)
    for track in args:
        if tracks > 1:
            output = os.path.join(options.output, os.path.splitext(track)[0])
            os.mkdir(output)
        else:
            output = options.output
        findsilence.split_phono(track, output, options.pause, 
                                min_length=options.min_)