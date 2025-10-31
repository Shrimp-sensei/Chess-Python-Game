Chess — Simple chess programs

This workspace contains two small ways to run chess in Python:

- `chess.py` — a Pygame-based GUI (already present). Use this if you have pygame installed.
- `cli_chess.py` — a minimal terminal (text) two-player chess program (no external deps).

Quick start
1. (Optional) create a virtual environment and activate it.
2. Install dependencies for the GUI only:

```powershell
python -m pip install -r requirements.txt
```

3. Run the GUI (if you installed pygame):

```powershell
python "d:\My Code\MyPython\Chess\chess.py"
```

4. Or run the terminal version without any extra packages:

```powershell
python "d:\My Code\MyPython\Chess\cli_chess.py"
```

Controls / notes
- GUI: use the mouse to select and drag pieces. Right click to cancel. Press R to reset.
- CLI: enter moves like `e2e4` or `e2 e4`. Type `quit` to exit. The terminal version supports
	basic legal-move checking and pawn promotion (auto to queen). Castling and en-passant are omitted.

If you want, tell me which version you want extended (full rules, AI opponent, PGN export, etc.) and I can implement it next.
