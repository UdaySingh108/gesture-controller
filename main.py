import cv2
import mediapipe as mp
import socketio
import numpy as np
import requests
from gestures.landmark_helper import get_finger_positions
from gestures.gesture_utils import detect_swipe_direction, is_pinch_gesture, detect_static_gesture

# Connect to Flask-SocketIO server
sio = socketio.Client()
sio.connect('http://localhost:5000')  # Make sure your socket_server.py is running

# Use video stream from socket_server.py
stream_url = 'http://localhost:5000/video_feed'
stream = requests.get(stream_url, stream=True)
bytes_data = b''

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

prev_index_x = None
is_dragging = False
dragged_item = None

bucket_top_left = (400, 350)
bucket_bottom_right = (600, 470)

items = [
    {"id": 1, "name": "Chips", "x": 100, "y": 150, "radius": 30},
    {"id": 2, "name": "Cookies", "x": 200, "y": 150, "radius": 30},
    {"id": 3, "name": "Chocolate", "x": 300, "y": 150, "radius": 30},
    {"id": 4, "name": "Nuts", "x": 400, "y": 150, "radius": 30},
    {"id": 5, "name": "Soda", "x": 100, "y": 250, "radius": 30},
    {"id": 6, "name": "Energy D", "x": 200, "y": 250, "radius": 30},
    {"id": 7, "name": "Water", "x": 300, "y": 250, "radius": 30},
    {"id": 8, "name": "Cold Drink", "x": 400, "y": 250, "radius": 30},
]

def get_item_under_finger(x, y):
    for item in items:
        dist = np.sqrt((x - item['x'])**2 + (y - item['y'])**2)
        if dist <= item['radius']:
            return item
    return None

for chunk in stream.iter_content(chunk_size=1024):
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')  # JPEG start
    b = bytes_data.find(b'\xff\xd9')  # JPEG end

    if a != -1 and b != -1:
        jpg = bytes_data[a:b+2]
        bytes_data = bytes_data[b+2:]

        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue

        #img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        cv2.rectangle(img, bucket_top_left, bucket_bottom_right, (0, 128, 255), 2)
        cv2.putText(img, "Bucket", (bucket_top_left[0], bucket_top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)

        for item in items:
            cv2.circle(img, (item['x'], item['y']), item['radius'], (255, 0, 255), -1)
            cv2.putText(img, item['name'], (item['x'] - 20, item['y'] - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if result.multi_hand_landmarks:
            for handLms in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                h, w, _ = img.shape
                finger_positions = get_finger_positions(handLms, w, h)

                if finger_positions:
                    index_x, index_y = finger_positions[1]
                    is_pinching = is_pinch_gesture(finger_positions)

                    gesture = detect_static_gesture(finger_positions)

                    if gesture == "fist":
                        print("🤜 Fist detected -> Clear Cart")
                        cv2.putText(img, "Clear Cart", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        sio.emit('gesture', {'type': 'clear_cart'})

                    if gesture == "twofingers_up":
                        print("👍 Two fingers UP detected -> Checkout")
                        cv2.putText(img, "Checkout", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        sio.emit('gesture', {'type': 'checkout'})

                    if is_pinching and not is_dragging:
                        is_dragging = True
                        dragged_item = get_item_under_finger(index_x, index_y)
                        print("Gesture: Started dragging")
                        sio.emit('gesture', {'type': 'drag_start', 'x': index_x, 'y': index_y})

                    if is_dragging and is_pinching:
                        cv2.putText(img, f'Dragging', (index_x, index_y - 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 0), 2)
                        cv2.circle(img, (index_x, index_y), 10, (255, 100, 0), -1)
                        sio.emit('gesture', {'type': 'drag_update', 'x': index_x, 'y': index_y})

                    if is_dragging and not is_pinching:
                        is_dragging = False
                        dropped_in_bucket = (
                            bucket_top_left[0] <= index_x <= bucket_bottom_right[0] and
                            bucket_top_left[1] <= index_y <= bucket_bottom_right[1]
                        )

                        if dropped_in_bucket:
                            print("Item dropped inside the bucket!")
                            cv2.putText(img, "Dropped in Bucket!", (30, 130),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 100), 3)
                            item_id = dragged_item['id'] if dragged_item else -1
                            sio.emit('gesture', {
                                'type': 'drop',
                                'x': index_x,
                                'y': index_y,
                                'in_bucket': True,
                                'item_id': item_id
                            })
                        else:
                            print("Item dropped outside")
                            cv2.putText(img, "Dropped outside", (30, 130),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                            sio.emit('gesture', {'type': 'drop', 'x': index_x, 'y': index_y, 'in_bucket': False})

                    if prev_index_x is not None:
                        direction = detect_swipe_direction(prev_index_x, index_x)
                        if direction:
                            cv2.putText(img, f'Swipe {direction}', (30, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                            print(f"Gesture: Swipe {direction}")
                            sio.emit('gesture', {'type': 'swipe', 'direction': direction})

                    prev_index_x = index_x

        cv2.imshow("Gesture Feed (from stream)", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
sio.disconnect()
