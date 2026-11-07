# Star Drifter

A small arcade space game made with Python and pygame, with three modes. Pick one on the title screen with **1 / 2 / 3** (or the arrow keys + Enter, or a mouse click).

| Mode | What it is |
| --- | --- |
| **1. Standard** | Collect star shards, dash through meteors, level up with upgrade cards and catch the Fever. |
| **2. Dodge** | An endless meteor shower that keeps getting faster and denser. No dash, no power-ups, no upgrades. Your score is how long you survive. |
| **3. Shooter** | Aim with the mouse and blast meteors. They have health bars and get tougher over time. Kills drop shards that level up your guns. |

Each mode keeps its own high score.

## Controls

| Key | Action |
| --- | --- |
| WASD / Arrow keys | Move |
| Space | **Standard:** dash (you're invincible while dashing and smash meteors you hit). **Shooter:** fire |
| Mouse | **Shooter:** aim, hold left click to fire |
| 1 / 2 / 3, arrows + Enter, or mouse | Pick a mode on the title screen, or an upgrade when you level up |
| P / Esc | Pause (Q from the pause menu goes back to mode select) |
| Enter | Play again after a game over |
| B | Toggle bloom (turn off if the game runs slowly) |
| M | Mute / unmute |

**Power-ups (Standard and Shooter):** green **S** gives a 5-second shield; purple **T** slows time for 5 seconds.

## Standard mode

- **Combo:** collect shards quickly to build a score multiplier (up to x10).
- **Close calls:** skim past a meteor without touching it for bonus points, a slow-mo moment, and Fever charge.
- **Fever:** fill the pink Fever bar (shards, close calls, smashes) to go rainbow for 7 seconds. You smash everything you touch and all points are doubled.
- **Events:** every 20-30 seconds something happens: a **Meteor Shower** (survive it for a bonus), a **Shard Storm** (shards everywhere), or **Hunters** (magenta stars that chase you).
- **Enemies:** red rocks, purple **splitters** that burst into smaller rocks, and magenta **hunters** that home in on you.

Every shard fills your XP bar (the gold line at the top of the screen). When it's full you level up and choose one of three upgrade cards:

| Upgrade | Effect | Max |
| --- | --- | --- |
| Thrusters | +15% speed and handling | 4 |
| Coolant | Dash recharges 20% faster | 4 |
| Afterburner | Dashes last 40% longer | 3 |
| Shard Magnet | Pulls nearby shards toward you | 4 |
| Hull Plating | +1 armor that blocks a hit, recharges every 25s | 3 |
| Nova Dash | Dashing releases a shockwave that shatters meteors | 3 |
| Greed | Shards worth 50% more | 3 |
| Shard Swarm | +1 shard on the field | 3 |
| Compact Hull | Smaller hitbox | 2 |
| Lucky Star | More frequent, longer-lasting power-ups | 2 |
| Chronoshift | Stronger, longer slow-time | 2 |
| Combo Keeper | Longer combos, +5 max multiplier | 2 |
| Daredevil | Close calls worth double, fill Fever faster | 2 |

## Dodge mode

Meteors rain from the top of the screen forever. Every few seconds they come faster, bigger and from wider angles. There's a milestone every 15 seconds. One hit and it's over.

## Shooter mode

- You start with **2 armor** (it recharges), and the ship always faces your mouse.
- Meteors show a **health bar** once they're damaged. They get tougher the longer you survive, and late in a run they arrive in pairs.
- Kills build a **kill streak** multiplier and drop gold shards. Collect them to fill your XP bar.
- Fever works here too: it doubles your fire rate and your points.

Shooter upgrades:

| Upgrade | Effect | Max |
| --- | --- | --- |
| Rapid Fire | Fire 25% faster | 4 |
| Heavy Rounds | +1 damage per bullet | 4 |
| Spread Shot | +1 bullet per shot, fanned out | 3 |
| Piercing | Bullets punch through 1 more meteor | 3 |
| Railgun | Faster bullets, longer range | 2 |
| Explosive Rounds | Bullets burst and hurt nearby meteors | 3 |
| Seeker Rounds | Bullets curve toward meteors | 2 |
| Critical Hits | +12% chance for triple damage | 3 |
| Rear Gun | Also fire out the back | 1 |
| Thrusters | +15% speed and handling | 4 |
| Hull Plating | +1 armor, recharges every 25s | 3 |
| Shard Magnet | Pulls dropped shards toward you | 4 |

## Play

### Download the exe
Go to the **Releases** page (or the **Actions** tab → latest run → *Artifacts*) and download `StarDrifter.exe`. Double-click to play.

> Windows SmartScreen may warn about an unknown app because the exe isn't signed. Click **More info → Run anyway**.

### Run from source
```bash
pip install -r requirements.txt
python star_drifter.py
```

### Build the exe yourself
Double-click `build.bat`, or run:
```bash
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --windowed --name StarDrifter star_drifter.py
```
The game will be at `dist/StarDrifter.exe`.

## Automatic builds

The GitHub Actions workflow in `.github/workflows/build.yml` builds the exe on every push to `main`.
To publish a release with the exe attached, push a tag:
```bash
git tag v1.0
git push origin v1.0
```

High scores are saved to `%APPDATA%\StarDrifter\highscores.json`.
