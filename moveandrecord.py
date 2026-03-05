import cv2
import numpy as np
import serial
import time
import datetime


# --- Serial connect---
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # Linux '/dev/ttyACM0'
time.sleep(2)

# --- Camera ---
cap = cv2.VideoCapture(0)
WIDTH = 640
HEIGHT = 480
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

BASE_SPEED = 200
KP = 0.6
count = 0

VIDEO_DIR = "/home/aieye/drive/botFromNeuro/videos"


def write_frame_to_video(frame, video_writer=None,  fps=30):
    """
    frame - изображение OpenCV (numpy array)
    video_writer - объект cv2.VideoWriter (если None, создается новый)
    filename - имя видеофайла
    fps - частота кадров
    """

    height, width = frame.shape[:2]

    if video_writer is None:
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    video_writer.write(frame)

    return video_writer


def send(left, right):
    cmd = f"{left},{right}\n"
    ser.write(cmd.encode())

while True:
    ret, frame = cap.read()
    if not ret:
        break

    count+=1
    writer = write_frame_to_video(frame, writer)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    roi = thresh[HEIGHT//2:HEIGHT, :]

    contours, _ = cv2.findContours(
        roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        M = cv2.moments(cnt)

        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            error = cx - WIDTH//2
            correction = int(KP*error)

            left = BASE_SPEED - correction
            right = BASE_SPEED + correction

            left = max(min(left, 200), -200)
            right = max(min(right, 200), -200)
            if count >20:
              print(right, left)
              send(right, left)
    else:
        send(0, 0)

    cv2.imshow("Frame", frame)
    cv2.imshow("Thresh", thresh)

    if cv2.waitKey(1) == 27:
        break

send(0,0)
if writer:
    writer.release()
cap.release()
cv2.destroyAllWindows()
