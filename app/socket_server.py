from flask import Flask, Response
from flask_socketio import SocketIO
from flask_cors import CORS
import cv2

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

camera = cv2.VideoCapture(0)

@app.route('/')
def index():
    return "Flask server for gesture-controlled UI is running."

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('gesture')
def handle_external_gesture(data):
    print(f"📩 Received gesture from Python script: {data}")
    socketio.emit('gesture', data, namespace='/')

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)

        # Draw bucket rectangle (for frontend reference only)
        bucket_top_left = (400, 350)
        bucket_bottom_right = (600, 470)
        cv2.rectangle(frame, bucket_top_left, bucket_bottom_right, (0, 128, 255), 2)
        cv2.putText(frame, "Bucket", (bucket_top_left[0], bucket_top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
