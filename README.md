# Tetris+ (Final Version)

This project is a modern and enhanced version of the classic **Tetris**, built in **Python** using **Pygame**. It includes all essential gameplay features from the original game, plus refined visuals, a smart assist system, and a **Cheat button** that automatically places the piece in the optimal location.

---

## Main Features

### 1. Complete Gameplay

* Standard 10x20 grid.
* All seven Tetrominoes (I, O, T, S, Z, J, L).
* Rotation, movement, soft drop, hard drop.
* Reliable **Game Over** detection.
* Scoring, levels, and cleared line tracking.
* Next piece preview.
* Full **Hold** system.
* **Ghost piece** showing final landing position.

### 2. Help Button

* Shows a suggested optimal placement for the current piece.
* Uses a basic heuristic:

  * prioritize lines cleared,
  * then final drop height,
  * then overall drop structure.
* Purely visual assistance (does not place the piece).

### 3. Cheat Button

* Automatically places the current piece in the best evaluated position.
* Performs:

  * rotation,
  * horizontal movement,
  * instant drop,
  * immediate lock.
* Useful for relaxed play or strategic testing.

### 4. Enhanced Side Panel

* Score, level, and lines cleared.
* Next piece display.
* Hold piece display.
* Interactive buttons:

  * **Restart**
  * **Help**
  * **Cheat**

---

## Controls

* **Left / Right Arrow**: move the piece
* **Down Arrow**: soft drop
* **Space**: hard drop
* **Z / Up Arrow**: rotate clockwise
* **X**: rotate counter‑clockwise
* **C**: Hold
* **Esc / Q**: quit
* **Mouse**: interact with Help, Cheat, and Restart buttons

---

## Dependencies

This project requires:

* Python 3.10+ (compatible with Python 3.12)
* pygame 2.6+

Install pygame:

```bash
pip install pygame
```

---

## Running the Game

Execute the script:

```bash
python3 tetris_game.py
```

Or run it from your IDE (PyCharm recommended).

---

## Project Structure

* `tetris_game.py` — the main and only required source file.
* No external assets needed.

---

## Possible Improvements

If you want to extend the project further:

* Add chiptune music and sound effects.
* Add line‑clear animations.
* Custom themes and color palettes.
* Local two‑player mode.
* Advanced AI (like professional Tetris Bots).
* High score saving system.

---

## License

Free to use, modify, and redistribute.

---

## Author

Developed using AI assistance (ChatGPT) and refined into a clean, stable final version.
