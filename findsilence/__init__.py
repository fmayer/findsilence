# Split WAV - Split long WAV files into tracks
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
    
    def get_silence(self, read_frames=50, silence_cap=500):
        """ 
        Frames
        ======
        Conversion from frames to time is about as following:
        
        2581655 frames => a minute 
        430275 frames => 10 seconds
        43027 frames => 1 second
        
        A normal value for a 33 phono is 80000 to get the position of the songs.
        """
        afterloop_frames = 20
        ##median_volume = self.median_volume()
        width = self.width
        frames = self.frames
        i = self.tell()
        silence = []
        test = []
        # This reads read_frames frames from *every* frame in the stream
        # This may be really unperformant, but ensures that all of the silence
        # is captured.
        while i < frames:
            set_i = True
            ##print '.'
            frame = self.readframes(read_frames)
            volume = audioop.rms(frame, width)
            test.append(volume)
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
        f.setframerate(self.getframerate())
        try:
            f.writeframes(frames)
        finally:
            f.close()


def split_phono(file_name, directory, frames=80000):
    if not os.path.exists(directory):
        os.mkdir(directory)
    elif os.path.isfile(directory):
        raise FileExists("The directory you supplied is a file.")
    audio = Audio(file_name)
    silence = audio.get_silence(frames, 300)
    split_tracks = audio.split_silence(silence)
    for i, split_track in enumerate(split_tracks):
        if len(split_track) < 430275:
            # Skip tracks shorter than 10 seconds.
            # As on old records that could be the pick-up.
            continue
        f_name = os.path.join(directory, "track_%.2d.wav" % i)
        audio.write_frames(f_name, split_track)


def main(file_name):
    directory = os.path.splitext(os.path.split(file_name)[1])[0]
    directory = os.path.abspath(directory)
    split_phono(file_name, directory)
    

if __name__ == "__main__":
    main(sys.argv[1])
