# VideoStream.py

class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(self.filename, 'rb')
        self.frameNum = 0

    def nextFrame(self):
        """
        Read next frame from MJPEG file.
        Format: each frame = 5-byte header (size) + JPEG bytes.
        Returns frame bytes or None on EOF.
        """
        # Read 5-byte header for frame length
        header = self.file.read(5)
        if len(header) < 5:
            # EOF
            return None

        frameLength = 0
        for b in header:
            frameLength = frameLength * 256 + b

        # Read frameLength bytes for the JPEG frame
        frameData = self.file.read(frameLength)
        if len(frameData) < frameLength:
            return None

        self.frameNum += 1
        return frameData

    def frameNbr(self):
        """Return current frame sequence number."""
        return self.frameNum
