import tkinter as tk
import random, math, time

WIDTH, HEIGHT = 800, 600
TILE, COLS, ROWS = 30, 20, 20
MAX_FLOOR = 12

SHOP = [
    ("heal",   "HEAL HEART",    30, "+1 heart"),
    ("soul",   "HEART SOUL",    80, "fill all hearts"),
    ("book",   "SPELL BOOK",    55, "sword +1 dmg"),
    ("armor",  "IRON ARMOR",    60, "+1 heart max"),
    ("boot",   "RUNNING SHOES", 45, "faster"),
    ("shield", "IRON SHIELD",   70, "press 1 for circle"),
]

class game:
    def __init__(self, root):
        self.root = root
        self.root.title("Dungeon Crawl (Python/Tkinter)")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)
        self.canvas.bind("<Button-1>", self.click)
        self.pressed = set()
        self.init_game()
        self.last = time.time()
        self.loop()

    def init_game(self):
        self.player = {"x": 0, "y": 0, "w": 24, "h": 24, "hearts": 3, "max_hearts": 3, "power": 3,
                       "speed": 5.4, "face": "down", "iframes": 0, "swing_cd": 0, "def_cd": 0, "shield": 0}
        self.monsters = []
        self.arrows = []
        self.particles = []
        self.rings = []
        self.texts = []
        self.trails = []
        self.coins = []
        self.potns = []
        self.torches = []
        self.swings = []
        self.map = []
        self.rooms = []
        self.score = 0
        self.gold = 0
        self.floor = 1
        self.game_over = False
        self.boss = None
        self.shake = 0
        self.flash = 0
        self.paused = False
        self.shop = False
        self.spawn_cd = 0.8
        self.mon_left = 0
        self.break_timer = 0
        self.banner = ""
        self.banner_t = 0
        self.combo = 1
        self.combo_t = 0
        self.time_now = 0
        self.owned = {"book": False, "armor": False, "boot": False, "shield": False}
        self.start_floor()

    def floor_config(self, f):
        boss = f % 3 == 0
        return {
            "boss": boss,
            "count": (4 + f//2) if boss else 4 + int(f*1.5),
            "skeleton_chance": max(0.0, (f-2)*0.11),
            "orc_chance": max(0.0, (f-1)*0.09),
            "hp_bonus": max(0, f-3),
            "speed_mul": 0.85 + min(0.75, (f-1)*0.07),
        }

    def start_floor(self):
        self.carve_floor()
        room = self.rooms[0]
        px = room["x"]*TILE + room["w"]//2*TILE + TILE//2
        py = room["y"]*TILE + room["h"]//2*TILE + TILE//2
        self.player["x"] = px
        self.player["y"] = py
        self.player["iframes"] = 1.0
        self.arrows = []
        self.particles = []
        self.rings = []
        self.texts = []
        self.trails = []
        self.swings = []
        self.spawn_loot()
        c = self.floor_config(self.floor)
        self.mon_left = c["count"]
        self.spawn_cd = 0.8
        if c["boss"]:
            self.spawn_boss()
        self.banner = ("FLOOR %d - BOSS" % self.floor) if c["boss"] else ("FLOOR %d" % self.floor)
        self.banner_t = 2.0

    def carve_floor(self):
        self.map = [[1 for _ in range(COLS)] for _ in range(ROWS)]
        self.rooms = []
        tries = 0
        while len(self.rooms) < 6 and tries < 200:
            tries += 1
            w = random.randint(4, 8)
            h = random.randint(3, 6)
            x = random.randint(1, COLS-w-2)
            y = random.randint(1, ROWS-h-2)
            if self.rooms_hit(self.rooms, x, y, w, h):
                continue
            self.rooms.append({"x": x, "y": y, "w": w, "h": h})
            for yy in range(y, y+h):
                for xx in range(x, x+w):
                    self.map[yy][xx] = 0
        for i in range(1, len(self.rooms)):
            self.carve_corridor(self.rooms[i-1], self.rooms[i])
        for _ in range(random.randint(3, 7)):
            r = random.choice(self.rooms)
            x = r["x"] + random.randint(0, r["w"]-1)
            y = r["y"] + random.randint(0, r["h"]-1)
            if self.map[y][x] == 0:
                self.map[y][x] = 3
        self.torches = []
        for y in range(1, ROWS-1):
            for x in range(1, COLS-1):
                if self.map[y][x] != 0:
                    continue
                up = self.map[y-1][x] != 0
                side = (self.map[y][x-1] != 0 and x < COLS//2) or (self.map[y][x+1] != 0 and x >= COLS//2)
                if (up or side) and random.random() < 0.055:
                    self.torches.append({"x": x*TILE+TILE//2, "y": y*TILE+6, "phase": random.random()*6})

    def rooms_hit(self, rooms, x, y, w, h):
        for r in rooms:
            if x < r["x"]+r["w"] and r["x"] < x+w and y < r["y"]+r["h"] and r["y"] < y+h:
                return True
        return False

    def carve_corridor(self, a, b):
        x = a["x"] + a["w"]//2
        y = a["y"] + a["h"]//2
        tx = b["x"] + b["w"]//2
        ty = b["y"] + b["h"]//2
        while x != tx:
            self.map[y][x] = 0
            x += 1 if tx > x else -1
        while y != ty:
            self.map[y][x] = 0
            y += 1 if ty > y else -1
        self.map[y][x] = 0

    def spawn_loot(self):
        for _ in range(random.randint(6, 9)):
            r = random.choice(self.rooms[1:] or self.rooms)
            x = r["x"] + random.randint(1, r["w"]-2)
            y = r["y"] + random.randint(1, r["h"]-2)
            if self.map[y][x] == 0:
                self.coins.append({"x": x*TILE+TILE//2, "y": y*TILE+TILE//2, "g": random.randint(3, 9)})
        for _ in range(random.randint(1, 3)):
            r = random.choice(self.rooms[1:] or self.rooms)
            x = r["x"] + random.randint(1, r["w"]-2)
            y = r["y"] + random.randint(1, r["h"]-2)
            if self.map[y][x] == 0:
                self.potns.append({"x": x*TILE+TILE//2, "y": y*TILE+TILE//2})

    def solid_at(self, px, py):
        tx, ty = int(px // TILE), int(py // TILE)
        if tx < 0 or ty < 0 or tx >= COLS or ty >= ROWS:
            return True
        return self.map[ty][tx] != 0

    def blocked(self, x, y, w):
        s = w/2
        return (self.solid_at(x-s+3, y-s+3) or self.solid_at(x+s-3, y-s+3)
                or self.solid_at(x-s+3, y+s-3) or self.solid_at(x+s-3, y+s-3))

    def key_press(self, event):
        self.pressed.add(event.keysym)
        k = event.keysym.lower()
        if k == "p":
            self.paused = not self.paused
        if k == "r" and self.game_over:
            self.init_game()
        if k == "b":
            self.shop = not self.shop
        if self.shop:
            if event.keysym.isdigit():
                self.buy(int(event.keysym)-1)
            return
        if k == "e" or k == "escape":
            self.shop = False
        if event.keysym == "space":
            self.swing_sword()
        if event.keysym == "1":
            self.use_def()

    def key_release(self, event):
        self.pressed.discard(event.keysym)

    def click(self, event):
        if self.game_over:
            self.init_game()

    def buy(self, idx):
        if idx < 0 or idx >= len(SHOP):
            return
        key, name, price, desc = SHOP[idx]
        p = self.player
        if key == "heal":
            if self.gold >= price and p["hearts"] < p["max_hearts"]:
                self.gold -= price
                p["hearts"] += 1
                self.popup(p["x"], p["y"]-28, "+1 HEART", "lime")
                self.explode(p["x"], p["y"], "lime", 12, shake=2)
            return
        if key == "soul":
            if self.gold >= price and p["hearts"] < p["max_hearts"]:
                self.gold -= price
                p["hearts"] = p["max_hearts"]
                self.popup(p["x"], p["y"]-28, "FULL HEARTS", "lime")
                self.explode(p["x"], p["y"], "lime", 18, shake=3)
            return
        if self.owned[key] or self.gold < price:
            return
        self.gold -= price
        self.owned[key] = True
        self.popup(p["x"], p["y"]-28, name, "gold")
        if key == "book":
            p["power"] += 1
        if key == "armor":
            p["max_hearts"] += 1
            p["hearts"] += 1
        if key == "boot":
            p["speed"] = 8.4
        if key == "shield":
            p["def_cd"] = 0
        self.explode(p["x"], p["y"], "gold", 14, shake=2)

    def swing_sword(self):
        p = self.player
        if p["swing_cd"] > 0 or self.shop or self.game_over or self.paused:
            return
        p["swing_cd"] = 0.34
        a = {"right": 0.0, "down": math.pi/2, "left": math.pi, "up": -math.pi/2}[p["face"]]
        self.swings.append({"x": p["x"], "y": p["y"], "a": a, "life": 0.18, "max": 0.18})
        self.rings.append({"x": p["x"]+math.cos(a)*26, "y": p["y"]+math.sin(a)*26, "r": 2, "max_r": 22, "life": 0.22})
        for m in list(self.monsters):
            mx = m["x"] + m["w"]/2 - p["x"]
            my = m["y"] + m["h"]/2 - p["y"]
            d = math.hypot(mx, my)
            if d > 52 + m["w"]/2:
                continue
            diff = abs(math.atan2(my, mx) - a)
            if diff > math.pi:
                diff = math.pi*2 - diff
            if diff <= 1.25:
                self.hurt_monster(m, p["power"])
        self.explode(p["x"]+math.cos(a)*28, p["y"]+math.sin(a)*28, "white", 5, size=2, shake=1)
        self.shake = min(14, self.shake + 2)

    def use_def(self):
        p = self.player
        if not self.owned["shield"] or p["def_cd"] > 0 or self.game_over or self.shop:
            return
        p["def_cd"] = 9.0
        p["shield"] = 3.0
        self.explode(p["x"], p["y"], "cyan", 16, shake=2)
        self.popup(p["x"], p["y"]-26, "SHIELD", "cyan")

    def spawn_monster(self):
        c = self.floor_config(self.floor)
        r = random.choice(self.rooms[1:] or self.rooms)
        x = (r["x"]+1)*TILE + random.uniform(0, (r["w"]-2)*TILE)
        y = (r["y"]+1)*TILE + random.uniform(0, (r["h"]-2)*TILE)
        if math.hypot(x-self.player["x"], y-self.player["y"]) < 130:
            return
        roll = random.random()
        t = "rat"
        if roll < c["skeleton_chance"]:
            t = "skeleton"
        elif roll < c["skeleton_chance"]+c["orc_chance"]:
            t = "orc"
        elif roll < 0.62:
            t = "rat"
        else:
            t = "bat"
        self.make_monster(t, x, y, c)

    def make_monster(self, t, x, y, c):
        if t == "rat":
            self.monsters.append({"x": x, "y": y, "w": 24, "h": 20, "type": "rat", "hp": 1+c["hp_bonus"], "maxhp": 1+c["hp_bonus"], "spd": 3.1*c["speed_mul"], "color": "gray60", "score": 10, "gold": 4, "cd": 1.5, "wt": 0, "wa": 0})
        elif t == "bat":
            self.monsters.append({"x": x, "y": y, "w": 22, "h": 22, "type": "bat", "hp": 1+c["hp_bonus"], "maxhp": 1+c["hp_bonus"], "spd": 2.3*c["speed_mul"], "color": "mediumorchid", "score": 15, "gold": 6, "cd": 1.5, "wt": 0, "wa": 0})
        elif t == "skeleton":
            self.monsters.append({"x": x, "y": y, "w": 24, "h": 28, "type": "skeleton", "hp": 2+c["hp_bonus"]//2, "maxhp": 2+c["hp_bonus"]//2, "spd": 1.7*c["speed_mul"], "color": "beige", "score": 20, "gold": 8, "cd": 2.0, "fire": 2.3, "wt": 0, "wa": 0})
        elif t == "orc":
            self.monsters.append({"x": x, "y": y, "w": 34, "h": 34, "type": "orc", "hp": 6+c["hp_bonus"]*2, "maxhp": 6+c["hp_bonus"]*2, "spd": 1.15*c["speed_mul"], "color": "mediumseagreen", "score": 35, "gold": 14, "cd": 2, "wt": 0, "wa": 0})
        elif t == "knight":
            self.monsters.append({"x": x, "y": y, "w": 26, "h": 26, "type": "knight", "hp": 2+c["hp_bonus"], "maxhp": 2+c["hp_bonus"], "spd": 2.55*c["speed_mul"], "color": "tomato", "score": 10, "gold": 5, "cd": 2, "wt": 0, "wa": 0})

    def spawn_knight(self, x, y):
        side = -30 if random.random() < 0.5 else 30
        self.make_monster("knight", x+side, y-10, self.floor_config(self.floor))
        self.explode(x, y, "tomato", 10, size=2, shake=2)

    def spawn_boss(self):
        hp = 150 + self.floor*60
        far, fd = self.rooms[0], 0
        for r in self.rooms:
            cx = r["x"]*TILE + r["w"]*TILE/2
            cy = r["y"]*TILE + r["h"]*TILE/2
            d = math.hypot(cx-self.player["x"], cy-self.player["y"])
            if d > fd:
                fd, far = d, r
        self.boss = {"x": far["x"]*TILE + far["w"]*TILE/2, "y": far["y"]*TILE + max(2, far["h"]//2)*TILE, "w": 80, "h": 80, "type": "boss", "hp": hp, "maxhp": hp, "spd": 1.0+self.floor*0.04, "color": "magenta", "score": 1000, "gold": 200, "cd": 2.4, "fire": 2.4, "sum": 6.0, "wt": 0, "wa": 0}
        self.monsters.append(self.boss)

    def monster_sees(self, m, reach):
        p = self.player
        d = math.hypot(p["x"]-m["x"], p["y"]-m["y"])
        if d > reach:
            return False
        steps = math.ceil(d/12)
        for i in range(1, steps):
            t = i/steps
            if self.solid_at(m["x"]+(p["x"]-m["x"])*t, m["y"]+(p["y"]-m["y"])*t):
                return False
        return True

    def step_toward(self, m, tx, ty, sp):
        dx, dy = tx-m["x"], ty-m["y"]
        d = math.hypot(dx, dy) or 1
        size = min(m["w"], 26)
        nx, ny = m["x"]+dx/d*sp, m["y"]+dy/d*sp
        if not self.blocked(nx, m["y"], size):
            m["x"] = nx
        if not self.blocked(m["x"], ny, size):
            m["y"] = ny

    def wander(self, m, sp, dt):
        m["wt"] = m.get("wt", 0) - dt
        if m["wt"] <= 0:
            m["wt"] = random.uniform(1.2, 2.8)
            m["wa"] = random.random()*math.pi*2
        size = min(m["w"], 26)
        nx, ny = m["x"]+math.cos(m["wa"])*sp, m["y"]+math.sin(m["wa"])*sp
        if not self.blocked(nx, m["y"], size):
            m["x"] = nx
        if not self.blocked(m["x"], ny, size):
            m["y"] = ny

    def fire_arrow(self, m):
        p = self.player
        a = math.atan2(p["y"]-m["y"], p["x"]-m["x"])
        self.arrows.append({"x": m["x"], "y": m["y"], "dx": math.cos(a)*3.6, "dy": math.sin(a)*3.6, "color": "gold"})
        self.explode(m["x"], m["y"], "gold", 3, size=1, shake=0, ring=False)

    def loop(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        if dt > 0.05:
            dt = 0.05
        if not self.paused:
            self.update(dt)
        self.draw()
        self.root.after(16, self.loop)

    def update(self, dt):
        p = self.player
        self.time_now += dt
        running = False
        if not self.shop and not self.game_over:
            nx, ny = p["x"], p["y"]
            if "Left" in self.pressed or "a" in self.pressed:
                running, p["face"], nx = True, "left", nx-p["speed"]
            if "Right" in self.pressed or "d" in self.pressed:
                running, p["face"], nx = True, "right", nx+p["speed"]
            if "Up" in self.pressed or "w" in self.pressed:
                running, p["face"], ny = True, "up", ny-p["speed"]
            if "Down" in self.pressed or "s" in self.pressed:
                running, p["face"], ny = True, "down", ny+p["speed"]
            if not self.blocked(nx, p["y"], 20):
                p["x"] = nx
            if not self.blocked(p["x"], ny, 20):
                p["y"] = ny
            if running and not self.blocked(p["x"], p["y"], 20):
                self.trails.append({"x": p["x"], "y": p["y"]-10, "life": 0.3, "max": 0.3})
            if p["iframes"] > 0: p["iframes"] -= dt
            if p["swing_cd"] > 0: p["swing_cd"] -= dt
            if p["def_cd"] > 0: p["def_cd"] -= dt
            if p["shield"] > 0: p["shield"] -= dt
        if self.break_timer > 0:
            self.break_timer -= dt
            if self.break_timer <= 0:
                self.break_timer = 0
                self.floor += 1
                self.start_floor()
        else:
            self.spawn_cd -= dt
            if self.spawn_cd <= 0 and self.mon_left > 0:
                self.spawn_cd = max(0.4, 1.4 - self.floor*0.08)
                self.spawn_monster()
                self.mon_left -= 1
            if self.mon_left <= 0 and len(self.monsters) == 0 and not self.game_over:
                self.floor_clear()

        for a in list(self.arrows):
            a["x"] += a["dx"]; a["y"] += a["dy"]
            if self.solid_at(a["x"], a["y"]):
                self.arrows.remove(a)
                self.explode(a["x"], a["y"], "gold", 4, size=1, shake=0, ring=False)
                continue
            if a["x"] < 0 or a["y"] < 0 or a["x"] > WIDTH or a["y"] > HEIGHT:
                self.arrows.remove(a)
                continue
            if p["iframes"] <= 0 and abs(a["x"]-p["x"]) < 15 and abs(a["y"]-p["y"]) < 15:
                self.arrows.remove(a)
                self.player_hit()

        for m in list(self.monsters):
            if m["type"] == "boss":
                self.step_toward(m, p["x"], p["y"], m["spd"])
                m["cd"] -= dt
                if m["cd"] <= 0:
                    m["cd"] = m["fire"] * random.uniform(0.85, 1.15)
                    base = math.atan2(p["y"]-m["y"], p["x"]-m["x"])
                    for k in range(-2, 3):
                        ang = base + k*0.24
                        self.arrows.append({"x": m["x"], "y": m["y"], "dx": math.cos(ang)*3.8, "dy": math.sin(ang)*3.8, "color": "plum"})
                    self.explode(m["x"], m["y"], "magenta", 8, size=2, shake=2)
                m["sum"] -= dt
                if m["sum"] <= 0:
                    m["sum"] = 6.5
                    self.spawn_knight(m["x"], m["y"])
            elif m["type"] == "skeleton":
                if self.monster_sees(m, 360):
                    if math.hypot(p["x"]-m["x"], p["y"]-m["y"]) > 150:
                        self.step_toward(m, p["x"], p["y"], m["spd"]*0.5)
                    m["cd"] -= dt
                    if m["cd"] <= 0:
                        m["cd"] = m["fire"] * random.uniform(0.75, 1.25)
                        self.fire_arrow(m)
                else:
                    self.wander(m, m["spd"]*0.6, dt)
            else:
                reach = 250 if m["type"] == "rat" else (300 if m["type"] == "bat" else 420)
                if self.monster_sees(m, reach):
                    self.step_toward(m, p["x"], p["y"], m["spd"])
                else:
                    self.wander(m, m["spd"]*0.55, dt)
            if p["iframes"] <= 0 and not self.game_over:
                if abs(p["x"]-m["x"]) < (m["w"]+p["w"])/2 and abs(p["y"]-m["y"]) < (m["h"]+p["h"])/2:
                    self.player_hit()

        for cn in list(self.coins):
            if math.hypot(cn["x"]-p["x"], cn["y"]-p["y"]) < 22:
                self.gold += cn["g"]
                self.popup(cn["x"], cn["y"]-14, "+%dg" % cn["g"], "gold")
                self.explode(cn["x"], cn["y"], "gold", 5, size=1, shake=0, ring=False)
                self.coins.remove(cn)
        for q in list(self.potns):
            if math.hypot(q["x"]-p["x"], q["y"]-p["y"]) < 22:
                if p["hearts"] < p["max_hearts"]:
                    p["hearts"] += 1
                    self.popup(q["x"], q["y"]-14, "+1 HEART", "lime")
                else:
                    self.gold += 15
                    self.popup(q["x"], q["y"]-14, "+15g", "gold")
                self.explode(q["x"], q["y"], "lime", 8, size=2, shake=1)
                self.potns.remove(q)

        self.update_effects(dt)

    def explode(self, x, y, color, n, size=3, shake=4, ring=True):
        for _ in range(n):
            ang = random.random()*math.pi*2
            sp = random.random()*160 + 40
            life = random.uniform(0.25, 0.7)
            self.particles.append({"x": x, "y": y, "vx": math.cos(ang)*sp, "vy": math.sin(ang)*sp, "life": life, "max": life, "r": random.randint(size, size*3), "color": color})
        if ring:
            self.rings.append({"x": x, "y": y, "r": 2, "max_r": 30+size*8, "life": 0.35})
        self.shake = min(18, self.shake + shake)

    def popup(self, x, y, text, color):
        self.texts.append({"x": x, "y": y, "text": text, "color": color, "life": 0.9})

    def hurt_monster(self, m, dmg):
        m["hp"] -= dmg
        ex = m["x"] + random.uniform(-4, 4)
        ey = m["y"] - 8
        self.explode(ex, ey, "orange", 5, size=2, shake=1, ring=False)
        self.popup(ex, ey, "-%d" % dmg, "salmon")
        if m["hp"] > 0:
            return
        if m in self.monsters:
            self.monsters.remove(m)
        if m["type"] == "boss":
            self.boss = None
            self.score += 1000
            self.gold += 200
            self.explode(m["x"], m["y"], "magenta", 90, size=6, shake=16)
            self.flash = 1
            self.popup(m["x"]-40, m["y"], "+200g", "gold")
            self.popup(m["x"]-40, m["y"]+20, "OGRE SLAIN", "gold")
        else:
            self.combo = min(6, self.combo+1)
            self.combo_t = 3.0
            self.score += m["score"] * self.combo
            self.gold += m["gold"]
            self.explode(m["x"], m["y"], m["color"], 20, size=3, shake=3)
            self.popup(m["x"]-16, m["y"], "+%dg" % m["gold"], "gold")
            if self.combo > 1:
                self.popup(m["x"]+14, m["y"]-20, "x%d" % self.combo, "orange")
            if random.random() < 0.4:
                self.coins.append({"x": m["x"], "y": m["y"], "g": random.randint(2, 6)})

    def player_hit(self):
        p = self.player
        if p["shield"] > 0:
            p["shield"] = 0
            p["iframes"] = 1.2
            self.explode(p["x"], p["y"], "cyan", 20, shake=4)
            self.popup(p["x"], p["y"]-26, "BLOCKED", "cyan")
            return
        p["hearts"] -= 1
        p["iframes"] = 1.2
        self.combo = 1
        self.explode(p["x"], p["y"], "red", 35, size=4, shake=10)
        self.flash = 0.7
        self.popup(p["x"], p["y"]-26, "-1 HEART", "red")
        if p["hearts"] <= 0:
            self.game_over = True
            self.explode(p["x"], p["y"], "red", 60, size=6, shake=18)
            self.rings.append({"x": p["x"], "y": p["y"], "r": 2, "max_r": 80, "life": 0.5})
            self.flash = 1

    def floor_clear(self):
        bonus = 25 + self.floor*10
        self.score += self.floor*100
        self.gold += bonus
        self.popup(self.player["x"]-30, self.player["y"]-40, "FLOOR CLEAR +%dg" % bonus, "lime")
        self.explode(self.player["x"], self.player["y"], "lime", 25, size=3, shake=4)
        if self.player["hearts"] < self.player["max_hearts"]:
            self.player["hearts"] += 1
            self.popup(self.player["x"]-20, self.player["y"]-58, "+1 HEART", "lime")
        if self.floor >= MAX_FLOOR:
            for m in list(self.monsters):
                self.explode(m["x"], m["y"], "gold", 15, size=3, shake=2)
                if m in self.monsters:
                    self.monsters.remove(m)
            self.arrows = []
            self.flash = 1
            self.explode(self.player["x"], self.player["y"], "gold", 60, size=6, shake=10)
            self.game_over = True
            return
        self.break_timer = 2.0
        if (self.floor+1) % 3 == 0:
            self.banner = "THE OGRE COMES NEXT..."
        else:
            self.banner = "NEXT FLOOR IN 2..."
        self.banner_t = 2.0

    def update_effects(self, dt):
        for q in self.particles:
            q["x"] += q["vx"]*dt
            q["y"] += q["vy"]*dt
            q["vx"] -= q["vx"]*3*dt
            q["vy"] -= q["vy"]*3*dt
            q["life"] -= dt
        self.particles = [q for q in self.particles if q["life"] > 0]
        for r in self.rings:
            r["r"] += (r["max_r"]-r["r"])*min(1, dt*7)
            r["life"] -= dt
        self.rings = [r for r in self.rings if r["life"] > 0]
        for t in self.texts:
            t["y"] -= 30*dt
            t["life"] -= dt
        self.texts = [t for t in self.texts if t["life"] > 0]
        for t in self.trails:
            t["life"] -= dt
        self.trails = [t for t in self.trails if t["life"] > 0]
        for s in self.swings:
            s["life"] -= dt
        self.swings = [s for s in self.swings if s["life"] > 0]
        if random.random() < 0.06 and self.torches:
            t = random.choice(self.torches)
            self.particles.append({"x": t["x"]+random.uniform(-2, 2), "y": t["y"]-4, "vx": random.uniform(-5, 5), "vy": -24-random.uniform(0, 14), "life": 0.5, "max": 0.5, "r": 2, "color": "orangered"})
        self.shake = max(0, self.shake - dt*30)
        self.flash = max(0, self.flash - dt*3)
        self.banner_t = max(0, self.banner_t - dt)
        self.combo_t = max(0, self.combo_t - dt)
        if self.combo_t <= 0:
            self.combo = 1

    def draw(self):
        c = self.canvas
        c.delete("all")
        ox = (random.random()-0.5)*self.shake
        oy = (random.random()-0.5)*self.shake

        for y in range(ROWS):
            for x in range(COLS):
                t = self.map[y][x]
                x0, y0 = x*TILE+ox, y*TILE+oy
                if t == 0:
                    col = "gray5" if (x+y) % 2 else "gray4"
                    c.create_rectangle(x0, y0, x0+TILE, y0+TILE, fill=col, outline="")
                elif t == 3:
                    c.create_rectangle(x0, y0, x0+TILE, y0+TILE, fill="gray30", outline="gray55")
                    c.create_rectangle(x0+3, y0+3, x0+TILE-3, y0+TILE-3, outline="gray55")
                else:
                    c.create_rectangle(x0, y0, x0+TILE, y0+TILE, fill="brown4", outline="")
                    c.create_rectangle(x0+4, y0+4, x0+TILE+1, y0+TILE+1, fill="tan3", outline="")

        for t in self.torches:
            flick = math.sin(self.time_now*7 + t["phase"]) > 0
            c.create_oval(t["x"]+ox-26, t["y"]+oy-26, t["x"]+ox+26, t["y"]+oy+26, fill="orange", outline="", stipple="gray25" if flick else "gray12")
            c.create_rectangle(t["x"]-2+ox, t["y"]-8+oy, t["x"]+2+ox, t["y"]+oy, fill="orangered", outline="")
            c.create_rectangle(t["x"]-1+ox, t["y"]-11+oy, t["x"]+1+ox, t["y"]-7+oy, fill="gold", outline="")

        for g in self.rings:
            c.create_oval(g["x"]+ox-g["r"], g["y"]+oy-g["r"], g["x"]+ox+g["r"], g["y"]+oy+g["r"], outline="white", width=2)
        for t in self.trails:
            r = 4 + t["life"]/t["max"]*8
            c.create_oval(t["x"]+ox-r, t["y"]+oy-r, t["x"]+ox+r, t["y"]+oy+r, fill="deepskyblue", outline="")
        for q in self.particles:
            rr = max(1, q["r"]*q["life"]/q["max"])
            c.create_oval(q["x"]+ox-rr, q["y"]+oy-rr, q["x"]+ox+rr, q["y"]+oy+rr, fill=q["color"], outline="")
        for t in self.texts:
            c.create_text(t["x"]+ox, t["y"]+oy, text=t["text"], fill=t["color"], font=("Arial", 14, "bold"))
        for s in self.swings:
            deg_a = s["a"] + 1.25
            start = -math.degrees(deg_a)
            c.create_arc(s["x"]+ox-32, s["y"]+oy-32, s["x"]+ox+32, s["y"]+oy+32, start=start, extent=143, style="arc", outline="white", width=5)

        for cn in self.coins:
            bob = math.sin(self.time_now*5 + cn["x"])*1.5
            c.create_oval(cn["x"]-5+ox, cn["y"]-5+bob+oy, cn["x"]+5+ox, cn["y"]+5+bob+oy, fill="gold", outline="white")
            c.create_rectangle(cn["x"]-1+ox, cn["y"]-2+bob+oy, cn["x"]+1+ox, cn["y"]+2+bob+oy, fill="yellow", outline="")
        for q in self.potns:
            c.create_oval(q["x"]-6+ox, q["y"]-6+oy, q["x"]+6+ox, q["y"]+6+oy, fill="hotpink", outline="white")
            c.create_rectangle(q["x"]-1+ox, q["y"]-5+oy, q["x"]+1+ox, q["y"]+oy+1, fill="white", outline="")

        for a in self.arrows:
            c.create_line(a["x"]-a["dx"]*2.4+ox, a["y"]-a["dy"]*2.4+oy, a["x"]+ox, a["y"]+oy, fill=a["color"], width=2)
        p = self.player
        col = "blue"
        if p["iframes"] > 0 and int(p["iframes"]*10) % 2 == 0:
            col = "gray60"
        c.create_rectangle(p["x"]-p["w"]/2+ox, p["y"]-p["h"]/2+oy, p["x"]+p["w"]/2+ox, p["y"]+p["h"]/2+oy, fill=col, outline="white")
        if self.owned["shield"] and p["shield"] > 0:
            c.create_oval(p["x"]-22+ox, p["y"]-22+oy, p["x"]+22+ox, p["y"]+22+oy, outline="cyan", width=2)
        c.create_rectangle(p["x"]-2+ox, p["y"]-30+oy, p["x"]+2+ox, p["y"]-26+oy, fill="lime", outline="")
        for m in self.monsters:
            c.create_rectangle(m["x"]-m["w"]/2+ox, m["y"]-m["h"]/2+oy, m["x"]+m["w"]/2+ox, m["y"]+m["h"]/2+oy,
                               fill=m["color"], outline="white")
            if m["type"] == "skeleton":
                c.create_rectangle(m["x"]-5+ox, m["y"]-6+oy, m["x"]+5+ox, m["y"]-3+oy, fill="black", outline="")
            elif m["type"] == "orc":
                c.create_rectangle(m["x"]-9+ox, m["y"]-8+oy, m["x"]+9+ox, m["y"]-5+oy, fill="black", outline="")
            elif m["type"] == "bat":
                c.create_rectangle(m["x"]-1+ox, m["y"]-8+oy, m["x"]+1+ox, m["y"]-2+oy, fill="white", outline="")
            if m["type"] == "boss":
                fr = max(0, m["hp"]/m["maxhp"])
                c.create_text(m["x"]+ox, m["y"]-m["h"]/2+oy-16, text="OGRE", fill="white", font=("Arial", 14, "bold"))
                c.create_rectangle(m["x"]-m["w"]/2+ox, m["y"]-m["h"]/2+oy-9, m["x"]+m["w"]/2+ox, m["y"]-m["h"]/2+oy-3, fill="gray40", outline="white")
                c.create_rectangle(m["x"]-m["w"]/2+ox, m["y"]-m["h"]/2+oy-9, m["x"]-m["w"]/2+m["w"]*fr+ox, m["y"]-m["h"]/2+oy-3, fill="magenta", outline="")
            elif m["maxhp"] > 1:
                fr = max(0, m["hp"]/m["maxhp"])
                c.create_rectangle(m["x"]-m["w"]/2+ox, m["y"]-m["h"]/2+oy-6, m["x"]+m["w"]/2+ox, m["y"]-m["h"]/2+oy-3, fill="gray40", outline="")
                c.create_rectangle(m["x"]-m["w"]/2+ox, m["y"]-m["h"]/2+oy-6, m["x"]-m["w"]/2+m["w"]*fr+ox, m["y"]-m["h"]/2+oy-3, fill="red", outline="")

        if self.flash > 0:
            c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="white", stipple="gray75" if self.flash < 0.5 else "gray25")

        c.create_text(10, 16, anchor="nw", text=f"score: {self.score}", fill="white")
        c.create_text(10, 36, anchor="nw", text=f"gold: {self.gold}", fill="gold")
        c.create_text(10, 56, anchor="nw", text=f"floor: {self.floor}   monsters left: {self.mon_left+len(self.monsters)}", fill="white")
        for i in range(p["max_hearts"]):
            x0 = 10 + i*18
            if i < p["hearts"]:
                c.create_rectangle(x0, 64, x0+13, 77, fill="red", outline="white")
                c.create_rectangle(x0+3, 67, x0+8, 72, fill="#ff7777", outline="")
            else:
                c.create_rectangle(x0, 64, x0+13, 77, fill="gray20", outline="white")
        c.create_text(WIDTH-10, 16, anchor="ne", text="B = SHOP", fill="cyan", font=("Arial", 12, "bold"))
        c.create_text(WIDTH-10, 36, anchor="ne", text="1 = shield", fill="gray70")
        c.create_text(WIDTH-10, 56, anchor="ne", text=" | ".join(k for k, v in self.owned.items() if v) or "no upgrades", fill="gray60")
        if p["swing_cd"] > 0:
            c.create_text(WIDTH-10, 76, anchor="ne", text="SWING wait", fill="gray40")
        if p["def_cd"] > 0 and self.owned["shield"]:
            c.create_text(WIDTH-10, 96, anchor="ne", text="DEF wait", fill="gray40")
        if self.combo > 1:
            c.create_text(WIDTH//2, 88, text="x%d combo" % self.combo, fill="orange", font=("Arial", 16, "bold"))
        c.create_text(WIDTH//2, HEIGHT-14, text="slashes beat bones - gold buys hearts - breathe", fill="white", font=("Arial", 13))

        if self.banner_t > 0:
            c.create_text(WIDTH//2, HEIGHT//2-90, text=self.banner, fill="lime", font=("Arial", 24, "bold"))
        if self.paused:
            c.create_text(WIDTH//2, HEIGHT//2, text="paused(p)", fill="yellow", font=("Arial", 26))
        if self.game_over:
            c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="black",
                               stipple="gray25" if self.floor >= MAX_FLOOR else "gray50")
            if self.floor >= MAX_FLOOR:
                c.create_text(WIDTH//2, HEIGHT//2, text="you escaped the dungeon", fill="gold", font=("Arial", 30))
                c.create_text(WIDTH//2, HEIGHT//2+40, text=f"score {self.score} gold {self.gold} - press r to play again", fill="white", font=("Arial", 13))
            else:
                c.create_text(WIDTH//2, HEIGHT//2, text="you died", fill="red", font=("Arial", 30))
                c.create_text(WIDTH//2, HEIGHT//2+40, text=f"score {self.score} gold {self.gold} floor {self.floor} - press r to restart", fill="white", font=("Arial", 13))
        if self.shop:
            self.draw_shop()

    def draw_shop(self):
        c = self.canvas
        px, py, pw, ph = 180, 90, 440, 380
        c.create_rectangle(px, py, px+pw, py+ph, fill="black", outline="gold", width=3)
        c.create_text(WIDTH//2, py+28, text="SHOP", fill="gold", font=("Arial", 22, "bold"))
        c.create_text(WIDTH//2, py+52, text=f"you have {self.gold} gold", fill="white", font=("Arial", 13))
        y = py + 84
        for i, (key, name, price, desc) in enumerate(SHOP):
            once = key in ("heal", "soul")
            owned = self.owned.get(key)
            full = once and self.player["hearts"] >= self.player["max_hearts"]
            col = "gray45" if owned or full else ("lime" if self.gold >= price else "gray70")
            label = f"{i+1}. {name:<14} {price:>4}g  {desc}"
            if owned or full:
                label = f"{i+1}. {name:<14} {'OWNED' if owned else 'HEARTS FULL'}"
            c.create_text(px+20, y, text=label, fill=col, font=("Courier", 12), anchor="nw")
            y += 30
        c.create_text(WIDTH//2, py+ph-24, text="press number to buy | b or esc to close", fill="cyan", font=("Arial", 11))

if __name__ == "__main__":
    root = tk.Tk()
    g = game(root)
    root.mainloop()