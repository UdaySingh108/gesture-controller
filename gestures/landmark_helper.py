def get_finger_positions(hand_landmarks, image_width, image_height):
    """
    Returns a list of (x, y) positions of fingertips.
    """
    tips_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    positions = []

    for tip_id in tips_ids:
        lm = hand_landmarks.landmark[tip_id]
        x, y = int(lm.x * image_width), int(lm.y * image_height)
        positions.append((x, y))

    return positions
