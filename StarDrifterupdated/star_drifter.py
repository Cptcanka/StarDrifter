"""
Star Drifter - a small arcade game with three modes.

1. STANDARD - collect star shards, dash through meteors, level up, catch the Fever.
2. DODGE    - an endless, ever-faster meteor shower. No dash, no power-ups. Survive.
3. SHOOTER  - aim with the mouse and blast meteors (they have health bars).
              Kills drop shards that level up your guns.

Controls:
    1 / 2 / 3          - pick a mode on the title screen (or arrows + ENTER)
    WASD / Arrow keys  - move
    SPACE              - dash (Standard) / fire (Shooter)
    Mouse              - aim, hold left click to fire (Shooter)
    1 / 2 / 3 or mouse - pick an upgrade card when you level up
    P / ESC            - pause
    B                  - toggle bloom (glow) effect
    M                  - mute / unmute
"""

import array
import json
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------- settings
WIDTH, HEIGHT = 960, 640
FPS = 60
TITLE = "Star Drifter"
BPM = 128
BEAT_MS = 60000 / BPM

BG = (8, 10, 24)
WHITE = (240, 240, 255)
CYAN = (90, 220, 255)
GOLD = (255, 210, 90)
YELLOW = (255, 240, 150)
RED = (255, 80, 80)
ORANGE = (255, 150, 60)
GREEN = (120, 255, 150)
PURPLE = (190, 120, 255)
PINK = (255, 110, 200)
MAGENTA = (255, 60, 170)
BLUE = (110, 150, 255)
STEEL = (160, 185, 255)
GREY = (140, 140, 170)

MODE_ORDER = ["standard", "dodge", "shooter"]
MODES = {
    "standard": ("STANDARD", "Grab shards, dash through meteors, level up and catch the Fever.", CYAN),
    "dodge": ("DODGE", "An endless meteor shower that keeps speeding up. No dash, no power-ups. Survive.", RED),
    "shooter": ("SHOOTER", "Blast meteors apart. Kills drop shards that upgrade your guns.", ORANGE),
}
CONTROLS = {
    "standard": [("WASD / Arrows", "move"), ("SPACE", "dash - invincible, smashes meteors"),
                 ("Skim meteors", "close-call bonus, fills the Fever bar")],
    "dodge": [("WASD / Arrows", "move"), ("That's it", "no dash, no power-ups - just survive")],
    "shooter": [("WASD / Arrows", "move"), ("MOUSE", "aim"),
                ("Hold CLICK / SPACE", "fire - kills drop shards for upgrades")],
}

# id: (name, description, max level, color, short label)
UPGRADES = {
    "thrust": ("Thrusters", "+15% top speed and handling.", 4, ORANGE, "TH"),
    "coolant": ("Coolant", "Dash recharges 20% faster.", 4, CYAN, "CO"),
    "afterburn": ("Afterburner", "Dashes last 40% longer.", 3, BLUE, "AB"),
    "magnet": ("Shard Magnet", "Pulls nearby shards toward you. Range grows each level.", 4, GOLD, "MG"),
    "armor": ("Hull Plating", "+1 armor: blocks one meteor hit. Recharges every 25s.", 3, STEEL, "AR"),
    "nova": ("Nova Dash", "Dashing releases a shockwave that shatters nearby meteors.", 3, PINK, "NV"),
    "greed": ("Greed", "Shards are worth 50% more points.", 3, YELLOW, "GR"),
    "swarm": ("Shard Swarm", "+1 shard on the field at all times.", 3, (255, 190, 120), "SW"),
    "compact": ("Compact Hull", "Shrinks your ship's hitbox.", 2, WHITE, "CH"),
    "lucky": ("Lucky Star", "Power-ups appear more often and stay longer.", 2, GREEN, "LS"),
    "chrono": ("Chronoshift", "Slow-time lasts longer and slows meteors more.", 2, PURPLE, "CS"),
    "combo": ("Combo Keeper", "Combos last 50% longer. Max multiplier +5.", 2, (255, 160, 200), "CK"),
    "daredevil": ("Daredevil", "Close calls are worth double and fill Fever faster.", 2, MAGENTA, "DD"),
}

SHOOTER_UPGRADES = {
    "rapid": ("Rapid Fire", "Fire 25% faster.", 4, ORANGE, "RF"),
    "power": ("Heavy Rounds", "+1 damage per bullet.", 4, RED, "HR"),
    "spread": ("Spread Shot", "+1 bullet per shot, fanned out.", 3, YELLOW, "SP"),
    "pierce": ("Piercing", "Bullets punch through 1 more meteor.", 3, CYAN, "PI"),
    "velocity": ("Railgun", "Faster bullets with longer range.", 2, BLUE, "RG"),
    "explosive": ("Explosive Rounds", "Bullets burst on impact and hurt nearby meteors.", 3, PINK, "EX"),
    "homing": ("Seeker Rounds", "Bullets curve toward meteors.", 2, GREEN, "SK"),
    "crit": ("Critical Hits", "+12% chance for a bullet to deal triple damage.", 3, GOLD, "CR"),
    "rear": ("Rear Gun", "Also fire a shot out the back.", 1, PURPLE, "RR"),
    "thrust": ("Thrusters", "+15% top speed and handling.", 4, (255, 190, 120), "TH"),
    "armor": ("Hull Plating", "+1 armor: blocks one meteor hit. Recharges every 25s.", 3, STEEL, "AR"),
    "magnet": ("Shard Magnet", "Pulls dropped shards toward you.", 4, (255, 220, 150), "MG"),
}

EVENTS = {
    "shower": ("METEOR SHOWER", "Incoming from above!", RED),
    "storm": ("SHARD STORM", "Grab them all!", GOLD),
    "hunters": ("HUNTERS", "They're tracking you...", MAGENTA),
}


def save_dir():
    """Scores live in the user's AppData (or home) so the exe can write them."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "StarDrifter")
    os.makedirs(folder, exist_ok=True)
    return folder


def load_highscores():
    scores = {}
    try:
        with open(os.path.join(save_dir(), "highscores.json"), "r", encoding="utf-8") as f:
            scores = {k: int(v) for k, v in json.load(f).items()}
    except (OSError, ValueError, AttributeError):
        pass
    if "standard" not in scores:  # carry over the score from older versions
        try:
            with open(os.path.join(save_dir(), "highscore.txt"), "r", encoding="utf-8") as f:
                scores["standard"] = int(f.read().strip() or 0)
        except (OSError, ValueError):
            pass
    return scores


def store_highscores(scores):
    try:
        with open(os.path.join(save_dir(), "highscores.json"), "w", encoding="utf-8") as f:
            json.dump(scores, f)
    except OSError:
        pass


def fmt_score(mode, value):
    return f"{value / 10:.1f}s" if mode == "dodge" else str(value)


# ---------------------------------------------------------------- sound
RATE = 22050


def tone_samples(freq_start, freq_end, duration, volume=0.35, noise=0.0):
    n = int(RATE * duration)
    out = array.array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2 * math.pi * freq / RATE
        env = (1 - t) ** 2
        sample = math.sin(phase) * (1 - noise) + random.uniform(-1, 1) * noise
        out.append(int(sample * env * volume * 32767))
    return out


def make_tone(*args, **kwargs):
    """Synthesize a short sound effect (no audio files needed)."""
    return pygame.mixer.Sound(buffer=tone_samples(*args, **kwargs).tobytes())


def make_arp(freqs, step=0.07, volume=0.3):
    buf = array.array("h")
    for f in freqs:
        buf.extend(tone_samples(f, f * 1.01, step, volume))
    return pygame.mixer.Sound(buffer=buf.tobytes())


class Sounds:
    """Synthesized sound effects."""

    def __init__(self):
        self.enabled = False
        self.muted = False
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=1)
            pygame.mixer.set_num_channels(24)
            # pickup pitch rises with the combo
            self.pickups = [make_tone(660 * 2 ** (i / 12), 1320 * 2 ** (i / 12), 0.12, 0.3) for i in range(0, 20, 2)]
            self.dash = make_tone(300, 900, 0.15, 0.25, noise=0.3)
            self.hit = make_tone(220, 40, 0.35, 0.45, noise=0.6)
            self.death = make_tone(300, 30, 0.9, 0.55, noise=0.7)
            self.power = make_tone(440, 1760, 0.3, 0.3)
            self.armor = make_tone(160, 60, 0.4, 0.5, noise=0.4)
            self.nova = make_tone(90, 500, 0.35, 0.4, noise=0.5)
            self.select = make_tone(880, 1400, 0.15, 0.3)
            self.graze = make_tone(1400, 2600, 0.12, 0.22, noise=0.45)
            self.shoot = make_tone(1100, 350, 0.06, 0.09, noise=0.25)
            self.ping = make_tone(1700, 1200, 0.04, 0.08)
            self.levelup = make_arp([523, 659, 784, 1047, 1319])
            self.fever = make_arp([523, 659, 784, 1047, 1319, 1568, 2093], 0.05, 0.32)
            self.alarm = make_arp([880, 660, 880, 660], 0.12, 0.25)
            self.survived = make_arp([784, 1047, 1319, 1568], 0.08, 0.3)
            self.enabled = True
        except pygame.error:
            pass  # no audio device - play silently

    def play(self, name, combo=0):
        if not self.enabled or self.muted:
            return
        if name == "pickup":
            self.pickups[min(combo, len(self.pickups) - 1)].play()
        else:
            getattr(self, name).play()


# ---------------------------------------------------------------- vfx helpers
_glow_cache = {}


def scale_color(c, k):
    k = max(0.0, min(1.0, k))
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


def hue(h, s=75, v=100):
    c = pygame.Color(0)
    c.hsva = (h % 360, s, v, 100)
    return (c.r, c.g, c.b)


def quant(k, steps=6):
    return max(1, round(k * steps)) / steps


def glow_surf(radius, color):
    """A soft radial glow, meant to be blitted with BLEND_ADD."""
    radius = max(2, int(radius))
    key = (radius, color)
    s = _glow_cache.get(key)
    if s is None:
        if len(_glow_cache) > 3000:
            _glow_cache.clear()
        s = pygame.Surface((radius * 2, radius * 2))
        steps = min(radius, 20)
        for i in range(steps):
            b = ((i + 1) / steps) ** 2
            r = max(1, int(radius * (1 - i / steps)))
            pygame.draw.circle(s, scale_color(color, b), (radius, radius), r)
        _glow_cache[key] = s
    return s


def add_glow(surf, x, y, radius, color):
    g = glow_surf(radius, color)
    half = g.get_width() // 2
    surf.blit(g, (int(x) - half, int(y) - half), special_flags=pygame.BLEND_ADD)


_text_cache = {}


def glow_text(dest, text, font, color, center, passes=2):
    """Text with a blurred halo behind it."""
    key = (text, id(font), color)
    entry = _text_cache.get(key)
    if entry is None:
        if len(_text_cache) > 200:
            _text_cache.clear()
        base = font.render(text, True, color)
        solid = font.render(text, True, color, (0, 0, 0))
        pad = 24
        w, h = solid.get_width() + pad * 2, solid.get_height() + pad * 2
        g = pygame.Surface((w, h))
        g.blit(solid, (pad, pad))
        small = pygame.transform.smoothscale(g, (max(1, w // 6), max(1, h // 6)))
        blur = pygame.transform.smoothscale(small, (w, h))
        entry = (base, blur)
        _text_cache[key] = entry
    base, blur = entry
    r = blur.get_rect(center=center)
    for _ in range(passes):
        dest.blit(blur, r, special_flags=pygame.BLEND_ADD)
    dest.blit(base, base.get_rect(center=center))


def make_nebula():
    small = pygame.Surface((60, 40))
    small.fill(BG)
    palette = [(45, 15, 70), (15, 30, 80), (60, 15, 45), (10, 45, 60)]
    for _ in range(8):
        add_glow(small, random.uniform(0, 60), random.uniform(0, 40), random.randint(8, 18), random.choice(palette))
    return pygame.transform.smoothscale(small, (WIDTH + 120, HEIGHT + 120))


def edge_pattern(sw=48, sh=32):
    """0..1 darkness/brightness that grows toward the screen edges."""
    for yy in range(sh):
        for xx in range(sw):
            dx = (xx + 0.5) / sw * 2 - 1
            dy = (yy + 0.5) / sh * 2 - 1
            d = math.hypot(dx, dy) / math.sqrt(2)
            yield xx, yy, min(1.0, max(0.0, (d - 0.35) / 0.65))


def make_vignette():
    small = pygame.Surface((48, 32), pygame.SRCALPHA)
    for xx, yy, a in edge_pattern():
        small.set_at((xx, yy), (0, 0, 0, int(a ** 1.5 * 200)))
    return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))


def make_edge_glow():
    small = pygame.Surface((48, 32))
    for xx, yy, a in edge_pattern():
        b = int(min(1.0, a * 1.3) ** 2 * 255)
        small.set_at((xx, yy), (b, b, b))
    return small


def wrap(text, font, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if font.size(trial)[0] <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def ship_points(x, y, a, r):
    return [
        (x + math.cos(a) * r * 1.3, y + math.sin(a) * r * 1.3),
        (x + math.cos(a + 2.5) * r, y + math.sin(a + 2.5) * r),
        (x - math.cos(a) * r * 0.4, y - math.sin(a) * r * 0.4),
        (x + math.cos(a - 2.5) * r, y + math.sin(a - 2.5) * r),
    ]


def turn_toward(vx, vy, tx, ty, max_turn):
    """Rotate velocity (vx, vy) toward direction (tx, ty) by at most max_turn radians."""
    cur = math.atan2(vy, vx)
    want = math.atan2(ty, tx)
    diff = (want - cur + math.pi) % math.tau - math.pi
    cur += max(-max_turn, min(max_turn, diff))
    spd = math.hypot(vx, vy)
    return math.cos(cur) * spd, math.sin(cur) * spd


# ---------------------------------------------------------------- effects
class Particle:
    def __init__(self, x, y, color, speed=4.0, life=40, size=3, vx=None, vy=None, drag=0.96, glow=True):
        if vx is None:
            ang = random.uniform(0, math.tau)
            spd = random.uniform(0.3, 1.0) * speed
            vx, vy = math.cos(ang) * spd, math.sin(ang) * spd
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color = color
        self.life = self.max_life = life
        self.size = size
        self.drag = drag
        self.glow = glow

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy *= self.drag
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        k = quant(self.life / self.max_life)
        r = max(1, int(self.size * k))
        if self.glow:
            add_glow(surf, self.x, self.y, r * 3, scale_color(self.color, k * 0.5))
        pygame.draw.circle(surf, scale_color(self.color, k), (int(self.x), int(self.y)), r)


class Debris:
    """A tumbling rock fragment."""

    def __init__(self, x, y, base_r, color, fill=(70, 40, 40)):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(1, 4.5)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(ang) * spd, math.sin(ang) * spd
        self.rot = random.uniform(0, math.tau)
        self.spin = random.uniform(-0.25, 0.25)
        n = random.randint(3, 4)
        size = random.uniform(0.25, 0.45) * base_r
        self.shape = [(i / n * math.tau + random.uniform(-0.3, 0.3), size * random.uniform(0.6, 1)) for i in range(n)]
        self.life = self.max_life = random.randint(40, 70)
        self.color, self.fill = color, fill

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.97
        self.vy *= 0.97
        self.rot += self.spin
        self.life -= 1

    def draw(self, surf):
        k = self.life / self.max_life
        pts = [(self.x + math.cos(a + self.rot) * d, self.y + math.sin(a + self.rot) * d) for a, d in self.shape]
        pygame.draw.polygon(surf, scale_color(self.fill, k), pts)
        pygame.draw.polygon(surf, scale_color(self.color, k), pts, 1)


class Ring:
    """Expanding shockwave ring."""

    def __init__(self, x, y, color, max_r, life=30, width=4, start_r=4):
        self.x, self.y = x, y
        self.color, self.max_r, self.start_r = color, max_r, start_r
        self.life = self.max_life = life
        self.width = width

    def update(self):
        self.life -= 1

    def draw(self, surf):
        k = self.life / self.max_life
        t = 1 - k
        ease = 1 - (1 - t) ** 3
        r = int(self.start_r + (self.max_r - self.start_r) * ease)
        w = max(1, int(self.width * k + 1))
        if r > w:
            pygame.draw.circle(surf, scale_color(self.color, k), (int(self.x), int(self.y)), r, w)


class FloatText:
    def __init__(self, x, y, text, color, font, life=50, vy=-1.4):
        self.surf = font.render(text, True, color)
        self.x, self.y, self.vy = x, y, vy
        self.life = self.max_life = life

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):
        k = self.life / self.max_life
        age = self.max_life - self.life
        img = self.surf
        if age < 6:  # pop in
            s = 1.6 - 0.1 * age
            img = pygame.transform.smoothscale(self.surf, (int(self.surf.get_width() * s), int(self.surf.get_height() * s)))
        img.set_alpha(255 if k > 0.4 else int(255 * k / 0.4))
        surf.blit(img, img.get_rect(center=(self.x, self.y)))


# ---------------------------------------------------------------- entities
class Player:
    RADIUS = 14

    def __init__(self, base_armor=0):
        self.x, self.y = WIDTH / 2, HEIGHT / 2
        self.vx = self.vy = 0.0
        self.angle = -math.pi / 2
        self.aim = None  # set in Shooter mode: the ship faces the mouse
        self.dash_timer = 0
        self.dash_cd = 0
        self.shield = 0  # frames of shield from power-up
        self.invuln = 0  # frames of post-hit invulnerability
        self.base_armor = base_armor
        self.armor = base_armor
        self.armor_regen = 0
        self.fever = False
        self.fever_smash = True
        self.thrusting = False
        self.trail = []
        self.ghosts = []
        self.recompute({})

    def recompute(self, levels):
        lv = lambda k: levels.get(k, 0)  # noqa: E731
        self.accel = 0.9 * (1 + 0.15 * lv("thrust"))
        self.max_speed = 7.5 * (1 + 0.15 * lv("thrust"))
        self.dash_cooldown = int(70 * 0.8 ** lv("coolant"))
        self.dash_time = int(12 * (1 + 0.4 * lv("afterburn")))
        self.hit_radius = self.RADIUS * 0.7 * 0.8 ** lv("compact")
        self.draw_scale = 1 - 0.1 * lv("compact")
        self.magnet = [0, 120, 180, 240, 300][lv("magnet")]
        self.max_armor = lv("armor") + self.base_armor

    @property
    def dashing(self):
        return self.dash_timer > 0

    @property
    def smashing(self):
        return self.dash_timer > 0 or self.shield > 0 or (self.fever and self.fever_smash)

    def update(self, keys, particles):
        events = []
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.thrusting = bool(dx or dy)
        if self.thrusting:
            length = math.hypot(dx, dy)
            self.vx += dx / length * self.accel
            self.vy += dy / length * self.accel
            a = math.atan2(dy, dx)  # exhaust goes opposite to the thrust direction
            tx = self.x - math.cos(a) * self.RADIUS * 0.6
            ty = self.y - math.sin(a) * self.RADIUS * 0.6
            for _ in range(2):
                spd = random.uniform(1.5, 3.5)
                particles.append(Particle(
                    tx, ty, random.choice((ORANGE, YELLOW, RED)),
                    vx=-math.cos(a) * spd + random.uniform(-0.7, 0.7) + self.vx * 0.3,
                    vy=-math.sin(a) * spd + random.uniform(-0.7, 0.7) + self.vy * 0.3,
                    life=random.randint(12, 22), size=random.randint(2, 4), drag=0.92,
                ))

        limit = self.max_speed * (2.2 if self.dashing else 1)
        speed = math.hypot(self.vx, self.vy)
        if speed > limit:
            self.vx *= limit / speed
            self.vy *= limit / speed
        if not self.dashing:
            self.vx *= 0.88
            self.vy *= 0.88

        r = self.RADIUS
        self.x = max(r, min(WIDTH - r, self.x + self.vx))
        self.y = max(r, min(HEIGHT - r, self.y + self.vy))
        if self.aim is not None:
            self.angle = self.aim
        elif speed > 0.3:
            self.angle = math.atan2(self.vy, self.vx)

        self.trail.append((self.x, self.y))
        if len(self.trail) > 16:
            self.trail.pop(0)

        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.dash_timer % 2 == 0:
                self.ghosts.append([self.x, self.y, self.angle, 16])
            particles.append(Particle(self.x, self.y, CYAN, 1.5, 18, 4))
        for g in self.ghosts:
            g[3] -= 1
        self.ghosts = [g for g in self.ghosts if g[3] > 0]

        if self.dash_cd > 0:
            self.dash_cd -= 1
            if self.dash_cd == 0:
                events.append("dash_ready")
        if self.shield > 0:
            self.shield -= 1
        if self.invuln > 0:
            self.invuln -= 1
        if self.armor < self.max_armor:
            self.armor_regen += 1
            if self.armor_regen >= 60 * 25:
                self.armor += 1
                self.armor_regen = 0
                events.append("armor")
        return events

    def try_dash(self):
        if self.dash_cd > 0:
            return False
        speed = math.hypot(self.vx, self.vy)
        if speed < 0.5:
            dirx, diry = math.cos(self.angle), math.sin(self.angle)
        else:
            dirx, diry = self.vx / speed, self.vy / speed
        self.vx, self.vy = dirx * self.max_speed * 2.2, diry * self.max_speed * 2.2
        self.dash_timer = self.dash_time
        self.dash_cd = self.dash_cooldown
        return True

    def draw(self, surf, tick):
        r = self.RADIUS * self.draw_scale
        a = self.angle

        # engine trail (rainbow during fever)
        n = len(self.trail)
        col = CYAN if self.dashing else (80, 130, 200)
        for i in range(1, n):
            k = i / n
            c = hue(tick * 6 + i * 14) if self.fever else col
            pygame.draw.line(surf, scale_color(c, k * 0.9), self.trail[i - 1], self.trail[i], max(1, int(k * (9 if self.fever else 6))))

        for gx, gy, ga, gl in self.ghosts:
            pygame.draw.polygon(surf, scale_color(CYAN, gl / 16 * 0.7), ship_points(gx, gy, ga, r), 2)

        if self.fever:
            add_glow(surf, self.x, self.y, int(r * 4.5), scale_color(hue(tick * 6), 0.45))
        add_glow(surf, self.x, self.y, int(r * 3.2), (50, 140, 190) if self.dashing else (20, 55, 80))

        if self.shield > 0 and (self.shield > 90 or tick % 10 < 5):
            add_glow(surf, self.x, self.y, int(r + 24), (10, 50, 25))
            pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), int(r + 10), 2)

        for i in range(self.armor):
            ang = tick * 0.05 + i * math.tau / max(1, self.armor)
            ox = self.x + math.cos(ang) * (r + 17)
            oy = self.y + math.sin(ang) * (r + 17)
            add_glow(surf, ox, oy, 9, (40, 50, 90))
            pygame.draw.circle(surf, STEEL, (int(ox), int(oy)), 3)

        if self.invuln > 0 and tick % 6 < 3:
            return  # blink after taking a hit

        if self.thrusting or self.dashing:
            length = r * (0.9 + random.random() * 0.8) * (1.8 if self.dashing else 1)
            bx, by = self.x - math.cos(a) * r * 0.4, self.y - math.sin(a) * r * 0.4
            px, py = -math.sin(a), math.cos(a)
            for w, ln, c in ((r * 0.45, length, ORANGE), (r * 0.22, length * 0.6, YELLOW)):
                pts = [(bx + px * w, by + py * w), (bx - math.cos(a) * ln, by - math.sin(a) * ln), (bx - px * w, by - py * w)]
                pygame.draw.polygon(surf, CYAN if self.dashing else c, pts)

        pts = ship_points(self.x, self.y, a, r)
        pygame.draw.polygon(surf, (225, 235, 255), pts)
        pygame.draw.polygon(surf, hue(tick * 8) if self.fever else CYAN, pts, 2)
        cx, cy = self.x + math.cos(a) * r * 0.35, self.y + math.sin(a) * r * 0.35
        pygame.draw.circle(surf, (30, 70, 120), (int(cx), int(cy)), max(2, int(r * 0.22)))


class Bullet:
    def __init__(self, x, y, angle, speed, dmg, pierce, life, crit):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.dmg, self.pierce, self.life, self.crit = dmg, pierce, life, crit
        self.hit = set()
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0 or not (-20 < self.x < WIDTH + 20 and -20 < self.y < HEIGHT + 20):
            self.alive = False

    def draw(self, surf):
        color = GOLD if self.crit else CYAN
        add_glow(surf, self.x, self.y, 12 if self.crit else 9, scale_color(color, 0.55))
        pygame.draw.line(surf, color, (self.x - self.vx * 1.4, self.y - self.vy * 1.4), (self.x, self.y), 4 if self.crit else 3)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 2)


class Meteor:
    """kind: 'rock', 'hunter' (homes in on you) or 'splitter' (breaks into rocks)."""

    POINTS = {"rock": 25, "hunter": 50, "splitter": 40}

    def __init__(self, difficulty, kind="rock", pos=None, vel=None, r=None):
        self.kind = kind
        self.r = r or {"rock": random.randint(14, 34), "hunter": random.randint(13, 17), "splitter": random.randint(30, 38)}[kind]
        if pos is None:
            side = random.randint(0, 3)
            if side == 0:
                self.x, self.y = random.uniform(0, WIDTH), -self.r
            elif side == 1:
                self.x, self.y = WIDTH + self.r, random.uniform(0, HEIGHT)
            elif side == 2:
                self.x, self.y = random.uniform(0, WIDTH), HEIGHT + self.r
            else:
                self.x, self.y = -self.r, random.uniform(0, HEIGHT)
        else:
            self.x, self.y = pos
        if vel is None:
            tx = WIDTH / 2 + random.uniform(-WIDTH / 3, WIDTH / 3)
            ty = HEIGHT / 2 + random.uniform(-HEIGHT / 3, HEIGHT / 3)
            ang = math.atan2(ty - self.y, tx - self.x)
            if kind == "hunter":
                spd = min(4.5, 2.2 + difficulty * 0.15)
            else:
                spd = random.uniform(1.5, 3.0) + difficulty * 0.35
            self.vx, self.vy = math.cos(ang) * spd, math.sin(ang) * spd
        else:
            self.vx, self.vy = vel
        self.speed = max(0.1, math.hypot(self.vx, self.vy))
        self.rot = random.uniform(0, math.tau)
        self.spin = random.uniform(-0.05, 0.05)
        if kind == "hunter":
            self.shape = [(i / 10 * math.tau, 1.2 if i % 2 == 0 else 0.55) for i in range(10)]
            self.spin = 0.12
        else:
            n = random.randint(7, 11)
            self.shape = [(i / n * math.tau, random.uniform(0.7, 1.1)) for i in range(n)]
        self.craters = [(random.uniform(0, math.tau), random.uniform(0.2, 0.55), random.uniform(0.12, 0.22)) for _ in range(3)]
        self.hot = kind == "rock" and self.speed > 4.0  # fast meteors burn
        self.home = 60 * 9 if kind == "hunter" else 0
        self.safe = 0  # frames before it can hit the player (fresh splitter shards)
        self.grazed = False
        self.alive = True
        self.t = random.uniform(0, math.tau)
        self.hp = self.max_hp = 1  # only matters in Shooter mode
        self.hit_flash = 0

    def update(self, slow, particles, target=None):
        self.t += 0.15 * slow
        if self.safe > 0:
            self.safe -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.home > 0 and target is not None:
            self.home -= 1
            self.vx, self.vy = turn_toward(self.vx, self.vy, target[0] - self.x, target[1] - self.y, 0.035 * slow)
        self.x += self.vx * slow
        self.y += self.vy * slow
        self.rot += self.spin * slow
        if (self.hot or self.kind == "hunter") and random.random() < 0.4 * slow:
            particles.append(Particle(
                self.x - self.vx / self.speed * self.r * 0.8, self.y - self.vy / self.speed * self.r * 0.8,
                random.choice((MAGENTA, PINK) if self.kind == "hunter" else (ORANGE, RED)),
                vx=-self.vx * 0.2 + random.uniform(-0.5, 0.5),
                vy=-self.vy * 0.2 + random.uniform(-0.5, 0.5), life=22, size=3, drag=0.95,
            ))
        m = self.r + 80
        if self.home <= 0 and (self.x < -m or self.x > WIDTH + m or self.y < -m or self.y > HEIGHT + m):
            self.alive = False

    def draw(self, surf):
        pts = [
            (self.x + math.cos(a + self.rot) * self.r * k, self.y + math.sin(a + self.rot) * self.r * k)
            for a, k in self.shape
        ]
        if self.kind == "hunter":
            pulse = 0.5 + 0.5 * math.sin(self.t * 2)
            add_glow(surf, self.x, self.y, int(self.r * 2.6), scale_color(MAGENTA, 0.25 + 0.2 * pulse))
            pygame.draw.polygon(surf, (60, 15, 45), pts)
            pygame.draw.polygon(surf, WHITE if self.hit_flash else MAGENTA, pts, 2)
            pygame.draw.circle(surf, scale_color(WHITE, 0.6 + 0.4 * pulse), (int(self.x), int(self.y)), max(2, int(self.r * 0.3)))
        elif self.kind == "splitter":
            add_glow(surf, self.x, self.y, int(self.r * 1.9), (30, 15, 50))
            pygame.draw.polygon(surf, (55, 40, 75), pts)
            for i in range(0, len(pts), 3):  # glowing cracks
                pygame.draw.line(surf, PURPLE, (self.x, self.y), pts[i], 2)
            pygame.draw.polygon(surf, WHITE if self.hit_flash else PURPLE, pts, 3 if self.hit_flash else 2)
        else:
            add_glow(surf, self.x, self.y, int(self.r * 1.8), (45, 14, 8) if self.hot else (30, 10, 10))
            pygame.draw.polygon(surf, (110, 80, 85) if self.hit_flash else (70, 42, 46), pts)
            for a, d, s in self.craters:
                cx = self.x + math.cos(a + self.rot) * self.r * d
                cy = self.y + math.sin(a + self.rot) * self.r * d
                pygame.draw.circle(surf, (45, 26, 30), (int(cx), int(cy)), max(2, int(self.r * s)))
            pygame.draw.polygon(surf, WHITE if self.hit_flash else (ORANGE if self.hot else RED), pts, 3 if self.hit_flash else 2)

        if self.max_hp > 1 and self.hp < self.max_hp:  # health bar
            w = max(24, self.r * 1.6)
            x, y = self.x - w / 2, self.y - self.r - 12
            frac = max(0.0, self.hp / self.max_hp)
            color = GREEN if frac > 0.6 else YELLOW if frac > 0.3 else RED
            pygame.draw.rect(surf, (20, 20, 30), (x - 1, y - 1, w + 2, 6))
            pygame.draw.rect(surf, color, (x, y, w * frac, 4))


class Pickup:
    """kind: 'shard' (points + XP), 'shield', or 'slow' (slows time)."""

    COLORS = {"shard": GOLD, "shield": GREEN, "slow": PURPLE}

    def __init__(self, kind="shard", life=None, avoid=None, pos=None):
        self.kind = kind
        if pos:
            self.x = max(20, min(WIDTH - 20, pos[0]))
            self.y = max(30, min(HEIGHT - 20, pos[1]))
        else:
            for _ in range(20):
                self.x = random.uniform(40, WIDTH - 40)
                self.y = random.uniform(60, HEIGHT - 50)
                if avoid is None or math.hypot(self.x - avoid[0], self.y - avoid[1]) > 140:
                    break
        self.r = 9 if kind == "shard" else 12
        self.t = random.uniform(0, math.tau)
        self.life = life
        self.age = 0
        self.taken = False
        self.pulled = False

    def update(self):
        self.t += 0.08
        self.age += 1
        if self.life is not None:
            self.life -= 1

    @property
    def alive(self):
        return not self.taken and (self.life is None or self.life > 0)

    def draw(self, surf, beat=0.0):
        if self.life is not None and self.life < 90 and int(self.t * 3) % 2:
            return  # blink before vanishing
        color = self.COLORS[self.kind]
        grow = min(1.0, self.age / 15)
        pulse = (self.r + math.sin(self.t) * 2 + beat * 3) * grow
        add_glow(surf, self.x, self.y, int(pulse * 3) + 2, scale_color(color, 0.45))
        if self.kind == "shard":
            s = pulse
            rot = self.t * 0.5
            pts = [
                (self.x + math.cos(rot + i * math.pi / 2) * s * (1 if i % 2 == 0 else 0.6),
                 self.y + math.sin(rot + i * math.pi / 2) * s * (1 if i % 2 == 0 else 0.6))
                for i in range(4)
            ]
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), max(1, int(s * 0.3)))
        else:
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), max(2, int(pulse)), 3)
            for i in range(3):
                a = self.t * 1.5 + i * math.tau / 3
                pygame.draw.circle(surf, color, (int(self.x + math.cos(a) * (pulse + 7)), int(self.y + math.sin(a) * (pulse + 7))), 2)
            label = "S" if self.kind == "shield" else "T"
            txt = FONT_SMALL.render(label, True, color)
            surf.blit(txt, txt.get_rect(center=(self.x, self.y)))


# ---------------------------------------------------------------- game
class Game:
    FEVER_TIME = 60 * 7

    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.sounds = Sounds()
        self.highscores = load_highscores()
        self.world = pygame.Surface((WIDTH, HEIGHT))
        self.flash_surf = pygame.Surface((WIDTH, HEIGHT))
        self.shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.band = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        self.nebula = make_nebula()
        self.vignette = make_vignette()
        self.edge_small = make_edge_glow()
        self.stars = [
            [random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.choice((1, 1, 1, 2, 2, 3))] for _ in range(170)
        ]
        self.bloom = True
        self.mode = "standard"
        self.title_sel = 0
        self.mode_rects = []
        self.cursor_visible = True
        self.state = "title"
        self.tick = 0
        self.beat = 0.0
        self.shake = 0
        self.flash_alpha = 0
        self.flash_color = WHITE
        self.hitstop = 0
        self.title_spawn = 0
        self.reset()

    def reset(self):
        self.player = Player(base_armor=2 if self.mode == "shooter" else 0)
        self.player.fever_smash = self.mode == "standard"
        self.meteors = []
        self.new_meteors = []
        self.pickups = [Pickup() for _ in range(3)] if self.mode == "standard" else []
        self.bullets = []
        self.fire_cd = 0
        self.particles = []
        self.debris = []
        self.rings = []
        self.texts = []
        self.score = 0
        self.shown_score = 0.0
        self.score_pop = 0.0
        self.combo = 0
        self.combo_timer = 0
        self.combo_pop = 0.0
        self.time_alive = 0
        self.spawn_timer = 0
        self.slow_timer = 0
        self.slowmo = 0
        self.new_record = False
        self.over_tick = 0
        self.level = 1
        self.xp = 0
        self.levels = {}
        self.cards = []
        self.card_sel = 0
        self.card_rects = []
        self.card_open_tick = 0
        self.fever_meter = 0.0
        self.fever_timer = 0
        self.grazes = 0
        self.kills = 0
        self.event = None
        self.next_event = 60 * 20
        self.banner = None

    def lv(self, key):
        return self.levels.get(key, 0)

    @property
    def pool(self):
        return SHOOTER_UPGRADES if self.mode == "shooter" else UPGRADES

    @property
    def highscore(self):
        return self.highscores.get(self.mode, 0)

    @property
    def difficulty(self):
        return self.time_alive / (60 * 12)  # +1 every 12 seconds

    @property
    def xp_needed(self):
        if self.mode == "shooter":
            return 8 + 6 * (self.level - 1)
        return 5 + 3 * (self.level - 1)

    @property
    def combo_cap(self):
        return 10 + 5 * self.lv("combo")

    @property
    def fever(self):
        return self.fever_timer > 0

    @property
    def bonus(self):
        return 2 if self.fever else 1

    # ------------------------------------------------------------ loop
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event.key)
                elif event.type == pygame.MOUSEMOTION:
                    if self.state == "upgrade":
                        self.hover_card(event.pos)
                    elif self.state == "title":
                        self.hover_mode(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "upgrade":
                        i = self.hover_card(event.pos)
                        if i is not None and self.cards_ready():
                            self.pick_card(i)
                    elif self.state == "title":
                        i = self.hover_mode(event.pos)
                        if i is not None:
                            self.start(MODE_ORDER[i])
            self.frame()
            self.clock.tick(FPS)

    def frame(self):
        # steady visual pulse (background, shards, HUD throb on this rhythm)
        self.beat = (1 - (self.tick * 1000 / FPS / BEAT_MS) % 1) ** 4
        if self.state == "playing":
            self.update()
        else:
            self.update_ambient()
        self.draw()
        self.tick += 1

    def quit(self):
        store_highscores(self.highscores)
        pygame.quit()
        sys.exit()

    def start(self, mode=None):
        if mode:
            self.mode = mode
            self.title_sel = MODE_ORDER.index(mode)
        self.reset()
        self.state = "playing"
        color = MODES[self.mode][2]
        self.rings.append(Ring(self.player.x, self.player.y, color, 120, life=30, width=4))
        self.flash(color, 60)
        self.show_banner(MODES[self.mode][0], {"standard": "Grab shards, dodge meteors",
                                               "dodge": "Survive as long as you can",
                                               "shooter": "Aim with the mouse, hold click to fire"}[self.mode], color, 110)

    def on_key(self, key):
        if key == pygame.K_b:
            self.bloom = not self.bloom
            return
        if key == pygame.K_m:
            self.sounds.muted = not self.sounds.muted
            return
        if self.state == "title":
            numbers = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
            if key in numbers:
                self.start(MODE_ORDER[numbers[key]])
            elif key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.title_sel = (self.title_sel - 1) % 3
            elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.title_sel = (self.title_sel + 1) % 3
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.start(MODE_ORDER[self.title_sel])
            elif key == pygame.K_ESCAPE:
                self.quit()
        elif self.state == "playing":
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "paused"
            elif key == pygame.K_SPACE and self.mode == "standard" and self.player.try_dash():
                self.on_dash()
        elif self.state == "paused":
            if key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = "playing"
            elif key == pygame.K_q:
                self.state = "title"
        elif self.state == "upgrade":
            if not self.cards_ready():
                return
            numbers = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
            if key in numbers and numbers[key] < len(self.cards):
                self.pick_card(numbers[key])
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.card_sel = (self.card_sel - 1) % len(self.cards)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.card_sel = (self.card_sel + 1) % len(self.cards)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.pick_card(self.card_sel)
        elif self.state == "gameover":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER) and self.tick - self.over_tick > 40:
                self.start()
            elif key == pygame.K_ESCAPE:
                self.state = "title"

    # ------------------------------------------------------------ effects
    def flash(self, color, alpha):
        if alpha >= self.flash_alpha:
            self.flash_color, self.flash_alpha = color, alpha

    def burst(self, x, y, color, n, speed=5):
        for _ in range(n):
            self.particles.append(Particle(x, y, color, speed, random.randint(25, 45), random.randint(2, 5)))

    def popup(self, x, y, text, color, font=None, life=50):
        self.texts.append(FloatText(x, y, text, color, font or FONT_SMALL, life))

    def show_banner(self, title, sub, color, dur=150):
        self.banner = [title, sub, color, 0, dur]

    def add_score(self, n):
        self.score += n
        self.score_pop = 1.0

    def add_fever(self, amount):
        if self.fever or self.mode == "dodge":
            return
        self.fever_meter += amount
        if self.fever_meter >= 1:
            self.start_fever()

    def start_fever(self):
        p = self.player
        self.fever_meter = 0
        self.fever_timer = self.FEVER_TIME
        p.fever = True
        sub = "Double fire rate - points x2" if self.mode == "shooter" else "Smash everything - points x2"
        self.show_banner("FEVER!", sub, PINK, 120)
        self.flash(WHITE, 170)
        self.shake = 14
        for i in range(6):
            self.rings.append(Ring(p.x, p.y, hue(i * 60), 90 + i * 45, life=26 + i * 4, width=5))
        for i in range(60):
            self.particles.append(Particle(p.x, p.y, hue(i * 6), 10, random.randint(30, 50), random.randint(2, 5)))
        self.sounds.play("fever")

    def prep_meteor(self, m):
        """Give meteors health in Shooter mode."""
        if self.mode == "shooter":
            d = self.difficulty
            # toughness keeps compounding so fully upgraded guns can't coast forever
            tough = (1 + 0.25 * d) * 1.06 ** d
            if m.kind == "hunter":
                hp = round(3 * tough)
            elif m.kind == "splitter":
                hp = round(m.r / 6 * tough)
            else:
                hp = max(1, round(m.r / 9 * tough))
            m.hp = m.max_hp = hp
            if m.speed > 7:  # tougher, not unfairly fast
                m.vx, m.vy = m.vx / m.speed * 7, m.vy / m.speed * 7
                m.speed = 7
        return m

    def smash(self, m, points):
        m.alive = False
        if points:
            points *= self.bonus
            self.add_score(points)
            self.popup(m.x, m.y - m.r, f"+{points}", ORANGE)
            self.add_fever(0.05)
        color = {"rock": ORANGE if m.hot else RED, "hunter": MAGENTA, "splitter": PURPLE}[m.kind]
        for _ in range(random.randint(4, 7)):
            self.debris.append(Debris(m.x, m.y, m.r, color))
        self.burst(m.x, m.y, color, 18)
        self.burst(m.x, m.y, RED if m.kind == "rock" else WHITE, 10, speed=3)
        self.rings.append(Ring(m.x, m.y, color, m.r * 2.5, life=18, width=3))
        if m.kind == "splitter":
            for _ in range(3):
                a = random.uniform(0, math.tau)
                child = Meteor(self.difficulty, "rock", pos=(m.x, m.y), vel=(math.cos(a) * 3.5, math.sin(a) * 3.5), r=random.randint(11, 15))
                child.safe = 30
                child.grazed = True
                self.new_meteors.append(self.prep_meteor(child))
        if self.mode != "shooter" or m.r >= 28 or m.kind != "rock":  # constant hitstop would feel stuttery
            self.hitstop = max(self.hitstop, 3)
        self.shake = max(self.shake, 5 if self.mode == "shooter" else 8)
        self.sounds.play("hit")

    def graze(self, m):
        """Near miss: reward skimming past a meteor without touching it."""
        p = self.player
        m.grazed = True
        self.grazes += 1
        dd = self.lv("daredevil")
        mult = max(1, min(self.combo, self.combo_cap))
        pts = int(15 * mult * (1 + dd) * self.bonus)
        self.add_score(pts)
        if self.combo > 0:
            self.combo_timer = int(120 * (1 + 0.5 * self.lv("combo")))
        self.add_fever(0.12 * (1 + 0.5 * dd))
        mx, my = (m.x + p.x) / 2, (m.y + p.y) / 2
        self.popup(mx, my - 20, f"CLOSE! +{pts}", WHITE, FONT_MED, 45)
        for _ in range(12):
            self.particles.append(Particle(mx, my, random.choice((WHITE, CYAN)), 6, random.randint(12, 22), 2))
        self.rings.append(Ring(mx, my, WHITE, 40, life=12, width=2))
        self.slowmo = 12
        self.shake = max(self.shake, 4)
        self.sounds.play("graze")

    def update_effects(self):
        for group in (self.particles, self.debris, self.rings, self.texts):
            for o in group:
                o.update()
        self.particles = [p for p in self.particles if p.life > 0][-900:]
        self.debris = [d for d in self.debris if d.life > 0]
        self.rings = [r for r in self.rings if r.life > 0]
        self.texts = [t for t in self.texts if t.life > 0]
        self.decay_screen()

    def decay_screen(self):
        if self.shake > 0:
            self.shake -= 1
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 9)
        self.score_pop = max(0.0, self.score_pop - 0.08)
        self.combo_pop = max(0.0, self.combo_pop - 0.08)

    def drift_stars(self, speed, player):
        for s in self.stars:
            s[1] += s[2] * speed
            s[0] -= player.vx * s[2] * 0.05
            s[1] -= player.vy * s[2] * 0.05
            s[0] %= WIDTH
            s[1] %= HEIGHT

    # ------------------------------------------------------------ update
    def update_ambient(self):
        if self.state != "upgrade":
            for s in self.stars:
                s[1] = (s[1] + s[2] * 0.15) % HEIGHT
        if self.state in ("title", "gameover"):
            if self.state == "title":
                self.title_spawn -= 1
                if self.title_spawn <= 0 and len(self.meteors) < 8:
                    self.meteors.append(Meteor(0, random.choice(("rock", "rock", "rock", "splitter", "hunter"))))
                    self.title_spawn = 70
            for m in self.meteors:
                m.update(1.0, self.particles)
                if m.kind == "hunter":
                    m.home = 0
            self.meteors = [m for m in self.meteors if m.alive]
            for b in self.bullets:
                b.update()
            self.bullets = [b for b in self.bullets if b.alive]
        self.update_effects()

    def spawn_meteor(self):
        d = self.difficulty
        r = random.random()
        if d > 2 and r < 0.08:
            kind = "hunter"
        elif d > 1 and r < 0.22:
            kind = "splitter"
        else:
            kind = "rock"
        self.meteors.append(self.prep_meteor(Meteor(d, kind)))

    def spawn_dodge(self):
        """Dodge mode: a never-ending meteor shower that keeps getting denser and faster."""
        t = self.time_alive / 60
        if self.time_alive % (60 * 15) == 0:
            self.popup(WIDTH / 2, 90, f"{int(t)} SECONDS", YELLOW, FONT_MED, 70)
            self.flash(YELLOW, 40)
            self.sounds.play("survived")
        self.spawn_timer -= 1
        if self.spawn_timer > 0:
            return
        self.spawn_timer = max(2, int(9 - t / 7))
        spread = min(3.5, 0.8 + t / 25)
        vy = min(13.0, 4.5 + t * 0.07) + random.uniform(0, 2.5)
        r = random.randint(10, int(min(34, 22 + t / 5)))
        x = random.uniform(-40, WIDTH + 40)
        self.meteors.append(Meteor(self.difficulty, "rock", pos=(x, -r - 10), vel=(random.uniform(-spread, spread), vy), r=r))

    def update_event(self):
        p = self.player
        if self.event is None:
            if self.time_alive >= self.next_event:
                kind = random.choice(list(EVENTS))
                name, sub, color = EVENTS[kind]
                self.event = {"kind": kind, "t": 0}
                self.show_banner(name, sub, color)
                self.sounds.play("power" if kind == "storm" else "alarm")
            return
        e = self.event
        e["t"] += 1
        t = e["t"] - 90  # 1.5s warning before it starts
        if t < 0:
            return
        if t < 60 * 7:
            if e["kind"] == "shower" and t % 5 == 0:
                x = random.uniform(0, WIDTH)
                vel = (random.uniform(-1.2, 1.2), 6 + random.random() * 2 + self.difficulty * 0.3)
                m = Meteor(self.difficulty, "rock", pos=(x, -30), vel=vel, r=random.randint(12, 22))
                if self.mode == "shooter":
                    m.hp = m.max_hp = 1  # shower rocks pop in one shot
                self.meteors.append(m)
            elif e["kind"] == "storm" and t % 7 == 0:
                pk = Pickup("shard", life=60 * 4, avoid=(p.x, p.y))
                self.pickups.append(pk)
                self.rings.append(Ring(pk.x, pk.y, GOLD, 26, life=14, width=2))
            elif e["kind"] == "hunters" and t % 50 == 0 and t <= 50 * (2 + int(self.difficulty // 2)):
                self.meteors.append(self.prep_meteor(Meteor(self.difficulty, "hunter")))
            return
        if e["kind"] == "shower":
            bonus = 250 * self.bonus
            self.add_score(bonus)
            self.popup(p.x, p.y - 50, f"SURVIVED! +{bonus}", YELLOW, FONT_MED, 80)
            self.rings.append(Ring(p.x, p.y, YELLOW, 160, life=30, width=5))
            self.sounds.play("survived")
        self.event = None
        self.next_event = self.time_alive + 60 * random.randint(20, 30)

    def update(self):
        if self.hitstop > 0:
            self.hitstop -= 1
            self.decay_screen()
            return
        self.time_alive += 1
        p = self.player
        dodge = self.mode == "dodge"
        shooter = self.mode == "shooter"
        slow = 1.0
        if self.slow_timer > 0:
            self.slow_timer -= 1
            slow = 0.4 - 0.08 * self.lv("chrono")
        if self.slowmo > 0:
            self.slowmo -= 1
            slow *= 0.45
        self.drift_stars((1.4 if dodge else 0.5) * slow * (2 if self.fever else 1), p)

        if self.banner:
            self.banner[3] += 1
            if self.banner[3] >= self.banner[4]:
                self.banner = None

        if self.fever_timer > 0:
            self.fever_timer -= 1
            for _ in range(2):
                self.particles.append(Particle(p.x, p.y, hue(self.tick * 8 + random.randint(0, 90)), 3, 25, 3))
            if self.fever_timer == 0:
                p.fever = False
                self.popup(p.x, p.y - 40, "FEVER OVER", GREY, FONT_MED, 50)

        if shooter:
            mx, my = pygame.mouse.get_pos()
            p.aim = math.atan2(my - p.y, mx - p.x)
        keys = pygame.key.get_pressed()
        events = p.update(keys, self.particles)
        if "armor" in events:
            self.popup(p.x, p.y - 30, "+ARMOR", STEEL)
            self.rings.append(Ring(p.x, p.y, STEEL, 60, life=24, width=3))
            self.sounds.play("power")
        if "dash_ready" in events:
            self.rings.append(Ring(p.x, p.y, CYAN, 34, life=14, width=2, start_r=12))

        if dodge:
            self.spawn_dodge()
        else:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.spawn_meteor()
                if shooter and random.random() < min(0.7, (self.difficulty - 6) * 0.05):
                    self.spawn_meteor()  # late game: meteors arrive in pairs
                base = 45 if shooter else 55
                self.spawn_timer = max(10 if shooter else 12, int(base - self.difficulty * 6))
                if self.fever:
                    self.spawn_timer //= 2
            self.update_event()
        for m in self.meteors:
            m.update(slow, self.particles, (p.x, p.y))

        if shooter:
            self.update_shooting(keys)

        if not dodge:
            lucky = self.lv("lucky")
            if random.random() < 0.0025 * (1 + lucky) and not any(pk.kind != "shard" for pk in self.pickups):
                self.pickups.append(Pickup(random.choice(("shield", "slow")), life=60 * (9 + 4 * lucky), avoid=(p.x, p.y)))

        for pk in self.pickups:
            pk.update()
            d = math.hypot(pk.x - p.x, pk.y - p.y)
            pk.pulled = False
            if pk.kind == "shard" and p.magnet and 1 < d < p.magnet:
                pull = 2 + 7 * (1 - d / p.magnet)
                pk.x += (p.x - pk.x) / d * pull
                pk.y += (p.y - pk.y) / d * pull
                pk.pulled = True
            if d < pk.r + p.RADIUS + 4 and not pk.taken:
                pk.taken = True
                self.collect(pk)
        self.pickups = [pk for pk in self.pickups if pk.alive]
        if self.mode == "standard":
            while sum(1 for pk in self.pickups if pk.kind == "shard" and pk.life is None) < 3 + self.lv("swarm"):
                self.pickups.append(Pickup(avoid=(p.x, p.y)))

        if self.state != "playing":  # leveled up this frame
            self.update_effects()
            return

        if self.combo_timer > 0:
            self.combo_timer -= 1
        elif self.combo:
            if self.combo >= 5:
                self.popup(p.x, p.y - 30, "combo lost", GREY)
            self.combo = 0

        # collisions and near misses
        for m in self.meteors:
            if not m.alive or m.safe > 0:
                continue
            d = math.hypot(m.x - p.x, m.y - p.y)
            hit_d = m.r * 0.85 + p.hit_radius
            if d >= hit_d:
                if not dodge and not m.grazed and d < hit_d + 22 and not p.smashing and p.invuln == 0:
                    self.graze(m)
                continue
            if p.smashing:
                self.smash(m, Meteor.POINTS[m.kind])
            elif p.invuln > 0:
                pass
            elif p.armor > 0:
                p.armor -= 1
                p.armor_regen = 0
                p.invuln = 90
                self.smash(m, 0)
                self.flash(RED, 110)
                self.shake = 16
                self.popup(p.x, p.y - 30, "ARMOR BROKEN", STEEL)
                self.sounds.play("armor")
            else:
                self.game_over()
                return
        self.meteors = [m for m in self.meteors if m.alive] + self.new_meteors
        self.new_meteors = []

        if dodge:
            self.score = self.time_alive // 6  # tenths of a second survived
        elif self.time_alive % 30 == 0:
            self.score += 1
        self.update_effects()

    # ------------------------------------------------------------ shooter
    def update_shooting(self, keys):
        if self.fire_cd > 0:
            self.fire_cd -= 1
        firing = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
        if firing and self.fire_cd <= 0:
            self.fire()
            delay = max(3, int(14 * 0.8 ** self.lv("rapid")))
            self.fire_cd = max(2, delay // 2) if self.fever else delay

        homing = self.lv("homing")
        for b in self.bullets:
            if homing and self.meteors:
                target = min(self.meteors, key=lambda m: (m.x - b.x) ** 2 + (m.y - b.y) ** 2)
                if (target.x - b.x) ** 2 + (target.y - b.y) ** 2 < 280 ** 2:
                    b.vx, b.vy = turn_toward(b.vx, b.vy, target.x - b.x, target.y - b.y, 0.07 * homing)
            b.update()
            if not b.alive:
                continue
            for m in self.meteors:
                if not m.alive or id(m) in b.hit:
                    continue
                if (m.x - b.x) ** 2 + (m.y - b.y) ** 2 < (m.r + 4) ** 2:
                    b.hit.add(id(m))
                    self.bullet_hit(m, b)
                    if len(b.hit) > b.pierce:
                        b.alive = False
                        break
        self.bullets = [b for b in self.bullets if b.alive]

    def fire(self):
        p = self.player
        lv = self.lv
        count = 1 + lv("spread")
        speed = 11 * (1 + 0.3 * lv("velocity"))
        life = int(55 * (1 + 0.3 * lv("velocity")))
        angles = [p.angle + (i - (count - 1) / 2) * 0.13 for i in range(count)]
        if lv("rear"):
            angles.append(p.angle + math.pi)
        for a in angles:
            crit = random.random() < 0.12 * lv("crit")
            dmg = (1 + lv("power")) * (3 if crit else 1)
            nx = p.x + math.cos(a) * p.RADIUS * 1.3
            ny = p.y + math.sin(a) * p.RADIUS * 1.3
            self.bullets.append(Bullet(nx, ny, a, speed, dmg, lv("pierce"), life, crit))
        mx = p.x + math.cos(p.angle) * p.RADIUS * 1.5
        my = p.y + math.sin(p.angle) * p.RADIUS * 1.5
        for _ in range(3):
            self.particles.append(Particle(mx, my, YELLOW, 2.5, 8, 2))
        p.vx -= math.cos(p.angle) * 0.12  # a little recoil
        p.vy -= math.sin(p.angle) * 0.12
        self.sounds.play("shoot")

    def bullet_hit(self, m, b):
        self.damage(m, b.dmg, b.crit, b)
        for _ in range(4):
            self.particles.append(Particle(b.x, b.y, GOLD if b.crit else YELLOW, 3, 12, 2))
        ex = self.lv("explosive")
        if ex:
            radius = 28 + 14 * ex
            self.rings.append(Ring(b.x, b.y, PINK, radius, life=14, width=3))
            self.burst(b.x, b.y, PINK, 8, speed=4)
            for o in self.meteors:
                if o is not m and o.alive and math.hypot(o.x - b.x, o.y - b.y) < radius + o.r:
                    self.damage(o, max(1, b.dmg // 2), False, None)

    def damage(self, m, dmg, crit, bullet):
        if not m.alive:
            return
        m.hp -= dmg
        m.hit_flash = 5
        if bullet is not None:  # knockback, less for big rocks
            push = 0.25 * 14 / max(14, m.r)
            m.x += bullet.vx * push
            m.y += bullet.vy * push
        if crit:
            self.popup(m.x, m.y - m.r - 10, f"CRIT {dmg}", GOLD, life=35)
        if m.hp <= 0:
            self.kill(m)
        else:
            self.sounds.play("ping")

    def kill(self, m):
        self.kills += 1
        self.combo += 1
        self.combo_pop = 1.0
        self.combo_timer = int(120 * (1 + 0.5 * self.lv("combo")))
        mult = min(self.combo, self.combo_cap)
        self.smash(m, Meteor.POINTS[m.kind] * mult)
        drops = 1 + (m.r >= 26) + (m.kind != "rock")
        for _ in range(drops):
            self.pickups.append(Pickup("shard", life=60 * 8, pos=(m.x + random.uniform(-14, 14), m.y + random.uniform(-14, 14))))
        if self.combo >= 5 and self.combo % 5 == 0:
            p = self.player
            self.popup(p.x, p.y - 40, f"x{mult} KILL STREAK!", YELLOW, FONT_MED, 60)
            self.rings.append(Ring(p.x, p.y, YELLOW, 80, life=20, width=3))

    # ------------------------------------------------------------ standard
    def on_dash(self):
        p = self.player
        self.sounds.play("dash")
        self.rings.append(Ring(p.x, p.y, CYAN, 50, life=16, width=3))
        nova = self.lv("nova")
        if nova:
            radius = 110 + 50 * nova
            self.rings.append(Ring(p.x, p.y, PINK, radius, life=24, width=7))
            self.rings.append(Ring(p.x, p.y, WHITE, radius * 0.7, life=18, width=3))
            self.burst(p.x, p.y, PINK, 30, speed=8)
            self.flash(PINK, 50)
            self.sounds.play("nova")
            for m in self.meteors:
                if m.alive and m.safe == 0 and math.hypot(m.x - p.x, m.y - p.y) < radius + m.r:
                    self.smash(m, Meteor.POINTS[m.kind])

    def collect(self, pk):
        p = self.player
        if pk.kind == "shard" and self.mode == "shooter":
            self.xp += 1
            self.add_score(5 * self.bonus)
            self.add_fever(0.02)
            self.burst(pk.x, pk.y, GOLD, 8)
            self.sounds.play("pickup", min(9, self.xp * 10 // self.xp_needed))
            if self.xp >= self.xp_needed:
                self.level_up()
        elif pk.kind == "shard":
            self.combo += 1
            self.combo_pop = 1.0
            self.combo_timer = int(120 * (1 + 0.5 * self.lv("combo")))
            mult = min(self.combo, self.combo_cap)
            pts = int(10 * (1 + 0.5 * self.lv("greed")) * mult * self.bonus)
            self.add_score(pts)
            self.xp += 1
            self.add_fever(0.05)
            self.popup(pk.x, pk.y - 14, f"+{pts}", GOLD)
            if self.combo >= 5 and self.combo % 5 == 0:
                self.popup(p.x, p.y - 40, f"x{mult} COMBO!", YELLOW, FONT_MED, 60)
                self.rings.append(Ring(p.x, p.y, YELLOW, 80, life=20, width=3))
                self.flash(GOLD, 40)
            self.burst(pk.x, pk.y, GOLD, 14)
            self.rings.append(Ring(pk.x, pk.y, GOLD, 30, life=14, width=2))
            self.sounds.play("pickup", self.combo - 1)
            if self.xp >= self.xp_needed:
                self.level_up()
        elif pk.kind == "shield":
            p.shield = 60 * 5
            self.burst(pk.x, pk.y, GREEN, 30)
            self.rings.append(Ring(pk.x, pk.y, GREEN, 70, life=24, width=4))
            self.popup(pk.x, pk.y - 20, "SHIELD!", GREEN, FONT_MED)
            self.flash(GREEN, 50)
            self.sounds.play("power")
        elif pk.kind == "slow":
            self.slow_timer = 60 * (5 + 3 * self.lv("chrono"))
            self.burst(pk.x, pk.y, PURPLE, 30)
            self.rings.append(Ring(pk.x, pk.y, PURPLE, 400, life=40, width=6))
            self.popup(pk.x, pk.y - 20, "SLOW TIME!", PURPLE, FONT_MED)
            self.flash(PURPLE, 60)
            self.sounds.play("power")

    # ------------------------------------------------------------ upgrades
    def level_up(self):
        p = self.player
        self.xp -= self.xp_needed
        self.level += 1
        self.flash(GOLD, 140)
        for i in range(3):
            self.rings.append(Ring(p.x, p.y, GOLD, 120 + i * 70, life=30 + i * 8, width=5))
        self.burst(p.x, p.y, GOLD, 60, speed=9)
        self.burst(p.x, p.y, WHITE, 25, speed=6)
        self.sounds.play("levelup")
        self.open_upgrades()

    def open_upgrades(self):
        available = [k for k, u in self.pool.items() if self.lv(k) < u[2]]
        if not available:
            self.add_score(500)
            self.popup(self.player.x, self.player.y - 40, "MAXED! +500", GOLD, FONT_MED, 70)
            return
        self.cards = random.sample(available, min(3, len(available)))
        self.card_sel = 0
        self.card_rects = []
        self.card_open_tick = self.tick
        self.state = "upgrade"

    def cards_ready(self):
        return self.tick - self.card_open_tick >= 25  # stops accidental picks

    def hover_card(self, pos):
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(pos):
                self.card_sel = i
                return i
        return None

    def hover_mode(self, pos):
        for i, rect in enumerate(self.mode_rects):
            if rect.collidepoint(pos):
                self.title_sel = i
                return i
        return None

    def pick_card(self, i):
        key = self.cards[i]
        name, _, _, color, _ = self.pool[key]
        p = self.player
        self.levels[key] = self.lv(key) + 1
        if key == "armor":
            p.armor += 1
        p.recompute(self.levels)
        p.invuln = max(p.invuln, 45)  # brief grace period after choosing
        self.sounds.play("select")
        self.flash(color, 90)
        self.rings.append(Ring(p.x, p.y, color, 160, life=30, width=6))
        self.burst(p.x, p.y, color, 40, speed=7)
        self.popup(p.x, p.y - 40, f"{name.upper()} {self.lv(key)}", color, FONT_MED, 70)
        self.state = "playing"
        if self.xp >= self.xp_needed:
            self.level_up()

    def game_over(self):
        p = self.player
        p.fever = False
        self.fever_timer = 0
        self.banner = None
        self.burst(p.x, p.y, CYAN, 60, speed=7)
        self.burst(p.x, p.y, ORANGE, 50, speed=9)
        self.burst(p.x, p.y, WHITE, 20, speed=4)
        for _ in range(8):
            self.debris.append(Debris(p.x, p.y, 30, CYAN, fill=(60, 70, 100)))
        for i in range(3):
            self.rings.append(Ring(p.x, p.y, (ORANGE, CYAN, WHITE)[i], 150 + i * 80, life=35 + i * 10, width=6))
        self.flash(WHITE, 200)
        self.shake = 30
        self.sounds.play("death")
        if self.score > self.highscore:
            self.highscores[self.mode] = self.score
            self.new_record = True
            store_highscores(self.highscores)
        self.state = "gameover"
        self.over_tick = self.tick

    # ------------------------------------------------------------ drawing
    def apply_bloom(self, surf):
        small = pygame.transform.smoothscale(surf, (WIDTH // 4, HEIGHT // 4))
        small.fill((45, 45, 45), special_flags=pygame.BLEND_SUB)
        tiny = pygame.transform.smoothscale(small, (WIDTH // 8, HEIGHT // 8))
        big = pygame.transform.smoothscale(tiny, (WIDTH, HEIGHT))
        surf.blit(big, (0, 0), special_flags=pygame.BLEND_ADD)

    def edge_glow(self, color, k):
        s = self.edge_small.copy()
        s.fill(scale_color(color, k), special_flags=pygame.BLEND_MULT)
        self.screen.blit(pygame.transform.smoothscale(s, (WIDTH, HEIGHT)), (0, 0), special_flags=pygame.BLEND_ADD)

    def draw(self):
        p = self.player
        w = self.world
        playing = self.state == "playing"
        nx = max(-120, min(0, -60 + (WIDTH / 2 - p.x) * 0.06))
        ny = max(-120, min(0, -60 + (HEIGHT / 2 - p.y) * 0.06))
        w.blit(self.nebula, (nx, ny))

        # background pulses - harder with combo and fever
        if self.state in ("playing", "title"):
            amount = 5 + (min(self.combo, 20) * 0.5 if playing else 0) + (6 if self.fever else 0)
            col = hue(self.tick * 4, 55) if self.fever else (90, 60, 170)
            w.fill(scale_color(col, self.beat * amount / 100), special_flags=pygame.BLEND_ADD)

        streak = playing and (p.dashing or self.fever)
        for x, y, z in self.stars:
            c = 60 + z * 55
            color = (c, c, min(255, c + 30))
            if streak and z > 1:
                pygame.draw.line(w, scale_color(color, 0.7), (x, y), (x - p.vx * z * 0.35, y - p.vy * z * 0.35 - (6 if self.fever else 0)), 1)
            else:
                w.fill(color, (x, y, z, z))

        if self.slow_timer > 0 and self.state != "title":
            w.fill((22, 8, 36), special_flags=pygame.BLEND_ADD)

        if self.state != "title":
            for pk in self.pickups:
                if pk.pulled:
                    pygame.draw.line(w, scale_color(GOLD, 0.3), (pk.x, pk.y), (p.x, p.y), 1)
                pk.draw(w, self.beat)
        for m in self.meteors:
            m.draw(w)
        for b in self.bullets:
            b.draw(w)
        for d in self.debris:
            d.draw(w)
        for part in self.particles:
            part.draw(w)
        for r in self.rings:
            r.draw(w)
        if self.state in ("playing", "paused", "upgrade"):
            p.draw(w, self.tick)
        for t in self.texts:
            t.draw(w)

        if self.bloom:
            self.apply_bloom(w)

        ox = oy = 0
        if self.shake > 0:
            ox = random.randint(-self.shake, self.shake) // 2
            oy = random.randint(-self.shake, self.shake) // 2
        self.screen.fill((0, 0, 0))
        self.screen.blit(w, (ox, oy))
        self.screen.blit(self.vignette, (0, 0))

        if playing:
            if self.fever:
                self.edge_glow(hue(self.tick * 5), 0.45 + 0.4 * self.beat)
            elif self.combo >= 10:
                self.edge_glow(GOLD, 0.15 + 0.25 * self.beat)
            elif self.event and self.event["kind"] in ("shower", "hunters"):
                self.edge_glow(RED, 0.12 + 0.18 * self.beat)

        if self.flash_alpha > 0:
            self.flash_surf.fill(self.flash_color)
            self.flash_surf.set_alpha(self.flash_alpha)
            self.screen.blit(self.flash_surf, (0, 0))

        if self.state == "title":
            self.draw_title()
        else:
            if playing:
                self.draw_warnings()
            self.draw_hud()
            if self.banner and self.state in ("playing", "paused"):
                self.draw_banner()
            if playing and self.mode == "shooter":
                self.draw_crosshair()
            if self.state == "paused":
                self.overlay("PAUSED", WHITE, ["P / ESC to resume", "Q to quit to title"])
            elif self.state == "upgrade":
                self.draw_upgrades()
            elif self.state == "gameover":
                self.draw_gameover()

        # hide the system cursor while aiming with the crosshair
        want_cursor = not (playing and self.mode == "shooter")
        if want_cursor != self.cursor_visible:
            pygame.mouse.set_visible(want_cursor)
            self.cursor_visible = want_cursor

        pygame.display.flip()

    def draw_crosshair(self):
        mx, my = pygame.mouse.get_pos()
        c = hue(self.tick * 6) if self.fever else CYAN
        pygame.draw.circle(self.screen, c, (mx, my), 11, 2)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pygame.draw.line(self.screen, c, (mx + dx * 6, my + dy * 6), (mx + dx * 16, my + dy * 16), 2)
        pygame.draw.circle(self.screen, WHITE, (mx, my), 2)

    def draw_gameover(self):
        if self.mode == "dodge":
            lines = [f"You survived {self.score / 10:.1f} seconds"]
        elif self.mode == "shooter":
            lines = [f"Score: {self.score}   Level: {self.level}   Kills: {self.kills}"]
        else:
            lines = [f"Score: {self.score}   Level: {self.level}   Close calls: {self.grazes}"]
        lines.append("NEW HIGH SCORE!" if self.new_record else f"Best: {fmt_score(self.mode, self.highscore)}")
        lines += ["", "ENTER to play again", "ESC for mode select"]
        self.overlay("GAME OVER", RED, lines)

    def draw_banner(self):
        title, sub, color, t, dur = self.banner
        ein = 1 - (1 - min(1.0, t / 14)) ** 3
        eout = max(0.0, (t - (dur - 14)) / 14) ** 2
        x = WIDTH / 2 + (1 - ein) * WIDTH - eout * WIDTH
        a = min(ein, 1 - eout)
        self.band.fill((0, 0, 0, int(150 * a)))
        stripe = scale_color(color, a)
        pygame.draw.line(self.band, stripe, (0, 1), (WIDTH, 1), 3)
        pygame.draw.line(self.band, stripe, (0, 98), (WIDTH, 98), 3)
        self.screen.blit(self.band, (0, 140))
        glow_text(self.screen, title, FONT_BIG, color, (x, 180))
        self.text(sub, FONT_SMALL, WHITE, (x + (1 - ein) * 200, 222))

    def draw_warnings(self):
        """Arrows at the screen edge for meteors about to enter."""
        for m in self.meteors:
            if 0 <= m.x <= WIDTH and 0 <= m.y <= HEIGHT:
                continue
            cx = max(16, min(WIDTH - 16, m.x))
            cy = max(16, min(HEIGHT - 16, m.y))
            dist = math.hypot(m.x - cx, m.y - cy)
            k = max(0.0, 1 - dist / 90)
            if k <= 0:
                continue
            k *= 0.6 + 0.4 * math.sin(self.tick * 0.4)
            a = math.atan2(m.y - cy, m.x - cx)
            s = 11 if m.kind == "hunter" else 9
            pts = [
                (cx + math.cos(a) * s, cy + math.sin(a) * s),
                (cx + math.cos(a + 2.4) * s, cy + math.sin(a + 2.4) * s),
                (cx + math.cos(a - 2.4) * s, cy + math.sin(a - 2.4) * s),
            ]
            pygame.draw.polygon(self.screen, scale_color(MAGENTA if m.kind == "hunter" else RED, max(0.2, k)), pts)

    def draw_score(self, label, value_text, color=WHITE):
        surf = FONT_MED.render(f"{label} {value_text}", True, color if self.score_pop < 0.3 else YELLOW)
        s = 1 + 0.25 * self.score_pop + 0.04 * self.beat
        surf = pygame.transform.smoothscale(surf, (int(surf.get_width() * s), int(surf.get_height() * s)))
        self.screen.blit(surf, (20, 18 - (s - 1) * 10))

    def draw_hud(self):
        p = self.player
        dodge = self.mode == "dodge"

        if dodge:
            self.draw_score("TIME", f"{self.score / 10:.1f}s")
            self.text(f"BEST {fmt_score('dodge', self.highscore)}", FONT_SMALL, GREY, (20, 52), anchor="topleft")
            danger = min(1.0, self.time_alive / (60 * 90))
            self.text("SHOWER INTENSITY", FONT_TINY, GREY, (WIDTH - 20, 18), anchor="topright")
            pygame.draw.rect(self.screen, (60, 30, 40), (WIDTH - 180, 36, 160, 8), 1)
            pygame.draw.rect(self.screen, RED, (WIDTH - 180, 36, 160 * danger, 8))
            return

        # XP bar across the top
        frac = min(1.0, self.xp / self.xp_needed)
        pygame.draw.rect(self.screen, (30, 30, 50), (0, 0, WIDTH, 6))
        pygame.draw.rect(self.screen, GOLD, (0, 0, WIDTH * frac, 6))
        if frac > 0:
            add_glow(self.screen, WIDTH * frac, 3, 16, (110, 80, 25))
        self.text(f"LEVEL {self.level}", FONT_SMALL, GOLD, (WIDTH / 2, 22))

        # score counts up and pops when it grows
        self.shown_score += (self.score - self.shown_score) * 0.18
        if abs(self.score - self.shown_score) < 1:
            self.shown_score = self.score
        self.draw_score("SCORE", int(round(self.shown_score)))
        self.text(f"BEST {self.highscore}", FONT_SMALL, GREY, (20, 52), anchor="topleft")

        for i in range(p.max_armor):
            cx, cy = 30 + i * 24, 86
            pts = [(cx + math.cos(j * math.pi / 3 + math.pi / 6) * 9, cy + math.sin(j * math.pi / 3 + math.pi / 6) * 9) for j in range(6)]
            if i < p.armor:
                pygame.draw.polygon(self.screen, STEEL, pts)
            else:
                pygame.draw.polygon(self.screen, (60, 70, 100), pts, 2)
                regen = p.armor_regen / (60 * 25)
                if i == p.armor:
                    pygame.draw.rect(self.screen, STEEL, (cx - 9, cy + 13, 18 * regen, 3))

        # combo (color heats up with the multiplier)
        if self.combo > 1:
            mult = min(self.combo, self.combo_cap)
            color = GOLD if mult < 5 else ORANGE if mult < 10 else PINK
            label = "STREAK" if self.mode == "shooter" else "COMBO"
            surf = FONT_MED.render(f"x{mult} {label}", True, color)
            s = 1 + 0.4 * self.combo_pop + 0.05 * self.beat * min(1, mult / 10)
            surf = pygame.transform.smoothscale(surf, (int(surf.get_width() * s), int(surf.get_height() * s)))
            self.screen.blit(surf, surf.get_rect(topright=(WIDTH - 20, 16)))
            full = 120 * (1 + 0.5 * self.lv("combo"))
            bw = 120 * self.combo_timer / full
            pygame.draw.rect(self.screen, color, (WIDTH - 20 - bw, 50, bw, 3))

        # fever meter
        fw, fx, fy = 160, WIDTH - 20 - 160, 62
        if self.fever:
            k = self.fever_timer / self.FEVER_TIME
            for i in range(int(fw * k)):
                self.screen.fill(hue(self.tick * 6 + i * 3), (fx + fw - fw * k + i, fy, 1, 8))
            glow_text(self.screen, "FEVER x2", FONT_SMALL, PINK, (fx + fw / 2, fy + 24), passes=1)
        else:
            pygame.draw.rect(self.screen, (60, 40, 70), (fx, fy, fw, 8), 1)
            pygame.draw.rect(self.screen, PINK, (fx, fy, fw * self.fever_meter, 8))
            self.text("FEVER", FONT_TINY, scale_color(PINK, 0.8), (fx - 8, fy + 4), anchor="midright")

        # owned upgrades
        x, y = 20, HEIGHT - 14
        for key, (_, _, _, color, short) in self.pool.items():
            if self.lv(key):
                surf = FONT_TINY.render(f"{short} {self.lv(key)}", True, color)
                if x + surf.get_width() + 12 > WIDTH / 2 - 90:  # wrap before the dash meter
                    x, y = 20, y - 28
                chip = surf.get_rect(bottomleft=(x + 6, y))
                pygame.draw.rect(self.screen, scale_color(color, 0.25), chip.inflate(10, 6), border_radius=6)
                self.screen.blit(surf, chip)
                x = chip.right + 12

        bw = 140
        bx = WIDTH / 2 - bw / 2
        if self.mode == "standard":  # dash meter
            dfrac = 1 - p.dash_cd / max(1, p.dash_cooldown)
            ready = dfrac >= 1
            pygame.draw.rect(self.screen, GREY, (bx, HEIGHT - 30, bw, 10), 1)
            pygame.draw.rect(self.screen, CYAN if ready else GREY, (bx, HEIGHT - 30, bw * dfrac, 10))
            if ready:
                add_glow(self.screen, WIDTH / 2, HEIGHT - 25, 40, (10, 40, 55))
            self.text("DASH", FONT_SMALL, CYAN if ready else GREY, (WIDTH / 2, HEIGHT - 44))
        else:
            self.text(f"KILLS {self.kills}", FONT_SMALL, ORANGE, (WIDTH / 2, HEIGHT - 30))
        y = HEIGHT - 60
        if p.shield > 0:
            pygame.draw.rect(self.screen, GREEN, (bx, y, bw * p.shield / 300, 4))
            y -= 8
        if self.slow_timer > 0:
            pygame.draw.rect(self.screen, PURPLE, (bx, y, bw * self.slow_timer / (60 * (5 + 3 * self.lv("chrono"))), 4))

    def draw_upgrades(self):
        self.shade.fill((0, 0, 0, 150))
        self.screen.blit(self.shade, (0, 0))
        glow_text(self.screen, "LEVEL UP!", FONT_BIG, GOLD, (WIDTH / 2, 90))
        self.text("Choose an upgrade  (1 / 2 / 3, arrows + ENTER, or click)", FONT_SMALL, GREY, (WIDTH / 2, 142))

        n = len(self.cards)
        cw, ch, gap = 240, 300, 30
        total = n * cw + (n - 1) * gap
        x0 = WIDTH / 2 - total / 2
        base_y = HEIGHT / 2 - ch / 2 + 50
        self.card_rects = []
        for i, key in enumerate(self.cards):
            name, desc, max_lv, color, short = self.pool[key]
            t = max(0.0, min(1.0, (self.tick - self.card_open_tick - i * 5) / 22))
            ease = 1 - (1 - t) ** 3
            sel = i == self.card_sel and self.cards_ready()
            y = base_y + (1 - ease) * HEIGHT - (14 if sel else 0)
            rect = pygame.Rect(int(x0 + i * (cw + gap)), int(y), cw, ch)
            self.card_rects.append(rect)

            if sel:
                add_glow(self.screen, rect.centerx, rect.centery, 190, scale_color(color, 0.3))
            card = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.rect(card, (18, 22, 46, 235), card.get_rect(), border_radius=16)
            self.screen.blit(card, rect)
            pygame.draw.rect(self.screen, color if sel else (70, 70, 110), rect, 3 if sel else 2, border_radius=16)

            icon = (rect.centerx, rect.top + 72)
            add_glow(self.screen, icon[0], icon[1], 60, scale_color(color, 0.35))
            pygame.draw.circle(self.screen, scale_color(color, 0.25), icon, 36)
            pygame.draw.circle(self.screen, color, icon, 36, 3)
            if sel:
                for j in range(6):
                    a = self.tick * 0.04 + j * math.tau / 6
                    pygame.draw.circle(self.screen, color, (int(icon[0] + math.cos(a) * 46), int(icon[1] + math.sin(a) * 46)), 2)
            self.text(short, FONT_MED, color, icon)

            self.text(name, FONT_MED, WHITE, (rect.centerx, rect.top + 136))
            for j, line in enumerate(wrap(desc, FONT_SMALL, cw - 30)):
                self.text(line, FONT_SMALL, GREY, (rect.centerx, rect.top + 172 + j * 24))

            cur = self.lv(key)
            pip_x = rect.centerx - (max_lv - 1) * 11
            for j in range(max_lv):
                c = (int(pip_x + j * 22), rect.bottom - 46)
                if j < cur:
                    pygame.draw.circle(self.screen, color, c, 6)
                elif j == cur:
                    k = 0.5 + 0.5 * math.sin(self.tick * 0.2)
                    pygame.draw.circle(self.screen, scale_color(color, 0.4 + 0.6 * k), c, 6)
                else:
                    pygame.draw.circle(self.screen, (70, 70, 110), c, 6, 2)
            self.text(f"[{i + 1}]", FONT_SMALL, GREY, (rect.centerx, rect.bottom - 20))

    def draw_title(self):
        bob = math.sin(self.tick * 0.05) * 6
        glow_text(self.screen, TITLE.upper(), FONT_BIG, CYAN, (WIDTH / 2, 90 + bob))
        self.text("Choose your mode", FONT_SMALL, GREY, (WIDTH / 2, 148))

        cw, ch, gap = 272, 180, 22
        x0 = WIDTH / 2 - (3 * cw + 2 * gap) / 2
        self.mode_rects = []
        for i, mode in enumerate(MODE_ORDER):
            name, desc, color = MODES[mode]
            sel = i == self.title_sel
            rect = pygame.Rect(int(x0 + i * (cw + gap)), 180 - (10 if sel else 0), cw, ch)
            self.mode_rects.append(rect)
            if sel:
                add_glow(self.screen, rect.centerx, rect.centery, 170, scale_color(color, 0.3))
            card = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.rect(card, (18, 22, 46, 225), card.get_rect(), border_radius=16)
            self.screen.blit(card, rect)
            pygame.draw.rect(self.screen, color if sel else (70, 70, 110), rect, 3 if sel else 2, border_radius=16)
            num = (rect.left + 26, rect.top + 26)
            pygame.draw.circle(self.screen, scale_color(color, 0.3), num, 15)
            pygame.draw.circle(self.screen, color, num, 15, 2)
            self.text(str(i + 1), FONT_SMALL, WHITE, num)
            if sel:
                glow_text(self.screen, name, FONT_MED, color, (rect.centerx, rect.top + 28), passes=1)
            else:
                self.text(name, FONT_MED, color, (rect.centerx, rect.top + 28))
            for j, line in enumerate(wrap(desc, FONT_SMALL, cw - 32)):
                self.text(line, FONT_SMALL, WHITE if sel else GREY, (rect.centerx, rect.top + 68 + j * 22))
            best = self.highscores.get(mode, 0)
            self.text(f"BEST  {fmt_score(mode, best)}", FONT_SMALL, GOLD if best else GREY, (rect.centerx, rect.bottom - 22))

        mode = MODE_ORDER[self.title_sel]
        color = MODES[mode][2]
        for i, (k, v) in enumerate(CONTROLS[mode]):
            y = 400 + i * 28
            self.text(k, FONT_SMALL, color, (WIDTH / 2 - 16, y), anchor="midright")
            self.text(v, FONT_SMALL, WHITE, (WIDTH / 2 + 16, y), anchor="midleft")
        if self.tick // 30 % 2 == 0:
            glow_text(self.screen, "Press 1 / 2 / 3  or  ENTER to play", FONT_MED, (150, 200, 230), (WIDTH / 2, HEIGHT - 80), passes=1)
        self.text("Arrows to browse  -  P pause  -  B bloom  -  M mute  -  ESC quit", FONT_TINY, GREY, (WIDTH / 2, HEIGHT - 36))

    def overlay(self, title, color, lines):
        self.shade.fill((0, 0, 0, 140))
        self.screen.blit(self.shade, (0, 0))
        glow_text(self.screen, title, FONT_BIG, color, (WIDTH / 2, HEIGHT / 2 - 90))
        for i, line in enumerate(lines):
            c = GOLD if "HIGH" in line else WHITE
            self.text(line, FONT_MED, c, (WIDTH / 2, HEIGHT / 2 - 10 + i * 36))

    def text(self, s, font, color, pos, anchor="center"):
        surf = font.render(s, True, color)
        self.screen.blit(surf, surf.get_rect(**{anchor: pos}))


def main():
    global FONT_BIG, FONT_MED, FONT_SMALL, FONT_TINY
    pygame.init()
    FONT_BIG = pygame.font.Font(None, 84)
    FONT_MED = pygame.font.Font(None, 36)
    FONT_SMALL = pygame.font.Font(None, 26)
    FONT_TINY = pygame.font.Font(None, 22)
    Game().run()


if __name__ == "__main__":
    main()
