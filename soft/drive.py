import cv2
import numpy as np
import serial
import time
import zmq
import datetime
import os

# --- НАСТРОЙКИ ---
CAMERA_INDEX = 0
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
BASE_SPEED = 255
KP = 0.5
MAX_SPEED = 255
ZMQ_PORT = 5555
VIDEO_DIR = "/home/aieye/robot_test/videos"


def setup_video_recording():
    """Создает папку для видео и возвращает имя файла с датой/временем"""
    # Создаем папку, если её нет
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    # Генерируем имя файла с текущей датой и временем
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_path = os.path.join(VIDEO_DIR, f"robot_{current_time}.avi")

    return video_path


def main():
    # --- НАСТРОЙКА ЗАПИСИ ВИДЕО ---
    video_path = setup_video_recording()
    print(f"Запись видео будет сохранена в: {video_path}")

    # Кодек и создание VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 20.0
    frame_size = (1920, 1080)  # Размер кадра (можно изменить под вашу камеру)

    # --- НАСТРОЙКА КАМЕРЫ ---
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_size[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_size[1])
    cap.set(cv2.CAP_PROP_FPS, fps)

    # Инициализация VideoWriter
    out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
    if not out.isOpened():
        print("ОШИБКА: Не удалось создать VideoWriter!")
        return

    # --- НАСТРОЙКА ZMQ (ПЕРЕДАЧА ВИДЕО) ---
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.bind(f"tcp://*:{ZMQ_PORT}")
    print(f"Трансляция запущена на порту {ZMQ_PORT}")

    # --- НАСТРОЙКА ARDUINO ---
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("Arduino: OK")
    except Exception as e:
        print(f"Arduino Ошибка: {e}")
        ser = None

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]

    frame_count = 0
    start_time = time.time()

    print("Запись видео начата! Нажмите Ctrl+C для остановки...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            height, width, _ = frame.shape
            roi = frame[height - 60:, :]
            # cv2.imshow("roi",roi)
            # if cv2.waitkey(1) & 0xff == ord('q'):
            # break

            # --- ОБРАБОТКА ---
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, mask = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            M = cv2.moments(mask)

            left_speed = 0
            right_speed = 0

            if M["m00"] > 800:
                cx = int(M["m10"] / M["m00"])
                error = cx - (width // 2)
                turn = int(error * KP)
                left_speed = np.clip(BASE_SPEED + turn, -MAX_SPEED, MAX_SPEED)
                right_speed = np.clip(BASE_SPEED - turn, -MAX_SPEED, MAX_SPEED)

                # Рисуем точку и линию на полном кадре
                cv2.circle(frame, (cx, height - 30), 8, (0, 255, 0), -1)
                cv2.line(frame, (width // 2, height - 30), (cx, height - 30), (0, 0, 255), 2)
            else:
                cv2.putText(frame, "LOST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Добавляем временную метку на кадр
            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, current_time_str, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Отправка на Arduino
            if ser and ser.is_open:
                ser.write(f"{int(left_speed)},{int(right_speed)}\n".encode())

            # --- ЗАПИСЬ ВИДЕО ---
            out.write(frame)
            frame_count += 1

            # --- ОТПРАВКА ВИДЕО ПО ZMQ ---
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if ret:
                try:
                    socket.send(buffer.tobytes(), flags=zmq.NOBLOCK)
                except zmq.Again:
                    pass

            # Статистика записи (каждые 100 кадров)
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed
                print(f"Записано кадров: {frame_count}, FPS: {actual_fps:.2f}")

    except KeyboardInterrupt:
        print("\nОстановка по запросу пользователя")
    finally:
        # --- ЗАВЕРШЕНИЕ РАБОТЫ ---
        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0

        print(f"\n--- СТАТИСТИКА ЗАПИСИ ---")
        print(f"Всего кадров: {frame_count}")
        print(f"Время записи: {elapsed_time:.2f} сек")
        print(f"Средний FPS: {actual_fps:.2f}")
        print(f"Видео сохранено: {video_path}")

        # Останавливаем робота
        if ser:
            ser.write(b"0,0\n")
            ser.close()

        # Освобождаем ресурсы
        out.release()
        cap.release()
        cv2.destroyAllWindows()
        print("Ресурсы освобождены")


if __name__ == "__main__":
    main()
