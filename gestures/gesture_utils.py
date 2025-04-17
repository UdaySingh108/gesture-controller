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
