def check_room_id(room_id: str):
    if room_id is None:
        return False
    return (
        len(room_id) == 15
        and all(
            c in "0123456789abcdef"
            for c in room_id
        )
    )