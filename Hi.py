import tkinter as tk
import random

TILE = 32
COLS = 25
ROWS = 18

class dungeon:
    def __init__(self, root):
        self.root = root
        self.root.title("Dungeon Crawl (Python/Tkinter)")
        self.root.geometry(f"{COLS*TILE}x{ROWS*TILE+80}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=COLS*TILE, height=ROWS*TILE, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.info = tk.Label(root, text="", bg="black", fg="white", font=("Courier", 11), justify="left")
        self.info.pack(fill="x")
        self.root.bind("<KeyPress>", self.key_press)
        self.new_game()

    def new_game(self):
        self.player = {"x": 1, "y": 1, "hp": 20, "maxhp": 20, "atk": 3, "dfn": 0, "gold": 0, "potions": 2, "level": 1, "kills": 0}
        self.monsters = []
        self.items = []
        self.msgs = []
        self.game_over = False
        self.build_level()

    def build_level(self):
        self.tiles = [[1 for x in range(COLS)] for y in range(ROWS)]
        rooms = []
        tries = 0
        while len(rooms) < 6 and tries < 200:
            tries += 1
            w = random.randint(3, 6)
            h = random.randint(3, 5)
            x = random.randint(1, COLS-w-1)
            y = random.randint(1, ROWS-h-1)
            if self.room_hits(rooms, x, y, w, h):
                continue
            rooms.append((x, y, w, h))
            for yy in range(y, y+h):
                for xx in range(x, x+w):
                    self.tiles[yy][xx] = 0
        if not rooms:
            return
        for i in range(1, len(rooms)):
            self.corridor(rooms[i-1], rooms[i])
        first = rooms[0]
        self.player["x"] = first[0]+1
        self.player["y"] = first[1]+1
        for room in rooms[1:]:
            self.spawn_monster(room)
            if random.random() < 0.6:
                self.drop_item(room)
            if random.random() < 0.3:
                self.drop_item(room)
        last = rooms[-1]
        self.tiles[last[1]+last[3]//2][last[0]+last[2]//2] = 2
        self.msg("level %d" % self.player["level"])

    def room_hits(self, rooms, x, y, w, h):
        for r in rooms:
            if x < r[0]+r[2] and r[0] < x+w and y < r[1]+r[3] and r[1] < y+h:
                return True
        return False

    def corridor(self, a, b):
        x = a[0]+a[2]//2
        y = a[1]+a[3]//2
        tx = b[0]+b[2]//2
        ty = b[1]+b[3]//2
        while x != tx:
            self.tiles[y][x] = 0
            x += 1 if tx > x else -1
        while y != ty:
            self.tiles[y][x] = 0
            y += 1 if ty > y else -1
        self.tiles[y][x] = 0

    def spawn_monster(self, room):
        x = random.randint(room[0], room[0]+room[2]-1)
        y = random.randint(room[1], room[1]+room[3]-1)
        pick = random.random()
        if pick < 0.45:
            self.monsters.append({"x": x, "y": y, "name": "rat", "hp": 4, "maxhp": 4, "atk": 2, "dfn": 0, "gold": 3})
        elif pick < 0.8:
            self.monsters.append({"x": x, "y": y, "name": "skeleton", "hp": 9, "maxhp": 9, "atk": 4, "dfn": 1, "gold": 7})
        else:
            self.monsters.append({"x": x, "y": y, "name": "orc", "hp": 16, "maxhp": 16, "atk": 7, "dfn": 2, "gold": 15})

    def drop_item(self, room):
        x = random.randint(room[0], room[0]+room[2]-1)
        y = random.randint(room[1], room[1]+room[3]-1)
        if random.random() < 0.6:
            self.items.append({"x": x, "y": y, "kind": "gold", "amount": random.randint(3, 12)})
        else:
            self.items.append({"x": x, "y": y, "kind": "potion"})

    def monster_at(self, x, y):
        for m in self.monsters:
            if m["x"] == x and m["y"] == y:
                return m
        return None

    def item_at(self, x, y):
        for i in self.items:
            if i["x"] == x and i["y"] == y:
                return i
        return None

    def can_go(self, x, y):
        if x < 0 or y < 0 or x >= COLS or y >= ROWS:
            return False
        if self.tiles[y][x] == 1:
            return False
        return True

    def key_press(self, event):
        key = event.keysym.lower()
        if key in ("w", "up"): self.move(0, -1)
        elif key in ("s", "down"): self.move(0, 1)
        elif key in ("a", "left"): self.move(-1, 0)
        elif key in ("d", "right"): self.move(1, 0)
        elif key == "e": self.take_item()
        elif key == "r": self.drink_potion()
        elif key == "q": self.new_game()

    def move(self, dx, dy):
        p = self.player
        if self.game_over:
            return
        x = p["x"]+dx
        y = p["y"]+dy
        if not self.can_go(x, y):
            return
        m = self.monster_at(x, y)
        if m:
            self.hit(m)
            return
        p["x"] = x
        p["y"] = y
        self.auto_pick()
        if self.tiles[y][x] == 2:
            self.msg("you take the stairs")
            self.next_level()
            return
        self.monsters_turn()

    def auto_pick(self):
        p = self.player
        item = self.item_at(p["x"], p["y"])
        if not item:
            return
        self.items.remove(item)
        if item["kind"] == "gold":
            p["gold"] += item["amount"]
            self.msg("you pick up %d gold" % item["amount"])
        else:
            p["potions"] += 1
            self.msg("you pick up a potion")

    def monsters_turn(self):
        p = self.player
        for m in list(self.monsters):
            if random.random() < 0.45:
                continue
            dx = 0
            dy = 0
            if p["x"] > m["x"]: dx = 1
            elif p["x"] < m["x"]: dx = -1
            elif p["y"] > m["y"]: dy = 1
            elif p["y"] < m["y"]: dy = -1
            else: continue
            nx = m["x"]+dx
            ny = m["y"]+dy
            if not self.can_go(nx, ny):
                continue
            if self.monster_at(nx, ny):
                continue
            if nx == p["x"] and ny == p["y"]:
                self.player_take(m)
            else:
                m["x"] = nx
                m["y"] = ny

    def hit(self, m):
        dmg = max(1, self.player["atk"]-m["dfn"])
        m["hp"] -= dmg
        self.msg("you hit the %s for %d" % (m["name"], dmg))
        if m["hp"] <= 0:
            self.monsters.remove(m)
            self.player["gold"] += m["gold"]
            self.player["kills"] += 1
            self.msg("the %s dies" % m["name"])

    def player_take(self, m):
        p = self.player
        dmg = max(1, m["atk"]-p["dfn"])
        p["hp"] -= dmg
        self.msg("the %s hits you for %d" % (m["name"], dmg))
        if p["hp"] <= 0:
            p["hp"] = 0
            self.game_over = True
            self.msg("you die on level %d" % p["level"])

    def next_level(self):
        p = self.player
        p["level"] += 1
        p["maxhp"] += 4
        p["hp"] = p["maxhp"]
        p["atk"] += 1
        self.monsters = []
        self.items = []
        self.build_level()

    def take_item(self):
        p = self.player
        item = self.item_at(p["x"], p["y"])
        if item:
            self.auto_pick()
        else:
            self.msg("nothing here")

    def drink_potion(self):
        p = self.player
        if p["potions"] <= 0:
            self.msg("no potions left")
            return
        if p["hp"] >= p["maxhp"]:
            self.msg("you are already at full health")
            return
        p["potions"] -= 1
        p["hp"] = min(p["maxhp"], p["hp"]+8)
        self.msg("you drink a potion")

    def msg(self, text):
        self.msgs.append(text)
        if len(self.msgs) > 3:
            self.msgs.pop(0)

    def loop(self):
        self.draw()
        self.root.after(80, self.loop)

    def draw(self):
        c = self.canvas
        c.delete("all")
        for y in range(ROWS):
            for x in range(COLS):
                tile = self.tiles[y][x]
                if tile == 1:
                    col = "saddlebrown"
                elif tile == 2:
                    col = "darkslategray"
                else:
                    col = "dimgray"
                c.create_rectangle(x*TILE, y*TILE, x*TILE+TILE, y*TILE+TILE, fill=col, outline="black")
                if tile == 2:
                    c.create_text(x*TILE+TILE//2, y*TILE+TILE//2, text=">", fill="white")
        for i in self.items:
            if i["kind"] == "gold":
                c.create_text(i["x"]*TILE+TILE//2, i["y"]*TILE+TILE//2, text="$", fill="gold")
            else:
                c.create_text(i["x"]*TILE+TILE//2, i["y"]*TILE+TILE//2, text="?", fill="hotpink")
        p = self.player
        c.create_oval(p["x"]*TILE+6, p["y"]*TILE+6, p["x"]*TILE+TILE-6, p["y"]*TILE+TILE-6, fill="dodgerblue", outline="white")
        for m in self.monsters:
            if m["name"] == "rat":
                col = "gray60"
            elif m["name"] == "skeleton":
                col = "beige"
            else:
                col = "darkgreen"
            c.create_rectangle(m["x"]*TILE+4, m["y"]*TILE+4, m["x"]*TILE+TILE-4, m["y"]*TILE+TILE-4, fill=col, outline="black")
            frac = m["hp"]/m["maxhp"]
            c.create_rectangle(m["x"]*TILE+4, m["y"]*TILE, m["x"]*TILE+TILE-4, m["y"]*TILE+4, fill="black", outline="")
            c.create_rectangle(m["x"]*TILE+4, m["y"]*TILE, m["x"]*TILE+4+(TILE-8)*frac, m["y"]*TILE+4, fill="red", outline="")
        head = "level %d   hp %d/%d   atk %d   def %d   gold %d   potions %d   kills %d" % (
            p["level"], p["hp"], p["maxhp"], p["atk"], p["dfn"], p["gold"], p["potions"], p["kills"])
        self.info.config(text=head+"\n"+" ".join(self.msgs))
        if self.game_over:
            c.create_rectangle(0, 0, COLS*TILE, ROWS*TILE, fill="black", stipple="gray50")
            c.create_text(COLS*TILE//2, ROWS*TILE//2-20, text="you died", fill="red", font=("Arial", 28, "bold"))
            c.create_text(COLS*TILE//2, ROWS*TILE//2+20, text="gold %d   kills %d   press q to start over" % (p["gold"], p["kills"]), fill="white", font=("Arial", 12))

if __name__ == "__main__":
    root = tk.Tk()
    g = dungeon(root)
    root.mainloop()