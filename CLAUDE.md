## TDD Workflow

### Before writing any feature:
1. Write failing test first (Red)
2. Run test — verify it fails (Red confirmed)
3. Write minimal implementation to pass (Green)
4. Run test — verify it passes (Green confirmed)
5. Refactor if needed (Refactor)
6. Commit with message: "[feature]: add failing test", then "[feature]: make pass"

### Test structure: Arrange-Act-Assert
```python
def test_feature_behavior():
    # Arrange: set up inputs and objects
    world = GameWorld()
    player_id = "test_player"

    # Act: exercise the behavior
    world.add_entity(Entity(player_id))

    # Assert: verify outcomes
    assert world.get_entity(player_id) is not None
```

### Naming: test_<unit>_<behavior>
```python
def test_gameworld_handle_join_creates_entity()
def test_movement_controller_blocks_excessive_speed()
def test_chatsystem_stores_last_5_messages()
```

### When to mock
- Network I/O: mock with asyncio Queue
- File I/O: use tmp_path fixture
- Time: mock with pytest-mock or time.monotonic patch
- **Don't mock business logic** — test real behavior

### Existing untested code
- Don't test private methods (starting with `_`)
- Test public API of each class/module
- If private method complex → extract to class first, then test
