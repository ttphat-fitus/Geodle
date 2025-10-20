# Geodle 
Author: ttpemc - Kali<3H2O
## Install pygame:
```bash
pip install -r requirements.txt
```

## Run
From the project root:
```bash
python3 main.py
```

## Gameplay
- Goal: guess the secret country within the allowed attempts.
- Type a country name in the input (autocomplete dropdown) and Submit (or press Enter).
- After each guess you get per-category hints:
  - Green = matches the target
  - Red = does not match
  - Blue arrow = temperature/population is higher/lower than the guess (direction)
- Remaining attempts shown under the title.
- After win or loss a modal appears; click "Play Again" to start a new game.

Enjoy!