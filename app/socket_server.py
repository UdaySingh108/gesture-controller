from flask import Flask, Response
from flask_socketio import SocketIO
from flask_cors import CORS
import cv2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mediapipe as mp
from gestures.landmark_helper import get_finger_positions
from gestures.gesture_utils import detect_swipe_direction, is_pinch_gesture

# Flask + SocketIO setup
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Flask server for gesture-controlled UI is running."

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

# ---- Gesture + Camera logic ----
camera = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

prev_index_x = None
is_dragging = False

def generate_frames():
    global prev_index_x, is_dragging

    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        # Bucket area coordinates
        bucket_top_left = (400, 350)
        bucket_bottom_right = (600, 470)

        cv2.rectangle(frame, bucket_top_left, bucket_bottom_right, (0, 128, 255), 2)
        cv2.putText(frame, "Bucket", (bucket_top_left[0], bucket_top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)

        if result.multi_hand_landmarks:
            for handLms in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                h, w, _ = frame.shape
                finger_positions = get_finger_positions(handLms, w, h)

                if finger_positions:
                    index_x, index_y = finger_positions[1]
                    is_pinching = is_pinch_gesture(finger_positions)

                    # Start drag
                    if is_pinching and not is_dragging:
                        is_dragging = True
                        socketio.emit('gesture', {
                            'type': 'drag_start',
                            'x': index_x,
                            'y': index_y
                        })

                    # Update drag
                    if is_dragging and is_pinching:
                        cv2.putText(frame, "Dragging...", (index_x, index_y - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 0), 2)
                        cv2.circle(frame, (index_x, index_y), 10, (255, 100, 0), -1)
                        socketio.emit('gesture', {
                            'type': 'drag_update',
                            'x': index_x,
                            'y': index_y
                        })

                    # Drop item
                    if is_dragging and not is_pinching:
                        is_dragging = False
                        dropped_in_bucket = (
                            bucket_top_left[0] <= index_x <= bucket_bottom_right[0] and
                            bucket_top_left[1] <= index_y <= bucket_bottom_right[1]
                        )
                        socketio.emit('gesture', {
                            'type': 'drop',
                            'x': index_x,
                            'y': index_y,
                            'in_bucket': dropped_in_bucket
                        })

                    # Swipe detection
                    if prev_index_x is not None:
                        direction = detect_swipe_direction(prev_index_x, index_x)
                        if direction:
                            socketio.emit('gesture', {
                                'type': 'swipe',
                                'direction': direction
                            })

                    prev_index_x = index_x

        # Send processed frame to React
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# ---- Run the server ----
if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
