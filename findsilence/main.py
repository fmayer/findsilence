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

""" Main command-line interface. Can also be used to invoke GUI. """

import os
import sys

# Enable users to run the file without installing the program.
script_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(script_path, os.pardir))

from optparse import OptionParser

import findsilence
from findsilence import defaults

def main():
    """ Main entry point for the command line interface """
    parser = OptionParser("findsilence [options] [input files]")
    
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
    
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
                      help="Increase verbosity. Use -vv for very verbose")
    
    parser.add_option('-q', '--quiet', action='store_const', dest='verbose', 
                      const=-1, default=0, help="Show only error messages")
    
    options, args = parser.parse_args()
    
    if options.gui:
        # Loading wx when it is not needed would be a waste of resources,
        # as you can observe it starting up slower when the import is 
        # module-level.
        from gui import create_gui
        create_gui()
    else:
        tracks = len(args)
        if tracks < 1:
            print parser.get_usage()
            sys.exit(1)
        if not options.output:
            # If not output directory is specified, fall back to output in the 
            # current working directory.
            options.output = os.path.join(os.getcwdu(), "output")
            if not os.path.exists(options.output):
                os.mkdir(options.output)
            else:
                raise IOError('No output directory given and "output/" already '
                              'exists in current working directory')
        for track in args:
            if tracks > 1:
                # If there is more than one track, put each of them into a 
                # separate directory.
                output = os.path.join(options.output, os.path.splitext(
                    os.path.basename(track))[0])
                os.mkdir(output)
            else:
                output = options.output
            findsilence.split_phono(track, output, options.pause, 
                                    min_length=options.min_)

            
if __name__ == "__main__":
    main()
