import os, sys, json, time, hmac, hashlib, uuid, threading, random, socket, platform
from datetime import datetime
from queue import Queue, Empty
import urllib.request, urllib.error
import tkinter as tk

# =========================
# PATHS
# =========================
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = app_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CFG = {
    "tool_name": "PHANTOM CORE",
    "endpoint_health": "http://127.0.0.1:5050/health",
    "endpoint_session": "http://127.0.0.1:5050/session",
    "shared_secret": "PHANTOM_CORE_SECRET_2026_SECURE",
    "user_key_sha256": "",
    "admin_key_sha256": ""
}

def load_cfg():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CFG, f, indent=2)
        return dict(DEFAULT_CFG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    for k, v in DEFAULT_CFG.items():
        d.setdefault(k, v)
    return d

def save_cfg(d):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

CFG = load_cfg()
TOOL_NAME = CFG.get("tool_name", "PHANTOM CORE")
ENDPOINT_HEALTH = CFG.get("endpoint_health")
ENDPOINT_SESSION = CFG.get("endpoint_session")
SHARED_SECRET = CFG.get("shared_secret", "")

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

USER_KEY_SHA = (CFG.get("user_key_sha256") or "").lower().strip()
ADMIN_KEY_SHA = (CFG.get("admin_key_sha256") or "").lower().strip()

# =========================
# THEME
# =========================
BG = "#050507"
PANEL = "#0b0b10"
PANEL2 = "#0e0e16"
CARD = "#0d0d14"
CARD2 = "#121225"
BORDER = "#1d1d2a"
TXT = "#d9d9e8"
MUTED = "#8c8ca6"
GREEN = "#8aff8a"
GREEN_DIM = "#2b7a2b"
RED = "#ff4d4d"
ACCENT = "#4aa3ff"

# =========================
# SECURITY (HMAC)
# =========================
def sign_payload(secret: str, ts: int, session_id: str) -> str:
    msg = f"{ts}:{session_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

# =========================
# HTTP
# =========================
def http_get_json(url, timeout=4):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read().decode("utf-8", errors="ignore")
            return True, json.loads(data)
    except Exception as e:
        return False, str(e)

def http_post_json(url, payload, timeout=7):
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="ignore")
            return True, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except:
            body = str(e)
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)

# =========================
# DATA (basic diagnostics)
# =========================
def collect_system():
    return {
        "hostname": socket.gethostname(),
        "username": os.environ.get("USERNAME", "unknown"),
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "python": platform.python_version(),
    }

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "unknown"

def collect_network():
    return {
        "local_ip": get_local_ip()
    }

def build_snapshot_payload(session_id: str, modules: dict):
    ts = int(time.time())
    payload = {
        "tool": TOOL_NAME,
        "session_type": "snapshot",
        "session_id": session_id,
        "secret": SHARED_SECRET,
        "timestamp": ts,
        "signature": sign_payload(SHARED_SECRET, ts, session_id),
        "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modules": modules
    }
    if modules.get("system"):
        payload.update(collect_system())
    if modules.get("network"):
        payload.update(collect_network())
    return payload

# =========================
# MATRIX RAIN (fast)
# =========================
class MatrixBG(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, highlightthickness=0, bg=BG)
        self.columns = []
        self.font = ("Consolas", 12, "bold")
        self.mouse_x = 99999
        self.fps_ms = 55
        self.col_w = 16
        self.max_cols = 90
        self.max_len = 18
        self.fade_stipple = "gray25"
        self.bind("<Configure>", self._on_resize)
        self.bind("<Motion>", self._on_mouse)

    def _on_mouse(self, e):
        self.mouse_x = e.x

    def _on_resize(self, _e=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 0 or h <= 0:
            return
        n = min(self.max_cols, max(22, w // self.col_w))
        cols = []
        for i in range(n):
            x = i * self.col_w + 8
            y = random.randint(-h, 0)
            speed = random.uniform(3.0, 7.0)
            length = random.randint(8, self.max_len)
            cols.append([x, y, speed, length])
        self.columns = cols

    def step(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 0 or h <= 0:
            self.after(self.fps_ms, self.step)
            return

        self.create_rectangle(0, 0, w, h, fill=BG, outline="", stipple=self.fade_stipple)

        mx = self.mouse_x
        for i in range(len(self.columns)):
            x, y, speed, length = self.columns[i]
            dist = abs(x - mx)
            boost = 1.0 + max(0.0, (180 - dist) / 180) * 0.35

            for j in range(length):
                yy = y - j * 16
                if 0 <= yy <= h:
                    ch = random.choice("01")
                    if j < 2:
                        fill = GREEN if dist < 200 else "#63ff63"
                    else:
                        fill = GREEN_DIM if dist < 220 else "#1d5a1d"
                    self.create_text(x, yy, text=ch, fill=fill, font=self.font)

            y += speed * boost
            if y - length * 16 > h + 80:
                y = random.randint(-h, 0)
                speed = random.uniform(3.0, 7.0)
                length = random.randint(8, self.max_len)

            self.columns[i] = [x, y, speed, length]

        self.after(self.fps_ms, self.step)

# =========================
# Rounded helper
# =========================
def rounded_rect(canvas, x1, y1, x2, y2, r=14, **kwargs):
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# =========================
# PAGES
# =========================
class LogsPage:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.content, bg=BG)
        self.canvas = tk.Canvas(self.frame, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        rounded_rect(self.canvas, 20, 20, 840, 590, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        self.canvas.create_text(40, 48, anchor="w", text="Logs", fill=TXT, font=("Segoe UI", 14, "bold"))

        self.box = tk.Text(self.frame, bg=BG, fg=GREEN, insertbackground=TXT, relief="flat", font=("Consolas", 10))
        self.canvas.create_window(40, 84, anchor="nw", window=self.box, width=780, height=470)
        self.append("Logs activés ✅")

    def append(self, line):
        self.box.insert("end", line + "\n")
        self.box.see("end")

    def clear(self):
        self.box.delete("1.0", "end")
        self.append("Logs cleared.")

    def sync(self):
        pass

class HomePage:
    def __init__(self, app):
        self.app = app
        self.last_send = "—"
        self.last_result = "—"
        self.frame = tk.Frame(app.content, bg=BG)
        self.canvas = tk.Canvas(self.frame, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        c = self.canvas
        c.delete("all")

        rounded_rect(c, 20, 20, 320, 300, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        c.create_text(40, 48, anchor="w", text="Connexion", fill=TXT, font=("Segoe UI", 14, "bold"))
        self.status_txt = c.create_text(40, 88, anchor="w", text="Statut: OFFLINE", fill=RED, font=("Consolas", 11, "bold"))
        c.create_text(40, 118, anchor="w", text=f"/health: {ENDPOINT_HEALTH}", fill=MUTED, font=("Consolas", 9))

        self.btn_connect = tk.Button(self.frame, text="🔌 CONNECTER", bg=ACCENT, fg="white",
                                     font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                                     command=self.app.connect)
        self.btn_disconnect = tk.Button(self.frame, text="⛔ DÉCONNECTER", bg=CARD, fg=TXT,
                                        font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                                        command=self.app.disconnect)
        c.create_window(40, 160, anchor="nw", window=self.btn_connect, width=240, height=40)
        c.create_window(40, 210, anchor="nw", window=self.btn_disconnect, width=240, height=40)

        rounded_rect(c, 340, 20, 840, 300, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        c.create_text(360, 48, anchor="w", text="Session", fill=TXT, font=("Segoe UI", 14, "bold"))
        self.launch_info = c.create_text(360, 88, anchor="w", text="Connecte-toi puis lance un snapshot.", fill=MUTED, font=("Segoe UI", 11))

        self.btn_launch = tk.Button(self.frame, text="▶ LANCER (1x)", bg=GREEN, fg="black",
                                    font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
                                    command=self.app.launch_snapshot)
        self.btn_stop = tk.Button(self.frame, text="■ STOP", bg=RED, fg="white",
                                  font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
                                  command=self.app.stop)
        c.create_window(360, 130, anchor="nw", window=self.btn_launch, width=220, height=42)
        c.create_window(590, 130, anchor="nw", window=self.btn_stop, width=180, height=42)

        rounded_rect(c, 360, 190, 840, 240, r=16, fill=CARD, outline=BORDER, width=1, stipple="gray25")
        rounded_rect(c, 360, 250, 840, 300, r=16, fill=CARD, outline=BORDER, width=1, stipple="gray25")
        self.sid_txt = c.create_text(380, 214, anchor="w", text="Session ID: —", fill=TXT, font=("Consolas", 11, "bold"))
        self.last_txt = c.create_text(380, 274, anchor="w", text="Dernier envoi: — | Résultat: —", fill=TXT, font=("Consolas", 11, "bold"))

        rounded_rect(c, 20, 320, 840, 590, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        c.create_text(40, 348, anchor="w", text="Aperçu (local)", fill=TXT, font=("Segoe UI", 14, "bold"))
        self.preview = tk.Text(self.frame, bg=BG, fg=GREEN, insertbackground=TXT, relief="flat", font=("Consolas", 10))
        c.create_window(40, 380, anchor="nw", window=self.preview, width=780, height=190)

    def sync(self):
        c = self.canvas
        if self.app.connected:
            c.itemconfigure(self.status_txt, text="Statut: CONNECTÉ ✅", fill=GREEN)
            c.itemconfigure(self.launch_info, text="Connexion établie. Snapshot possible.", fill=TXT)
        else:
            c.itemconfigure(self.status_txt, text="Statut: OFFLINE ❌", fill=RED)
            c.itemconfigure(self.launch_info, text="OFFLINE: bloque.", fill=MUTED)

        if self.app.launching:
            c.itemconfigure(self.launch_info, text="Envoi en cours…", fill=TXT)

        sid = self.app.session_id or "—"
        c.itemconfigure(self.sid_txt, text=f"Session ID: {sid}")
        c.itemconfigure(self.last_txt, text=f"Dernier envoi: {self.last_send} | Résultat: {self.last_result}")

        s = collect_system()
        n = collect_network()
        self.preview.delete("1.0", "end")
        self.preview.insert("end", f"Session: {sid}\n")
        self.preview.insert("end", f"System: {s['os']} | {s['arch']} | py {s['python']}\n")
        self.preview.insert("end", f"User: {s['username']} | Host: {s['hostname']}\n")
        self.preview.insert("end", f"Network: local {n['local_ip']}\n")

class ToolsPage:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.content, bg=BG)
        self.canvas = tk.Canvas(self.frame, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.buttons = []
        self._build()

    def _build(self):
        c = self.canvas
        c.delete("all")

        rounded_rect(c, 20, 20, 840, 590, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        c.create_text(40, 48, anchor="w", text="Outils", fill=TXT, font=("Segoe UI", 14, "bold"))
        self.hint = c.create_text(40, 78, anchor="w", text="OFFLINE: outils désactivés.", fill=MUTED, font=("Segoe UI", 10, "bold"))

        self.cb_sys = tk.Checkbutton(self.frame, text="System", variable=self.app.mod_system, bg=PANEL, fg=TXT, selectcolor=PANEL2)
        self.cb_net = tk.Checkbutton(self.frame, text="Network", variable=self.app.mod_network, bg=PANEL, fg=TXT, selectcolor=PANEL2)
        c.create_window(680, 44, anchor="nw", window=self.cb_sys)
        c.create_window(760, 44, anchor="nw", window=self.cb_net)

        base = [
            ("📌 Envoyer Snapshot", self.app.launch_snapshot),
            ("🩺 Health Check", self.app.connect),
            ("🔄 Nouvelle session", self.app.new_session),
            ("📋 Copier Session ID", self.copy_sid),
            ("🧾 Export report TXT", self.export_report),
            ("🗂 Ouvrir dossier tool", self.open_folder),
            ("🔌 Déconnecter", self.app.disconnect),
        ]
        admin = [
            ("🔒 Admin: Export JSON", self.admin_export_json),
        ]
        tools = base + (admin if self.app.admin_ok else [])

        for b in self.buttons:
            b.destroy()
        self.buttons = []

        x0, y0 = 40, 120
        bw, bh = 260, 52
        gapx, gapy = 18, 16
        cols = 2

        for i, (name, fn) in enumerate(tools):
            r = i // cols
            col = i % cols
            x = x0 + col * (bw + gapx)
            y = y0 + r * (bh + gapy)

            b = tk.Button(self.frame, text=name, bg=CARD, fg=TXT,
                          font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                          command=lambda f=fn: self.guard(f))
            b.bind("<Enter>", lambda e, bb=b: bb.configure(bg=CARD2, fg=GREEN))
            b.bind("<Leave>", lambda e, bb=b: bb.configure(bg=CARD, fg=TXT))
            c.create_window(x, y, anchor="nw", window=b, width=bw, height=bh)
            self.buttons.append(b)

    def guard(self, fn):
        if not self.app.connected:
            self.app.log("Bloqué: OFFLINE.")
            return
        fn()

    def sync(self):
        if self.app.connected:
            self.canvas.itemconfigure(self.hint, text="ONLINE ✅", fill=GREEN)
            for b in self.buttons:
                b.configure(state="normal")
        else:
            self.canvas.itemconfigure(self.hint, text="OFFLINE ❌", fill=MUTED)
            for b in self.buttons:
                b.configure(state="disabled")
        self._build()

    def copy_sid(self):
        sid = self.app.session_id or "—"
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(sid)
        self.app.log(f"Session ID copié -> {sid}")

    def export_report(self):
        sid = self.app.session_id or f"PC-{uuid.uuid4().hex[:8].upper()}"
        path = os.path.join(BASE_DIR, f"report_{sid}.txt")
        s = collect_system()
        n = collect_network()
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{TOOL_NAME} REPORT\nTime: {datetime.now()}\nSession: {sid}\n\n")
            for k, v in s.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")
            for k, v in n.items():
                f.write(f"{k}: {v}\n")
        self.app.log(f"Report exporté -> {path}")

    def open_folder(self):
        try:
            os.startfile(BASE_DIR)
        except Exception as e:
            self.app.log(f"open_folder fail ({e})")

    def admin_export_json(self):
        sid = self.app.session_id or f"PC-{uuid.uuid4().hex[:8].upper()}"
        modules = {"system": bool(self.app.mod_system.get()), "network": bool(self.app.mod_network.get())}
        p = build_snapshot_payload(sid, modules)
        path = os.path.join(BASE_DIR, f"payload_{sid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2)
        self.app.log(f"Export JSON -> {path}")

class KeyPage:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.content, bg=BG)
        self.canvas = tk.Canvas(self.frame, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        c = self.canvas
        c.delete("all")
        rounded_rect(c, 20, 20, 840, 590, r=18, fill=PANEL, outline=BORDER, width=1, stipple="gray25")
        c.create_text(40, 48, anchor="w", text="Key", fill=TXT, font=("Segoe UI", 14, "bold"))
        c.create_text(40, 88, anchor="w", text="Choisis une key et clique Set USER / Set ADMIN.", fill=MUTED, font=("Segoe UI", 10, "bold"))

        self.entry = tk.Entry(self.frame, bg=CARD, fg=TXT, insertbackground=TXT, relief="flat", font=("Consolas", 12))
        c.create_window(40, 140, anchor="nw", window=self.entry, width=540, height=38)

        self.btn_validate = tk.Button(self.frame, text="✅ VALIDER", bg=ACCENT, fg="white",
                                      font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                                      command=self._do_validate)
        c.create_window(600, 140, anchor="nw", window=self.btn_validate, width=200, height=38)

        self.btn_set_user = tk.Button(self.frame, text="Set USER", bg=CARD2, fg=TXT,
                                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                      command=self._set_user)
        self.btn_set_admin = tk.Button(self.frame, text="Set ADMIN", bg=RED, fg="white",
                                       font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                       command=self._set_admin)
        c.create_window(40, 200, anchor="nw", window=self.btn_set_user, width=170, height=34)
        c.create_window(220, 200, anchor="nw", window=self.btn_set_admin, width=170, height=34)

        self.status = c.create_text(40, 260, anchor="w", text="Statut: verrouillé", fill=RED, font=("Consolas", 11, "bold"))

    def _do_validate(self):
        ok, lvl = self.app.validate_key(self.entry.get())
        self.canvas.itemconfigure(self.status, text=f"Statut: {lvl}", fill=(GREEN if ok else RED))

    def _set_user(self):
        ok, msg = self.app.set_user_key(self.entry.get())
        self.app.log(msg)
        self.canvas.itemconfigure(self.status, text=("USER KEY SET ✅" if ok else "FAIL ❌"), fill=(GREEN if ok else RED))

    def _set_admin(self):
        ok, msg = self.app.set_admin_key(self.entry.get())
        self.app.log(msg)
        self.canvas.itemconfigure(self.status, text=("ADMIN KEY SET ✅" if ok else "FAIL ❌"), fill=(GREEN if ok else RED))

    def sync(self):
        pass

# =========================
# APP
# =========================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PHANTOM CORE")
        self.root.geometry("1220x720")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.bg = MatrixBG(self.root)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg.step()

        self.overlay = tk.Frame(self.root, bg=BG)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)

        self.queue = Queue()
        self.connected = False
        self.launching = False
        self.session_id = None
        self.key_ok = False
        self.admin_ok = False
        self.mod_system = tk.BooleanVar(value=True)
        self.mod_network = tk.BooleanVar(value=True)

        self.pages = {}
        self.nav_items = []
        self.current = None

        self._build_layout()
        self.root.after(120, self._poll)

    def _build_layout(self):
        self.top = tk.Frame(self.overlay, bg=PANEL, height=60)
        self.top.pack(side="top", fill="x")

        tk.Label(self.top, text=TOOL_NAME, fg=GREEN, bg=PANEL, font=("Segoe UI", 16, "bold")).pack(side="left", padx=18)
        self.pill = tk.Label(self.top, text="OFFLINE", fg=RED, bg=CARD, font=("Consolas", 11, "bold"), padx=12, pady=6)
        self.pill.pack(side="right", padx=18)

        body = tk.Frame(self.overlay, bg=BG)
        body.pack(fill="both", expand=True)

        self.side_w_closed = 78
        self.side_w_open = 270
        self.side = tk.Frame(body, bg=PANEL2, width=self.side_w_closed)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)

        self.side.bind("<Enter>", lambda e: self._side_anim(True))
        self.side.bind("<Leave>", lambda e: self._side_anim(False))

        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        tk.Label(self.side, text="MENU", fg=MUTED, bg=PANEL2, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(14, 6))
        self._nav_btn("🏠", "Accueil", "home")
        self._nav_btn("🧰", "Outils", "tools")
        self._nav_btn("🔑", "Key", "key")

        self.pages["home"] = HomePage(self)
        self.pages["tools"] = ToolsPage(self)
        self.pages["key"] = KeyPage(self)
        for p in self.pages.values():
            p.frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_page("home")

    def _nav_btn(self, icon, text, key):
        row = tk.Frame(self.side, bg=PANEL2)
        row.pack(fill="x", padx=10, pady=6)

        ind = tk.Frame(row, bg=PANEL2, width=4, height=46)
        ind.pack(side="left", fill="y")

        ico = tk.Label(row, text=icon, bg=CARD, fg=TXT, font=("Segoe UI", 11, "bold"), width=3, height=2)
        ico.pack(side="left", padx=(10, 0))

        lbl = tk.Label(row, text=text, bg=PANEL2, fg=TXT, font=("Segoe UI", 11, "bold"))
        lbl.pack(side="left", padx=12)

        def hover(on):
            if on:
                ico.configure(bg=CARD2, fg=GREEN)
                lbl.configure(fg=GREEN)
            else:
                if self.current != key:
                    ico.configure(bg=CARD, fg=TXT)
                    lbl.configure(fg=TXT)

        def click(_e=None):
            self.show_page(key)

        for w in (row, ind, ico, lbl):
            w.bind("<Enter>", lambda e: hover(True))
            w.bind("<Leave>", lambda e: hover(False))
            w.bind("<Button-1>", click)

        self.nav_items.append((key, ind, ico, lbl))

    def _side_anim(self, open_):
        target = self.side_w_open if open_ else self.side_w_closed
        cur = self.side.winfo_width()
        step = 16 if target > cur else -16

        def tick():
            nonlocal cur
            cur += step
            if (step > 0 and cur >= target) or (step < 0 and cur <= target):
                cur = target
            self.side.configure(width=cur)
            if cur != target:
                self.root.after(10, tick)
        tick()

    def show_page(self, key):
        self.current = key
        self.pages[key].frame.lift()

        for kk, ind, ico, lbl in self.nav_items:
            if kk == key:
                ind.configure(bg=GREEN)
                ico.configure(bg=CARD2, fg=GREEN)
                lbl.configure(fg=GREEN)
            else:
                ind.configure(bg=PANEL2)
                ico.configure(bg=CARD, fg=TXT)
                lbl.configure(fg=TXT)

        self.update_ui()

    def update_ui(self):
        self.pill.configure(text=("ONLINE" if self.connected else "OFFLINE"), fg=(GREEN if self.connected else RED))
        for p in self.pages.values():
            if hasattr(p, "sync"):
                p.sync()

    def ensure_logs_page(self):
        if "logs" in self.pages:
            return
        self.pages["logs"] = LogsPage(self)
        self.pages["logs"].frame.place(x=0, y=0, relwidth=1, relheight=1)
        self._nav_btn("📜", "Logs", "logs")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        if "logs" in self.pages:
            self.pages["logs"].append(line)

    # actions
    def connect(self):
        self.log("Connexion: /health ...")
        ok, data = http_get_json(ENDPOINT_HEALTH, timeout=4)
        if ok and isinstance(data, dict) and data.get("ok") is True:
            self.connected = True
            self.log("Connexion établie ✅")
        else:
            self.connected = False
            self.log(f"Connexion FAIL ❌ ({data})")
        self.update_ui()

    def disconnect(self):
        self.connected = False
        self.log("Déconnecté.")
        self.update_ui()

    def new_session(self):
        self.session_id = f"PC-{uuid.uuid4().hex[:8].upper()}"
        self.log(f"Nouvelle session: {self.session_id}")
        self.update_ui()

    def launch_snapshot(self):
        if not self.connected:
            self.log("Bloqué: OFFLINE.")
            return
        if self.launching:
            return
        if not self.session_id:
            self.new_session()

        self.launching = True
        self.log("Snapshot: envoi en cours…")
        self.update_ui()

        modules = {"system": bool(self.mod_system.get()), "network": bool(self.mod_network.get())}
        payload = build_snapshot_payload(self.session_id, modules)

        def worker():
            ok, info = http_post_json(ENDPOINT_SESSION, payload, timeout=8)
            self.queue.put(("sent", ok, info))

        threading.Thread(target=worker, daemon=True).start()

    def stop(self):
        self.launching = False
        self.log("Stop.")
        self.update_ui()

    def validate_key(self, raw_key: str):
        global USER_KEY_SHA, ADMIN_KEY_SHA
        k = (raw_key or "").strip()
        if not k:
            self.key_ok = False
            self.admin_ok = False
            self.update_ui()
            return False, "Key vide"

        ksha = sha256_hex(k).lower()
        if ADMIN_KEY_SHA and ksha == ADMIN_KEY_SHA:
            self.key_ok = True
            self.admin_ok = True
            self.ensure_logs_page()
            self.log("Admin key validée ✅")
            self.update_ui()
            return True, "ADMIN"
        if USER_KEY_SHA and ksha == USER_KEY_SHA:
            self.key_ok = True
            self.admin_ok = False
            self.ensure_logs_page()
            self.log("User key validée ✅")
            self.update_ui()
            return True, "USER"

        self.key_ok = False
        self.admin_ok = False
        self.update_ui()
        return False, "INVALIDE"

    def set_user_key(self, raw_key: str):
        global USER_KEY_SHA
        k = (raw_key or "").strip()
        if not k:
            return False, "Key vide"
        USER_KEY_SHA = sha256_hex(k).lower()
        CFG["user_key_sha256"] = USER_KEY_SHA
        save_cfg(CFG)
        return True, "User key enregistrée ✅"

    def set_admin_key(self, raw_key: str):
        global ADMIN_KEY_SHA
        k = (raw_key or "").strip()
        if not k:
            return False, "Key vide"
        ADMIN_KEY_SHA = sha256_hex(k).lower()
        CFG["admin_key_sha256"] = ADMIN_KEY_SHA
        save_cfg(CFG)
        return True, "Admin key enregistrée ✅"

    def _poll(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "sent":
                    ok, info = item[1], item[2]
                    self.launching = False
                    if ok:
                        self.log("Snapshot: OK ✅")
                        self.pages["home"].last_send = datetime.now().strftime("%H:%M:%S")
                        self.pages["home"].last_result = "OK ✅"
                    else:
                        self.log(f"Snapshot: FAIL ❌ ({info})")
                        self.pages["home"].last_send = datetime.now().strftime("%H:%M:%S")
                        self.pages["home"].last_result = "FAIL ❌"
                    self.update_ui()
        except Empty:
            pass
        self.root.after(120, self._poll)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    App().root.mainloop()