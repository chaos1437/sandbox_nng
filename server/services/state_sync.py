from server.state.world import get_world
from shared.protocol import Message
from shared.constants import MsgType


def make_state_sync(player_id: str) -> Message:
    world = get_world()
    player = world.players.get(player_id)
    if player is None:
        return Message(
            type=MsgType.STATE_SYNC,
            seq=world.seq,
            player_id=player_id,
            payload={
                "seq": world.seq,
                "players": {},
                "full_chunks": [],
                "deltas": [],
            },
        )

    chunk_size = world.chunk_manager.chunk_size
    current_chunk = (player.x // chunk_size, player.y // chunk_size)

    if current_chunk != player.last_chunk:
        new_fov = world.fov_manager.compute_fov(player)
        entered = new_fov - player.current_fov
        player.current_fov = new_fov
        player.pending_full_chunks |= entered
        player.last_chunk = current_chunk

    pending_to_send = player.pending_full_chunks.copy()
    player.pending_full_chunks.clear()

    full_chunks = []
    deltas = []

    for cx, cy in pending_to_send:
        chunk = world.chunk_manager.get_chunk(cx, cy)
        if chunk is not None:
            full_chunks.append({"cx": cx, "cy": cy, "tiles": chunk.tiles})

    for cx, cy in player.current_fov:
        if (cx, cy) in pending_to_send:
            continue
        chunk = world.chunk_manager.get_chunk(cx, cy)
        if chunk is None:
            continue
        for ly in range(len(chunk.tiles)):
            for lx in range(len(chunk.tiles[ly])):
                wx = cx * chunk_size + lx
                wy = cy * chunk_size + ly
                deltas.append([wx, wy, chunk.tiles[ly][lx]])

    return Message(
        type=MsgType.STATE_SYNC,
        seq=world.seq,
        player_id=player_id,
        payload={
            "seq": world.seq,
            "players": {pid: {"x": p.x, "y": p.y} for pid, p in world.players.items()},
            "full_chunks": full_chunks,
            "deltas": deltas,
        },
    )