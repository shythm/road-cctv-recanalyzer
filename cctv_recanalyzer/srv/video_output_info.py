import random

import cv2


def get_video_frame(
    filename: str, frame_number: int | None = None, random_number: bool = False
) -> bytes:
    """
    영상의 미리보기 이미지를 생성하여 BufferIO로 반환합니다. 출력은 영상의 크기와 동일합니다.
    """
    if frame_number and random_number:
        raise ValueError("frame_number and random cannot be used together")

    cap = cv2.VideoCapture(filename)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {filename}")

    # total frame count
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_number is not None:
        if frame_number < 0 or frame_number >= total_frames:
            raise ValueError(f"Invalid frame number: {frame_number} / {total_frames}")
    else:
        frame_number = 0

    if random_number:
        frame_number = random.randint(0, total_frames - 1)

    # set frame number
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    # read first frame
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"Cannot read video frame: {filename}")

    # encode frame to jpg
    ret, jpeg = cv2.imencode(".jpg", frame)
    if not ret:
        raise RuntimeError(f"Cannot encode video frame to jpeg: {filename}")

    return jpeg.tobytes()
