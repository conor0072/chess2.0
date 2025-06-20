# Chess Game with Pygame and Stockfish AI

**Author:** Conor Kelly  
**Date:** June 13, 2025

---

## How to Run

1. Make sure you have **Python 3** installed.  
2. Install the required libraries:

   ```
   pip install pygame stockfish
   ```

3. Place your **Stockfish binary** inside a folder named `stockfish/`.  
   Update the path in your code if needed:

   ```python
   path = "stockfish/stockfish-macos-x86-64-avx2"
   ```

4. Run the script:

   ```
   python main.py
   ```

---

## Controls and Features

| **Feature**       | **Description**                                              |
|-------------------|--------------------------------------------------------------|
| Drag and Drop     | Click and drag pieces to move them                           |
| Home Screen       | Choose AI difficulty or local multiplayer                    |
| AI Difficulty     | Easy (Depth 4), Medium (Depth 8), Hard (Depth 15)            |
| Check & Checkmate | Highlighted kings and automatic win screen                  |
| Promotion         | Select a piece when a pawn reaches the final rank            |
| Castling          | Fully implemented (king and rook move together legally)      |
| Exit              | Press `E` to confirm and return to home screen               |

---

## Features

- Basic two-player chess functionality  
- Validated piece movement and turn logic  
- AI opponent powered by Stockfish  
- Castling and pawn promotion support  
- Check and checkmate detection  
- Smooth animations and drag behavior  
- User-friendly home and win screens  
