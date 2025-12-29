import cv2
import numpy as np
import serial
import time

# --- Serial ---
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Linux '/dev/ttyUSB0'
time.sleep(2)

# --- Camera ---
cap = cv2.VideoCapture(0)
WIDTH = 640
HEIGHT = 480
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

BASE_SPEED = 180
KP = 0.6

def send(left, right):
    cmd = f"{left},{right}\n"
    ser.write(cmd.encode())

while True:
    ret, frame = cap.read()
    if not ret:
        break

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

            left = max(min(left, 255), -255)
            right = max(min(right, 255), -255)

            send(left, right)
    else:
        send(0, 0)

    cv2.imshow("Frame", frame)
    cv2.imshow("Thresh", thresh)

    if cv2.waitKey(1) == 27:
        break

send(0,0)
cap.release()
cv2.destroyAllWindows()
