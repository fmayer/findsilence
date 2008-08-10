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
        while i <= frames:
            print '.'
            frame = self.readframes(read_frames)
            volume = audioop.rms(frame, width)
            test.append(volume)
            if volume < silence_cap:
                # Segment is silence!
                silence.append([i, i+read_frames])
                # Maybe we should try and see if the silence goes on longer
                # by continuing in smaller setps
                while volume < silence_cap and self.tell() < self.frames:
                    print "*"
                    frame = self.readframes(afterloop_frames)
                    volume = audioop.rms(frame, width)
                else:
                    silence[-1][1] = self.tell()
            i+=read_frames
        self.rewind()
        return unify(silence)