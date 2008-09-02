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

""" Command line interface """

import os
import re
import sys

import findsilence
from findsilence import defaults


def check_overwrite(args, options):
    """ Check whether splitting the tracks contained in args might overwrite 
    files in options.output. """
    file_regex = re.compile("track_\d\d.wav")
    tracks = len(args)
    if tracks < 2:
        # Tracks are directly written into options.output
        if lendir_if(options.output, lambda x: file_regex.match(x)):
            # We could overwrite a track_??.wav file.
            return False
    elif tracks > 1:
        # Each track gets its own sub directory in options.output
        for track in map(get_output_name, args):
            path = os.path.join(options.output, track)
            if os.path.exists(path) and \
               lendir_if(path, lambda x: file_regex.match(x)):
                # We could overwrite a track_??.wav in a sub-directory.
                return False
    return True


def lendir_if(path, cond):
    """ Count all elements in path where cond evaluates True. """
    return sum(1 for x in os.listdir(path) if cond(x))


def get_output_name(track):
    """ Return name of directory that the files of track will be put in. """
    return os.path.splitext(os.path.basename(track))[0]


def create_cli(options, args, parser):
    """ Create the CLI according to options and args. Parser is needed to show 
    help upon invalid input """
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
    elif not check_overwrite(args, options) and not options.force:
        # --force not used and program would overwrite files. 
        # Abort and inform user.
        print ('Output directory contains files that may be '
               'overridden by the program. Skipping.')
        sys.exit(2)
    
    for track in args:
        if tracks > 1:
            # If there is more than one track, put each of them into a 
            # separate directory.
            output = os.path.join(options.output, get_output_name(track))
            os.mkdir(output)
        else:
            output = options.output
        try:
            findsilence.split_phono(track, output, options.pause, 
                                    defaults.volume_cap, 
                                    min_length=options.min_)
        except findsilence.Cancelled:
            print "Operation Cancelled"
        except findsilence.NoSilence:
            print "No silence found in %s" % track