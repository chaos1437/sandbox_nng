# server/handlers.py
from shared.protocol import Message
from shared.constants import MsgType

def handle_message(state, msg: Message) -> Message | None:
    if msg.type == MsgType.JOIN:
        player = state.add_player(msg.player_id or None)
        state.seq += 1
        return Message(
            type=MsgType.STATE_SYNC,
            seq=state.seq,
            player_id=player.player_id,
            payload=state.get_state_snapshot(include_map=True),
        )
    elif msg.type == MsgType.MOVE:
        dx = msg.payload.get("dx", 0)
        dy = msg.payload.get("dy", 0)
        state.move_player(msg.player_id, dx, dy)
        state.seq += 1
        return Message(
            type=MsgType.STATE_SYNC,
            seq=state.seq,
            payload=state.get_state_snapshot(),
        )
    elif msg.type == MsgType.LEAVE:
        state.remove_player(msg.player_id)
        return None
    return None
