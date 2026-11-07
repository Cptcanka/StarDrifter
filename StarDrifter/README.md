# Star Drifter

A small arcade game made with Python and pygame. Fly your ship, collect glowing star shards, and dodge meteors. The longer you survive, the faster they come.

## Controls

| Key | Action |
| --- | --- |
| WASD / Arrow keys | Move |
| Space | Dash (you're invincible while dashing, and you smash meteors you hit) |
| 1 / 2 / 3, arrows + Enter, or mouse | Pick an upgrade when you level up |
| P / Esc | Pause |
| Enter | Start / restart |
| B | Toggle bloom (turn off if the game runs slowly) |
| M | Mute / unmute |

**Power-ups:** green **S** gives a 5-second shield; purple **T** slows time for 5 seconds.
Collect shards quickly to build a combo multiplier (up to x10).

## Thrills

- **Close calls:** skim past a meteor without touching it for bonus points, a slow-mo moment, and Fever charge.
- **Fever:** fill the pink Fever bar (shards, close calls, smashes) to go rainbow for 7 seconds. You smash everything you touch and all points are doubled.
- **Events:** every 20-30 seconds something happens: a **Meteor Shower** (survive it for a bonus), a **Shard Storm** (shards everywhere), or **Hunters** (magenta stars that chase you).
- **Enemies:** red rocks, purple **splitters** that burst into smaller rocks, and magenta **hunters** that home in on you.
## Upgrades

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

High scores are saved to `%APPDATA%\StarDrifter\highscore.txt`.
