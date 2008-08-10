import wave
import audioop

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
    
    def get_silence(self, read_frames=50):
        median_volume = self.median_volume()
        width = self.width
        frames = self.frames
        i = self.tell()
        silence = []
        test = []
        tolerance = 500
        # This reads read_frames frames from *every* frame in the stream
        # This may be really unperformant, but ensures that all of the silence
        # is captured.
        while i <= frames:
            print '.'
            frame = self.readframes(read_frames)
            volume = audioop.rms(frame, width)
            test.append(volume)
            if volume+tolerance < median_volume:
                # Segment is silence!
                silence.append(i)
            i+=read_frames
        self.rewind()
        return test