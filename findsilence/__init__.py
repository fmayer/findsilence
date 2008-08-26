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

""" This module provides functionality to split files by silence detection """

import wave
import audioop
import os
import os.path
import sys

import actions

__version__ = "0.1rc1"
__author__ = "Florian Mayer <flormayer@aim.com>"
__url__ = ""
__copyright__ = "(c) 2008 Florian Mayer"
__license__ = "GNU General Public License version 3"
__bugs__ = ""

class DummyAction:
    """ Dummy action that always returns False for isSet """
    def isSet(self):
        return False
    

class DummyThread:
    """ Dummy Thread that is used when the functions are used without
    a parent_thread argument """
    def __init__(self):
        self.stopthread = DummyAction()

        
class Cancelled(Exception):
    """ Raised when silence detection was cancelled by parent thread """
    pass

        
class FileExists(Exception):
    """ This is raised when the directory passed to split_phono is a file """
    pass


def unify(lst):
    """ unify continuous ranges.
    
    >>> unify(((50, 100), (100, 150), (190, 210)))
    [[50, 150], [190, 210]]
    """
    ret = [list(lst[0])]
    lst = lst[1:]
    for elem in lst:
        if ret[-1][1] == elem[0]:
            ret[-1][1] = elem[1]
        else:
            ret.append(list(elem))
    
    return ret


class Audio(wave.Wave_read):
    """ Improve functionality for wave.Wave_read with silence finding 
    capabilities. """
    def __init__(self, file_name):
        wave.Wave_read.__init__(self, file_name)
        self.width = self.getsampwidth()
        self.frames = self.getnframes()
        self.channels = self.getnchannels()
        self.framerate = self.getframerate()
    
    def median_volume(self):
        """ Median volume for the whole file. 
        
        It returns to the position where
        the file was before after telling the median volume."""
        pos = self.tell()
        self.rewind()
        median_volume = audioop.rms(
            self.readframes(self.frames),
            self.width
        )
        self.setpos(pos)
        return median_volume
    
    def get_silence(self, pause_seconds=2, silence_cap=500, parent_thread=None):
        """ 
        pause_seconds is either an int or a float containing the minimum length 
        of a pause. Silence cap defines what volume level is considered silence.
        """
        last_emitted = None
        # Enable function to run without a parent Thread.
        if parent_thread is None:
            parent_thread = DummyThread()
        # Find out how many frames the passed second value is
        read_frames = int(pause_seconds * self.framerate)
        # Once silence has been found, continue searching in this interval
        afterloop_frames = 20
        width = self.width
        frames = self.frames
        i = self.tell()
        silence = []
        # This scans the file in steps of read_frames whether a section's volume
        # is lower than silence_cap, if it is it is written to silence.
        while i < frames:
            if parent_thread.stopthread.isSet():
                raise Cancelled
            set_i = True
            frame = self.readframes(read_frames)
            volume = audioop.rms(frame, width)
            if volume < silence_cap:
                # Segment is silence!
                silence.append([i, i+read_frames])
                # Continue searching in smaller steps whether the silence is 
                # longer than read_frames but smaller than read_frames*2.
                while volume < silence_cap and self.tell() < self.frames:
                    frame = self.readframes(afterloop_frames)
                    volume = audioop.rms(frame, width)
                else:
                    silence[-1][1] = i = self.tell()
                    set_i = False
            if set_i:
                i += read_frames
            # Prevent callback to happen too often, thus draining performance.
            if last_emitted is None or last_emitted + self.frames / 100 < i:
                last_emitted = i
                # Callback used to update progessbar
                actions.emmit_action('current_frame', i)
        self.rewind()
        return unify(silence)
    
    def get_silence_deep(self, pause_seconds=2, silence_cap=500, 
                         parent_thread=None):
        """ Search more aggressively for silence. Processes a millisecond at a 
        time. 
        This needs more CPU-Power but should find silence better as with the
        other function some silence might be left out. 
        
        This also seems to yield more false positives, which need to be
        removed later by filters discarding too short tracks. """
        last_emitted = None
        # Enable function to run without a parent Thread.
        if parent_thread is None:
            parent_thread = DummyThread()
        # Scan every millisecond.
        steps = self.framerate / 1000
        # Tell how many frames pause_seconds is
        read_frames = int(pause_seconds * self.framerate)
        silence = []
        width = self.width
        frames = self.frames
        i = 0
        while i < frames:
            if parent_thread.stopthread.isSet():
                raise Cancelled
            # Read a millisecond
            frame = self.readframes(steps)
            volume = audioop.rms(frame, width)
            if volume < silence_cap:
                # Frame is silence
                silence.append([i, i+steps])
            i+=steps
            # Prevent callback to happen to often, thus draining performance.
            if last_emitted is None or last_emitted + self.frames / 100 < i:
                last_emitted = i
                # Callback used to update progessbar
                actions.emmit_action('current_frame', i)
        # Filter out too short segments of silence.
        return [[mini, maxi] for mini, maxi in unify(silence) 
                if maxi - mini > read_frames]
    
    def split_silence(self, silence):
        """ Split the file according to the silence contained in silence. This 
        is usually the return value of Audio.get_silence.
        
        Returns a list of frames, each being a separate song """
        from_pos = 0
        ret = []
        for to_pos, next_from in silence:
            self.setpos(from_pos)
            ret.append(self.readframes(to_pos-from_pos))
            from_pos = next_from
        return ret

    def write_frames(self, file_name, frames):
        """ Write the frames into file_name with the same header as the 
        original file had """
        f = wave.open(file_name, 'wb')
        f.setnchannels(self.channels)
        f.setsampwidth(self.width)
        f.setframerate(self.framerate)
        try:
            f.writeframes(frames)
        finally:
            f.close()


def split_phono(file_name, directory, pause_seconds=2, volume_cap=300, 
                min_length=10, parent_thread=None):
    """ Only change pause_seconds or volume_cap if you are sure what you are 
    doing! They seem to be working pretty good for old records. """
    if not os.path.exists(directory):
        os.mkdir(directory)
    elif os.path.isfile(directory):
        raise FileExists("The directory you supplied is a file.")
    audio = Audio(file_name)
    # Callback used to initalize progessbar.
    actions.emmit_action('frames', audio.frames)
    silence = audio.get_silence_deep(pause_seconds, volume_cap, parent_thread)
    split_tracks = audio.split_silence(silence)
    minus = 0
    for i, split_track in enumerate(split_tracks):
        if len(split_track) / (audio.channels * audio.width) \
           < min_length * audio.framerate:
            # Prevent track numbers to be left out because of too short
            # tracks in order to ensure consistency.
            minus+=1
            # Skip tracks shorter than min_length seconds.
            # As on old records that could be the pick-up.
            continue
        f_name = os.path.join(directory, "track_%.2d.wav" % (i - minus))
        audio.write_frames(f_name, split_track)
    # Callback to allow UI to do cleanup actions without needing to worry
    # about the state of the worker Thread.
    actions.emmit_action('done')


def main(file_name):
    """ Main command-line interface """
    directory = os.path.splitext(os.path.split(file_name)[1])[0]
    directory = os.path.abspath(directory)
    split_phono(file_name, directory)
    

if __name__ == "__main__":
    main(sys.argv[1])
