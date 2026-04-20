# RtpPacket.py
# RTP packet encode/decode for the RTSP/RTP video streaming lab.

class RtpPacket:
    def __init__(self):
        # 12-byte header + payload
        self.header = bytearray()
        self.payload = b''

    # ---------- ENCODE ----------

    def encode(self, version, padding, extension, cc,
               marker, payloadType, seqnum, timestamp, ssrc,
               payload):
        """
        Build the RTP header and store the payload.

        RTP Header layout (12 bytes):
        0:  V (2 bits) | P (1) | X (1) | CC (4)
        1:  M (1 bit)  | PT (7)
        2-3:   Sequence Number (16 bits)
        4-7:   Timestamp (32 bits)
        8-11:  SSRC (32 bits)
        """

        # Allocate 12 bytes for header
        self.header = bytearray(12)

        # Byte 0: Version, Padding, Extension, CC
        self.header[0] = (
            (version & 0x03) << 6 |
            (padding & 0x01) << 5 |
            (extension & 0x01) << 4 |
            (cc & 0x0F)
        )

        # Byte 1: Marker, Payload Type
        self.header[1] = (
            (marker & 0x01) << 7 |
            (payloadType & 0x7F)
        )

        # Bytes 2-3: Sequence number
        self.header[2] = (seqnum >> 8) & 0xFF
        self.header[3] = seqnum & 0xFF

        # Bytes 4-7: Timestamp
        self.header[4] = (timestamp >> 24) & 0xFF
        self.header[5] = (timestamp >> 16) & 0xFF
        self.header[6] = (timestamp >> 8) & 0xFF
        self.header[7] = timestamp & 0xFF

        # Bytes 8-11: SSRC
        self.header[8] = (ssrc >> 24) & 0xFF
        self.header[9] = (ssrc >> 16) & 0xFF
        self.header[10] = (ssrc >> 8) & 0xFF
        self.header[11] = ssrc & 0xFF

        # Payload: raw JPEG frame
        self.payload = payload

    # ---------- ACCESSORS ----------

    def getPacket(self):
        """Return the complete RTP packet (header + payload)."""
        return bytes(self.header) + self.payload

    def getPayload(self):
        """Return only the RTP payload."""
        return self.payload

    def seqNum(self):
        """Return the RTP sequence number."""
        # Combine bytes 2 and 3
        return (self.header[2] << 8) | self.header[3]

    def timestamp(self):
        """Return the RTP timestamp."""
        return (
            (self.header[4] << 24) |
            (self.header[5] << 16) |
            (self.header[6] << 8) |
            self.header[7]
        )

    def payloadType(self):
        """Return the RTP payload type."""
        return self.header[1] & 0x7F

    # ---------- DECODE ----------

    def decode(self, packet: bytes):
        """
        Decode a raw RTP packet (bytes) into header + payload.
        """
        # First 12 bytes = header
        self.header = bytearray(packet[:12])
        # Rest = payload
        self.payload = packet[12:]
        return self.header, self.payload
# End of RtpPacket.py