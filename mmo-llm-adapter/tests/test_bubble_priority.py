import pytest
import asyncio
from core.bubble import AttentionBubbleManager

def test_bubble_distance_filtering():
    mgr = AttentionBubbleManager(max_active_bots=3, bubble_radius=1000.0)
    
    # 5 bots at varying distances
    bots = [
        {"pid": 1, "name": "Bot1", "x": 100, "y": 100, "map_index": 21},  # close (~141)
        {"pid": 2, "name": "Bot2", "x": 300, "y": 400, "map_index": 21},  # close (500)
        {"pid": 3, "name": "Bot3", "x": 600, "y": 800, "map_index": 21},  # border (1000)
        {"pid": 4, "name": "Bot4", "x": 1500, "y": 1500, "map_index": 21},# out of range
        {"pid": 5, "name": "Bot5", "x": 100, "y": 100, "map_index": 41}   # wrong map
    ]
    
    active_pids = mgr.update_player_proximity(player_x=0, player_y=0, player_map=21, all_bots=bots)
    
    assert len(active_pids) == 3
    assert 1 in active_pids
    assert 2 in active_pids
    assert 3 in active_pids
    assert 4 not in active_pids
    assert 5 not in active_pids

@pytest.mark.asyncio
async def test_bubble_priority_queue():
    mgr = AttentionBubbleManager()
    
    # Enqueue ambient say (priority 20) first
    await mgr.enqueue_event(
        event_type="say",
        target_pid=1,
        payload={"msg": "ambient chatter"},
        priority=20
    )
    
    # Enqueue direct whisper (priority 100) second
    await mgr.enqueue_event(
        event_type="whisper",
        target_pid=2,
        payload={"msg": "direct whisper"},
        priority=100
    )
    
    # Whisper must come out first due to higher priority
    first = await mgr.get_next_event()
    assert first.event_type == "whisper"
    assert first.target_pid == 2
    
    second = await mgr.get_next_event()
    assert second.event_type == "say"
    assert second.target_pid == 1

