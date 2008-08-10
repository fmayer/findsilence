#!/usr/bin/env python

# Copyright (c) 2008 Florian Mayer

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import wave
import audioop

def unify(lst):
    ret = [list(lst[0])]
    lst = lst[1:]
    for elem in lst:
        if ret[-1][1] == elem[0]:
            ret[-1][1] = elem[1]
        else:
            ret.append(list(elem))
    
    return ret


class Audio(wave.Wave_read):
    def __init__(self, file_name):
        wave.Wave_read.__init__(self, file_name)
        self.width = self.getsampwidth()
        self.frames = self.getnframes()
    
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
        median_volume = self.median_volume()
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
                # Maybe we should try and see if the silence goes on longer
                # by continuing in smaller setps
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
                i+=read_frames
            ##print i
            ##print self.frames
        self.rewind()
        return unify(silence)
