"""
Looping video frame reader.

Opens a video file with cv2 and yields JPEG-encoded frames one at a
time.  Loops back to the beginning when the video ends so that fake
robots can stream indefinitely even when the recording is short.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2

logger = logging.getLogger(__name__)


class VideoFrameReader:
    """Read frames from a video file and return them as JPEG bytes."""

    def __init__(self, video_path: Path, jpeg_quality: int = 85):
        self._path = video_path
        self._jpeg_quality = jpeg_quality
        self._cap = cv2.VideoCapture(str(video_path))
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        self.fps: float = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width: int = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height: int = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count: int = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._frame_idx: int = 0

        logger.info(
            "VideoFrameReader: %s  %dx%d @ %.1f fps (%d frames)",
            video_path.name, self.width, self.height, self.fps, self.frame_count,
        )

    def read_next_jpeg(self) -> Optional[tuple[bytes, int]]:
        """Read the next frame, JPEG-encode it, and return ``(jpeg_bytes, frame_idx)``.

        Automatically loops back to the start when the video ends.
        Returns ``None`` only if the video is completely unreadable.
        """
        ok, frame = self._cap.read()

        if not ok:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._frame_idx = 0
            ok, frame = self._cap.read()
            if not ok:
                return None

        success, buf = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
        )
        if not success:
            return None

        idx = self._frame_idx
        self._frame_idx += 1
        return bytes(buf), idx

    def close(self) -> None:
        self._cap.release()
