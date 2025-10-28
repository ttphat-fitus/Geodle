# Geodle 
**A Wordle-ish geography game**
_Student: Trinh Tan Phat - ID: 24127485_

---

## How to run

### 1. Clone the repository

```bash
git clone https://github.com/ttphat-fitus/Geodle
cd Geodle
```

### 2. Create a Virtual Environment (Optional but Recommended)
Create a virtual environment to avoid conflicts with other projects.

```bash
python -m venv venv
```

Activate it:

- On Windows:
    ```bash
    .\.venv\Scripts\activate
    ```
- On MacOS/Linux:
    ```bash
    source venv/bin/activate
    ```

Deactivate it:

```bash

deactivate
```

### 3. Install Dependencies
Install the required packages using requirements.txt

```bash
pip install -r requirements.txt
```

### 4. Run the game

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