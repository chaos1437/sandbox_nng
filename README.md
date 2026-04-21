# CLI Roguelike

## Install

```bash
pip install -r requirements.txt
```

**Windows**: `pip install windows-curses`

## Run

```bash
# server
python -m server.main --port 8765

# client (in another terminal)
python -m client.main
python -m client.main --host 1.2.3.4 --port 9000
```

## Test

```bash
pytest
```
