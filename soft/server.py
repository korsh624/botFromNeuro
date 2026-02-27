# -*- coding: utf-8 -*-
from flask import Flask, Response, render_template_string
import zmq

app = Flask(__name__)
ZMQ_PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.CONFLATE, 1)
socket.connect(f"tcp://localhost:{ZMQ_PORT}")
socket.setsockopt_string(zmq.SUBSCRIBE, '')

def gen_frames():
    print("Сервер готов, ждем кадры от робота...")
    while True:
        try:
            frame_bytes = socket.recv()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Ошибка получения кадра: {e}")
            break

@app.route('/')
def index():
    return render_template_string('''
        <html>
        <head>
            <title>Robot Live</title>
            <style>
                body { 
                    background: #111; 
                    color: white; 
                    display: flex; 
                    flex-direction: column;
                    align-items: center; 
                    justify-content: center; 
                    height: 100vh;
                    margin: 0;
                    font-family: Arial;
                }
                h1 { margin-bottom: 10px; font-size: 20px;}
                .video-container {
                    border: 3px solid #444;
                    padding: 5px;
                    border-radius: 8px;
                    background: #222;
                }
                img { 
                    width: 640px; 
                    height: 480px; 
                    display: block;
                }
            </style>
        </head>
        <body>
            <h1>Камера робота (Low Latency)</h1>
            <div class="video-container">
                <img src="{{ url_for('video_feed') }}">
            </div>
        </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
