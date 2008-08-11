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

class FileExists(Exception):
    pass


def unify(lst):
    """ ((50, 100), (100, 150), (190, 210)) -> ((50, 150), (190, 210)) """
    ret = [list(lst[0])]
    lst = lst[1:]
    for elem in lst:
        if ret[-1][1] == elem[0]:
            ret[-1][1] = elem[1]
        else:
            ret.append(list(elem))
    
    return ret


class Audio(wave.Wave_read):
    """ Improve functionality for wave.Wave_read """
    def __init__(self, file_name):
        wave.Wave_read.__init__(self, file_name)
        self.width = self.getsampwidth()
        self.frames = self.getnframes()
        self.channels = self.getnchannels()
        self.framerate = self.getframerate()
    
    def median_volume(self):
        """ Median volume for the whole file """
        pos = self.tell()
        self.rewind()
        median_volume = audioop.rms(
            self.readframes(self.frames),
            self.width
        )
        self.setpos(pos)
        return median_volume
    
    def get_silence(self, pause_seconds=2, silence_cap=500):
        """ 
        pause_seconds is either an int or a float containing the minimum length 
        of a pause. Silence cap defines what volume level is considered silence.
        """
        read_frames = int(pause_seconds * self.framerate)
        afterloop_frames = 20
        ##median_volume = self.median_volume()
        width = self.width
        frames = self.frames
        i = self.tell()
        silence = []
        # This scans the file in steps of read_frames whether a section's volume
        # is lower than silence_cap, if it is it is written to silence.
        while i < frames:
            set_i = True
            ##print '.'
            frame = self.readframes(read_frames)
            volume = audioop.rms(frame, width)
            if volume < silence_cap:
                # Segment is silence!
                silence.append([i, i+read_frames])
                # Continue searching in smaller steps whether the silence is 
                # longer than read_frames but smaller than read_frames*2.
                while volume < silence_cap and self.tell() < self.frames:
                    ##print "*"
                    frame = self.readframes(afterloop_frames)
                    volume = audioop.rms(frame, width)
                else:
                    tmp = self.tell()
                    silence[-1][1] = tmp
                    i = tmp
                    set_i = False
            if set_i:
                i += read_frames
            ##print i
            ##print self.frames
        self.rewind()
        return unify(silence)
    
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
        f = wave.open(file_name, 'wb')
        f.setnchannels(self.channels)
        f.setsampwidth(self.width)
        f.setframerate(self.framerate)
        try:
            f.writeframes(frames)
        finally:
            f.close()


def split_phono(file_name, directory, pause_seconds=2, volume_cap=300):
    """ Only change pause_seconds or volume_cap if you are sure what you are 
    doing! They seem to be working pretty good for old records. """
    if not os.path.exists(directory):
        os.mkdir(directory)
    elif os.path.isfile(directory):
        raise FileExists("The directory you supplied is a file.")
    audio = Audio(file_name)
    silence = audio.get_silence(pause_seconds, volume_cap)
    split_tracks = audio.split_silence(silence)
    for i, split_track in enumerate(split_tracks):
        if len(split_track) < 10 * audio.framerate:
            # Skip tracks shorter than 10 seconds.
            # As on old records that could be the pick-up.
            continue
        f_name = os.path.join(directory, "track_%.2d.wav" % i)
        audio.write_frames(f_name, split_track)


def main(file_name):
    """ Main command-line interface """
    directory = os.path.splitext(os.path.split(file_name)[1])[0]
    directory = os.path.abspath(directory)
    split_phono(file_name, directory)
    

if __name__ == "__main__":
    main(sys.argv[1])
