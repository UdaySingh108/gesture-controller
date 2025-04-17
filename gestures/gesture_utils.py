def detect_swipe_direction(prev_x, current_x, threshold=40):
    """
    Detects horizontal swipe direction based on X movement.
    Returns 'left', 'right', or None
    """
    if abs(current_x - prev_x) > threshold:
        if current_x > prev_x:
            return "right"
        else:
            return "left"
    return None


def is_pinch_gesture(finger_positions, threshold=40):
    """
    Detect if thumb and index finger are close enough to be considered a pinch.
    """
    if len(finger_positions) < 2:
        return False

    thumb = finger_positions[0]
    index = finger_positions[1]

    distance = ((thumb[0] - index[0]) ** 2 + (thumb[1] - index[1]) ** 2) ** 0.5

    print(f"Pinch distance: {distance}")  # Debug line

    return distance < threshold

def detect_static_gesture(finger_positions):
    """
    Detect static gestures like thumbs up and fist based on finger positions.
    """
    if len(finger_positions) < 5:
        return None

    thumb_tip = finger_positions[0]
    index_tip = finger_positions[1]
    middle_tip = finger_positions[2]
    ring_tip = finger_positions[3]
    pinky_tip = finger_positions[4]

    palm_y = finger_positions[0][1]  # Approximate palm level using thumb tip Y

    # Fist: all fingers folded (tips below palm)
    fingers_folded = all(tip[1] > palm_y for tip in [index_tip, middle_tip, ring_tip, pinky_tip])
    if fingers_folded:
        return "fist"

    # Thumbs up: thumb above others, others folded
    thumb_up = thumb_tip[1] < index_tip[1] and all(tip[1] > palm_y for tip in [index_tip, middle_tip, ring_tip, pinky_tip])
    if thumb_up:
        return "thumbs_up"

    return None
