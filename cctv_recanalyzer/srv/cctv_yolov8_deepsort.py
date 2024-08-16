import os

import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from deep_sort_realtime.deep_sort.track import Track

CONFIDENCE_THRESHOLD = 0.6
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)

model = YOLO('yolov8l.pt')
tracker = DeepSort(max_age=10)

video_path = os.path.join('.', 'input.mp4')
video_out_path = os.path.join('.', 'output.mp4')

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise Exception('Error opening video file')

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

cap_out = cv2.VideoWriter(video_out_path, fourcc, fps, (frame_width, frame_height))
show = True

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # https://docs.ultralytics.com/modes/predict/
    detection = model.predict(source=[frame], conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

    # for update deepsort tracker
    raw_detections: list[tuple[list[float | int], float, str]] = []

    for data in detection.boxes.data.tolist():
        # data : [xmin, ymin, xmax, ymax, confidence_score, class_id]
        xmin, ymin, xmax, ymax = map(int, data[:4])
        width = xmax - xmin
        height = ymax - ymin
        confidence = float(data[4])
        detection_class = int(data[5])

        # [left, top, width, height], confidence, detection_class
        raw_detections.append(([xmin, ymin, width, height], confidence, detection_class))

    tracks: list[Track] = tracker.update_tracks(raw_detections, frame=frame)
    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        class_id = track.det_class

        xmin, ymin, xmax, ymax = map(int, track.to_ltrb())
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), GREEN, 2)
        cv2.rectangle(frame, (xmin, ymin - 20), (xmin + 20, ymin), GREEN, -1)
        cv2.putText(frame, str(track_id) + "/" + str(class_id), (xmin + 5, ymin - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 2)

    cap_out.write(frame)
    if show:
        cv2.imshow('cctv', frame)
        if cv2.waitKey(1000 // fps) & 0xFF == ord('q'):
            break

cap.release()
cap_out.release()
cv2.destroyAllWindows()
