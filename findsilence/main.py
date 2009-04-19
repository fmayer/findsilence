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

from findsilence import defaults

def main():
    """ Main entry point for the command line interface """
    parser = OptionParser("findsilence [options] [input files]")
    
    parser.add_option("-g", "--gui", action="store_true", 
                      dest="gui", default=False,
                      help="Run Graphical User Interface")
    
    parser.add_option("-f", "--force", action="store_true", 
                      dest="force", default=False,
                      help="Give force to override files")
    
    parser.add_option("-o", "--output", action="store", 
                      type="string", dest="output", metavar="DIRECTORY",
                      help="write output to DIRECTORY", default=None)
    
    parser.add_option("-m", "--min", action="store", 
                      type="float", dest="min_", metavar="SECONDS",
                      help="drop tracks shorter than SECONDS", 
                      default=defaults.min_length)
    
    parser.add_option("-p", "--pause", action="store", 
                      type="float", dest="pause", metavar="SECONDS",
                      help="find pauses that are more than SECONDS long",
                      default=defaults.pause_seconds)
    
    parser.add_option("-s", "--silence", action="store", 
                      type="int", dest="volume_cap", metavar="VOLUME",
                      help="Assume everything lower than VOLUME silence.",
                      default=defaults.volume_cap)
    
    parser.add_option("-t", "--tracks", action="store", 
                      type="int", dest="tracks", metavar="TRACKS",
                      help="Adjust the volume cap until it splits into TRACKS tracks.",
                      default=None)
    
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
                      help="Increase verbosity. Use -vv for very verbose")
    
    parser.add_option('-q', '--quiet', action='store_const', dest='verbose', 
                      const=-1, default=0, help="Show only error messages")
    
    options, args = parser.parse_args()
    
    if options.gui:
        # Loading wx when it is not needed would be a waste of resources,
        # as you can observe it starting up slower when the import is 
        # module-level. Plus, using the CLI won't fail if we don't have
        # wxPython this way.
        from findsilence.gui import create_gui
        create_gui(options, args, parser)
    else:
        from findsilence.cli import create_cli
        create_cli(options, args, parser)
            

            
if __name__ == "__main__":
    main()
