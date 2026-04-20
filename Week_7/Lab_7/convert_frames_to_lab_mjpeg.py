import os

OUTPUT_FILE = "movie.mjpeg"  # final output for your lab
FRAMES_DIR = "frames"

with open(OUTPUT_FILE, "wb") as out:

    frame_files = sorted(os.listdir(FRAMES_DIR))

    frame_count = 0

    for frame in frame_files:
        if not frame.lower().endswith(".jpg"):
            continue

        path = os.path.join(FRAMES_DIR, frame)

        with open(path, "rb") as f:
            data = f.read()

        length = len(data)

        # Write 5-byte big-endian header
        out.write(length.to_bytes(5, byteorder="big"))

        # Write JPEG frame
        out.write(data)

        frame_count += 1
        print("Wrote frame", frame_count, "size:", length)

print("DONE. Total frames:", frame_count)
