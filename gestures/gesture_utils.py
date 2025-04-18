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
    Detect static gestures like 'two fingers up' (index + middle) and 'fist'.
    """
    if len(finger_positions) < 5:
        return None

    thumb_tip = finger_positions[0]
    index_tip = finger_positions[1]
    middle_tip = finger_positions[2]
    ring_tip = finger_positions[3]
    pinky_tip = finger_positions[4]

    # Use average Y of all fingertips as a reference palm line
    palm_y = (thumb_tip[1] + index_tip[1] + middle_tip[1] + ring_tip[1] + pinky_tip[1]) / 5

    # Check if a finger is up (tip above palm level)
    def is_up(tip_y): return tip_y < palm_y
    def is_down(tip_y): return tip_y > palm_y

    # Fist: all fingers folded (excluding thumb)
    if all(is_down(tip[1]) for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):
        return "fist"

    # Two fingers up: index and middle up, others down
    if (
        is_up(index_tip[1]) and
        is_up(middle_tip[1]) and
        is_down(ring_tip[1]) and
        is_down(pinky_tip[1]) and
        is_down(thumb_tip[1])  # optional: remove for leniency
    ):
        return "twofingers_up"

    return None
