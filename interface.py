import tkinter as tk
from tkinter import ttk
import pyautogui
import keyboard
import threading
import time
import random
import ctypes
import os
import sys
import math

# On importe la logique, les couleurs, et les fonctions de sauvegarde
from logic import BotVision, GAME_COLORS, load_config, save_config


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- CLASSE TOOLTIP ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#313244", foreground="#cdd6f4",
                         relief="solid", borderwidth=1, font=("Segoe UI", 8))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# --- APPLICATION PRINCIPALE ---
class WplaceBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ARC PLACER")

        # --- GESTION FERMETURE (Sauvegarde) ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- CONFIG WINDOWS ---
        self.setup_dpi_awareness()
        self.setup_dark_mode_title_bar()

        # --- FENÊTRE ---
        self.root.geometry("260x465")
        self.root.resizable(True, True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # --- ICONE ---
        try:
            img_path = resource_path(os.path.join("Assets", "Logo.png"))
            self.root.iconphoto(False, tk.PhotoImage(file=img_path))
        except Exception as e:
            print(f"Info: Pas de logo trouvé ({e})")

        # --- THEME ---
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#cba6f7"
        self.btn_color = "#313244"
        self.btn_active = "#45475a"
        self.highlight = "#89b4fa"
        self.border_color = "#45475a"

        self.root.configure(bg=self.bg_color)
        self.setup_styles()

        # --- VARIABLES & CHARGEMENT CONFIG ---
        self.running = False
        self.full_block_size = tk.IntVar(value=0)
        self.play_area = None
        self.tolerance = 15
        self.status_var = tk.StringVar(value="En attente...")

        # 1. On charge le fichier JSON
        config = load_config()
        saved_color_name = config.get("color_name", "Noir")
        saved_delay = config.get("delay", "0.2")

        # 2. On retrouve la couleur dans notre liste GAME_COLORS
        # (On utilise next() pour trouver la couleur par son nom, sinon on prend la dernière par défaut)
        target_col = next((c for c in GAME_COLORS if c["name"] == saved_color_name), GAME_COLORS[-1])

        # 3. On applique les valeurs
        self.target_color_rgb = target_col['rgb']
        self.target_color_name = tk.StringVar(value=target_col['name'])
        self.target_color_hex = target_col['hex']
        self.user_delay = tk.StringVar(value=saved_delay)

        self.create_widgets()

        # --- HOTKEYS ---
        try:
            keyboard.add_hotkey('s', self.toggle_bot_safe)
        except Exception as e:
            print(f"Erreur Hotkey: {e}")

    # --- SAUVEGARDE A LA FERMETURE ---
    def on_close(self):
        # On récupère les valeurs actuelles
        current_color = self.target_color_name.get()
        current_delay = self.user_delay.get()

        # On sauvegarde dans le fichier via logic.py
        save_config(current_color, current_delay)

        # On ferme l'appli proprement
        self.root.destroy()
        sys.exit()

    # --- NOUVELLE FONCTION : CALCUL DU CONTRASTE ---
    def get_contrast_color(self, rgb):
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        return "white" if luminance < 128 else "black"

    # --- SETUP SYSTÈME ---
    def setup_dpi_awareness(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    def setup_dark_mode_title_bar(self):
        try:
            self.root.update()
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.windll.user32.GetParent(self.root.winfo_id()),
                20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10), borderwidth=0,
                        focuscolor=self.bg_color)
        style.configure("TLabelframe", background=self.bg_color, foreground=self.accent_color,
                        bordercolor=self.border_color, lightcolor=self.bg_color, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.accent_color,
                        font=("Segoe UI", 9, "bold"))
        style.configure("TEntry", fieldbackground=self.btn_color, foreground="white", insertcolor="white",
                        bordercolor=self.bg_color, lightcolor=self.btn_color, borderwidth=0, relief="flat")
        style.configure("TButton", background=self.btn_color, foreground=self.fg_color, borderwidth=0,
                        font=("Segoe UI", 9), padding=6, relief="flat")
        style.map("TButton", background=[("active", self.btn_active), ("pressed", self.accent_color)],
                  foreground=[("pressed", self.bg_color)])
        style.configure("Start.TButton", background=self.accent_color, foreground=self.bg_color,
                        font=("Segoe UI", 11, "bold"), padding=10)
        style.map("Start.TButton", background=[("active", self.highlight), ("disabled", self.btn_color)],
                  foreground=[("disabled", "#6c7086")])

    def create_widgets(self):
        header = tk.Frame(self.root, bg=self.bg_color)
        header.pack(fill="x", pady=(15, 5))
        tk.Label(header, text="ARC PLACER", font=("Segoe UI", 16, "bold"), bg=self.bg_color,
                 fg=self.accent_color).pack()
        tk.Label(header, text="v2.0 • Mathis Maureau", font=("Segoe UI", 8), bg=self.bg_color, fg="#6c7086").pack()

        f_params = ttk.LabelFrame(self.root, text="Cible & Délai", padding=10)
        f_params.pack(fill="x", padx=15, pady=5)

        # 1. Selecteur de Couleur
        tk.Label(f_params, text="Couleur cible :", bg=self.bg_color, fg="#6c7086", font=("Segoe UI", 8)).pack(
            anchor="w")
        initial_fg = self.get_contrast_color(self.target_color_rgb)
        self.btn_color_pick = tk.Button(
            f_params,
            textvariable=self.target_color_name,
            bg=self.target_color_hex,
            fg=initial_fg,
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            command=self.open_color_palette
        )
        self.btn_color_pick.pack(fill="x", pady=(2, 10), ipady=5)

        # 2. Délai
        tk.Label(f_params, text="Délai Clic (sec) :", bg=self.bg_color, fg="#6c7086", font=("Segoe UI", 8)).pack(
            anchor="w")
        ttk.Entry(f_params, textvariable=self.user_delay, justify="center").pack(fill="x")

        # Setup Buttons
        f_conf = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        f_conf.pack(fill="x", padx=15, pady=5)
        self.btn_calib = ttk.Button(f_conf, text="1. Calibrer (Carré Plein)", command=self.start_auto_calib)
        self.btn_calib.pack(fill="x", pady=2)
        self.btn_zone = ttk.Button(f_conf, text="2. Zone de Jeu", command=self.start_zone_select)
        self.btn_zone.pack(fill="x", pady=2)
        self.lbl_info = tk.Label(f_conf, text="Non calibré", bg=self.bg_color, fg="#6c7086",
                                 font=("Segoe UI", 8, "italic"))
        self.lbl_info.pack(pady=(5, 0))

        # Actions
        f_act = tk.Frame(self.root, bg=self.bg_color)
        f_act.pack(fill="x", padx=15, pady=10)
        self.btn_start = ttk.Button(f_act, text="▶  START (Touche 'S')", command=self.toggle_bot, state="disabled",
                                    style="Start.TButton")
        self.btn_start.pack(fill="x")

        # Footer
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bg=self.btn_color, fg=self.fg_color,
                                   font=("Consolas", 8), anchor="w", padx=10, pady=5)
        self.status_bar.pack(side="bottom", fill="x")

    def log(self, message):
        self.status_var.set(f"> {message}")
        self.root.update_idletasks()

    def toggle_setup_buttons(self, state):
        self.btn_calib.config(state=state)
        self.btn_zone.config(state=state)

    def cancel_overlay(self, event=None):
        if hasattr(self, 'top') and self.top:
            self.top.destroy()
        self.toggle_setup_buttons("normal")
        self.log("Annulé.")

    # --- LOGIQUE PALETTE COULEUR ---
    def open_color_palette(self):
        self.toggle_setup_buttons("disabled")
        self.top = tk.Toplevel(self.root)
        self.top.title("Choisir une couleur")
        self.top.configure(bg=self.bg_color)
        self.top.attributes("-topmost", True)
        self.top.resizable(False, False)

        grid_frame = tk.Frame(self.top, bg=self.bg_color)
        grid_frame.pack(padx=10, pady=10)
        cols = 16

        for i, color in enumerate(GAME_COLORS):
            btn = tk.Button(
                grid_frame, bg=color['hex'], width=4, height=2, relief="flat", cursor="hand2",
                command=lambda c=color: self.select_color_from_palette(c)
            )
            row = i // cols
            col = i % cols
            btn.grid(row=row, column=col, padx=2, pady=2)
            ToolTip(btn, color['name'])

        self.top.bind("<Escape>", self.cancel_overlay)
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2)

    def select_color_from_palette(self, color_data):
        self.target_color_rgb = color_data['rgb']
        self.target_color_name.set(color_data['name'])
        self.target_color_hex = color_data['hex']
        new_fg = self.get_contrast_color(self.target_color_rgb)
        self.btn_color_pick.configure(bg=self.target_color_hex, fg=new_fg)
        self.top.destroy()
        self.toggle_setup_buttons("normal")
        self.log(f"Cible : {color_data['name']}")

    # --- GESTION DU BOT ---
    def toggle_bot_safe(self):
        self.root.after(0, self.toggle_bot)

    def toggle_bot(self):
        if not self.running:
            self.running = True
            self.btn_start.config(text="⏹ STOP (Touche 'Q')", style="TButton")
            self.log("RUNNING... ('Q' pour stop)")
            threading.Thread(target=self.bot_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_start.config(text="▶  START (Touche 'S')", style="Start.TButton")
            self.log("Arrêté.")

    def bot_loop(self):
        target_rgb = self.target_color_rgb
        ref_size = self.full_block_size.get()
        tol = self.tolerance
        threshold = ref_size * 0.7
        scan_step = 4

        try:
            base_delay = float(self.user_delay.get().replace(',', '.'))
            if base_delay < 0.01: base_delay = 0.01
        except:
            base_delay = 0.1

        pic_test = pyautogui.screenshot()
        w_s, h_s = pic_test.size
        sx, sy, ex, ey = 20, 100, w_s - 20, h_s - 20
        if self.play_area:
            sx, sy, ex, ey = self.play_area

        while self.running:
            if keyboard.is_pressed('q'):
                self.root.after(0, self.toggle_bot)
                break

            pic = pyautogui.screenshot()
            pixels = pic.load()
            found = False
            processed_zones = []

            y = sy
            while y < ey:
                if not self.running: break
                x = sx
                while x < ex:
                    if keyboard.is_pressed('q'): break
                    if self.is_in_processed_zone(x, y, processed_zones):
                        x += scan_step;
                        continue
                    if not BotVision.check_match(pixels[x, y], target_rgb, tol):
                        x += scan_step;
                        continue

                    blob_w, blob_h, bbox = BotVision.measure_blob_at(pixels, x, y, w_s, h_s, target_rgb, tol)
                    blob_size = max(blob_w, blob_h)
                    processed_zones.append(bbox)

                    if blob_size < threshold:
                        cx, cy = (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
                        if sx <= cx <= ex and sy <= cy <= ey:
                            ox, oy = random.randint(-1, 1), random.randint(-1, 1)
                            pyautogui.click(cx + ox, cy + oy)
                            actual_delay = base_delay + random.uniform(0, base_delay * 0.3)
                            time.sleep(actual_delay)
                            found = True
                    x = bbox[2] + 2
                y += scan_step
            if not found: time.sleep(0.5)

    def is_in_processed_zone(self, x, y, zones):
        for z in zones:
            if z[0] <= x <= z[2] and z[1] <= y <= z[3]: return True
        return False

    # --- CALIBRATION ---
    def start_zone_select(self):
        self.toggle_setup_buttons("disabled")
        self.log("Encadre la zone de jeu...")
        self.top = tk.Toplevel(self.root)
        self.top.attributes('-fullscreen', True);
        self.top.attributes('-alpha', 0.3)
        self.top.config(cursor="crosshair")
        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>",
                         lambda e: setattr(self, 'start_x', e.x) or setattr(self, 'start_y', e.y) or setattr(self,
                                                                                                             'rect_id',
                                                                                                             self.canvas.create_rectangle(
                                                                                                                 e.x,
                                                                                                                 e.y,
                                                                                                                 e.x,
                                                                                                                 e.y,
                                                                                                                 outline="#cba6f7",
                                                                                                                 width=2,
                                                                                                                 fill="#cba6f7",
                                                                                                                 stipple="gray25")))
        self.canvas.bind("<B1-Motion>",
                         lambda e: self.canvas.coords(self.rect_id, self.start_x, self.start_y, e.x, e.y))
        self.canvas.bind("<ButtonRelease-1>", self.on_zone_end)
        self.top.bind("<Escape>", self.cancel_overlay)

    def on_zone_end(self, event):
        self.play_area = (min(self.start_x, event.x), min(self.start_y, event.y), max(self.start_x, event.x),
                          max(self.start_y, event.y))
        self.top.destroy()
        w, h = self.play_area[2] - self.play_area[0], self.play_area[3] - self.play_area[1]
        self.toggle_setup_buttons("normal")
        self.log("Zone définie !")
        self.update_info_label()

    def start_auto_calib(self):
        self.toggle_setup_buttons("disabled")
        self.log("Overlay actif. Clique sur un PLEIN.")
        self.top = tk.Toplevel(self.root)
        self.top.attributes('-fullscreen', True);
        self.top.attributes('-alpha', 0.3)
        self.top.config(cursor="crosshair")
        self.canvas = tk.Canvas(self.top, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonRelease-1>", self.run_calib_scan)
        self.top.bind("<Escape>", self.cancel_overlay)

    def run_calib_scan(self, event):
        self.root.update();
        time.sleep(0.1)
        pic = pyautogui.screenshot()
        target = pic.load()[event.x, event.y]
        width, height, bbox = BotVision.measure_blob_at(pic.load(), event.x, event.y, pic.width, pic.height, target, 30)
        self.canvas.delete("all")
        self.canvas.create_rectangle(bbox[0], bbox[1], bbox[2], bbox[3], outline="#ff0000", width=3)
        self.root.update()
        size = max(width, height)
        if size < 5:
            self.log("Erreur: Trop petit.")
            self.root.after(1000, lambda: (self.top.destroy(), self.toggle_setup_buttons("normal")))
            return
        time.sleep(0.5);
        self.top.destroy()
        self.toggle_setup_buttons("normal")
        self.full_block_size.set(size)
        self.update_info_label()
        self.btn_start.config(state="normal")
        self.log(f"Calibré ! Ref: {size}px.")

    def update_info_label(self):
        txt = f"Ref: {self.full_block_size.get()}px"
        if self.play_area:
            w, h = self.play_area[2] - self.play_area[0], self.play_area[3] - self.play_area[1]
            txt += f" | Zone: {w}x{h}"
        self.lbl_info.config(text=txt, fg="#a6e3a1")