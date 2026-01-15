import json
import os

# --- DONNÉES DES COULEURS ---
RAW_COLORS_DATA = [
    ("Black", 0, 0, 0),
    ("Dark Gray", 60, 60, 60),
    ("Gray", 120, 120, 120),
    ("Medium Gray", 170, 170, 170),
    ("Light Gray", 210, 210, 210),
    ("White", 255, 255, 255),
    ("Deep Red", 96, 0, 24),
    ("Dark Red", 165, 14, 30),
    ("Red", 237, 28, 36),
    ("Light Red", 250, 128, 114),
    ("Dark Orange", 228, 92, 26),
    ("Orange", 255, 127, 39),
    ("Gold", 246, 170, 9),
    ("Yellow", 249, 221, 59),
    ("Light Yellow", 255, 250, 188),
    ("Dark Goldenrod", 155, 131, 49),
    ("Goldenrod", 197, 173, 49),
    ("Light Goldenrod", 232, 212, 95),
    ("Dark Olive", 74, 107, 58),
    ("Olive", 90, 148, 74),
    ("Light Olive", 132, 197, 115),
    ("Dark Green", 14, 185, 104),
    ("Green", 19, 230, 123),
    ("Light Green", 135, 255, 94),
    ("Dark Teal", 12, 129, 110),
    ("Teal", 16, 174, 166),
    ("Light Teal", 19, 225, 190),
    ("Dark Cyan", 15, 121, 159),
    ("Cyan", 96, 247, 242),
    ("Light Cyan", 187, 250, 242),
    ("Dark Blue", 40, 80, 158),
    ("Blue", 64, 146, 227),
    ("Light Blue", 125, 199, 255),
    ("Dark Indigo", 77, 49, 184),
    ("Indigo", 107, 80, 246),
    ("Light Indigo", 153, 177, 251),
    ("Dark Slate Blue", 74, 66, 132),
    ("Slate Blue", 122, 113, 196),
    ("Light Slate Blue", 181, 174, 241),
    ("Dark Purple", 120, 12, 153),
    ("Purple", 170, 56, 185),
    ("Light Purple", 224, 159, 249),
    ("Dark Pink", 203, 0, 122),
    ("Pink", 236, 31, 128),
    ("Light Pink", 243, 141, 169),
    ("Dark Peach", 155, 82, 73),
    ("Peach", 209, 128, 120),
    ("Light Peach", 248, 181, 163),
    ("Dark Brown", 104, 70, 52),
    ("Brown", 149, 104, 42),
    ("Light Brown", 219, 164, 99),
    ("Dark Tan", 123, 99, 82),
    ("Tan", 156, 132, 107),
    ("Light Tan", 214, 181, 148),
    ("Dark Beige", 209, 128, 81),
    ("Beige", 248, 178, 119),
    ("Light Beige", 255, 197, 165),
    ("Dark Stone", 109, 100, 63),
    ("Stone", 148, 140, 107),
    ("Light Stone", 205, 197, 158),
    ("Dark Slate", 51, 57, 65),
    ("Slate", 109, 117, 141),
    ("Light Slate", 179, 185, 209),
]

# --- GÉNÉRATION AUTOMATIQUE ---
def _rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

GAME_COLORS = []
for name, r, g, b in RAW_COLORS_DATA:
    GAME_COLORS.append({
        "name": name,
        "rgb": (r, g, b),
        "hex": _rgb_to_hex(r, g, b)
    })

# --- GESTION DE LA SAUVEGARDE ---
import os
app_data_path = os.getenv('APPDATA')
app_folder = os.path.join(app_data_path, "ArcPlacer")

if not os.path.exists(app_folder):
    os.makedirs(app_folder)

CONFIG_FILE = os.path.join(app_folder, "config.json")

DEFAULT_CONFIG = {
    "color_name": "Black",
    "delay": "0.2"
}

def load_config():
    """Charge la config depuis AppData"""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(color_name, delay):
    """Sauvegarde la config dans AppData"""
    data = {
        "color_name": color_name,
        "delay": delay
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Erreur sauvegarde config : {e}")

# --- LOGIQUE DU BOT ---
class BotVision:
    @staticmethod
    def parse_rgb(string_rgb):
        try:
            return tuple(map(int, string_rgb.split(',')))
        except:
            return (0, 0, 0)

    @staticmethod
    def check_match(c1, c2, tol):
        return (abs(c1[0] - c2[0]) <= tol and
                abs(c1[1] - c2[1]) <= tol and
                abs(c1[2] - c2[2]) <= tol)

    @staticmethod
    def measure_blob_at(pixels, start_x, start_y, w, h, target_rgb, tol):
        start_x = max(0, min(start_x, w - 1))
        start_y = max(0, min(start_y, h - 1))

        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        limit = 100

        while min_x > 0 and (start_x - min_x) < limit:
            if not BotVision.check_match(pixels[min_x - 1, start_y], target_rgb, tol): break
            min_x -= 1
        while max_x < (w - 1) and (max_x - start_x) < limit:
            if not BotVision.check_match(pixels[max_x + 1, start_y], target_rgb, tol): break
            max_x += 1
        while min_y > 0 and (start_y - min_y) < limit:
            if not BotVision.check_match(pixels[start_x, min_y - 1], target_rgb, tol): break
            min_y -= 1
        while max_y < (h - 1) and (max_y - start_y) < limit:
            if not BotVision.check_match(pixels[start_x, max_y + 1], target_rgb, tol): break
            max_y += 1

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        return width, height, (min_x, min_y, max_x, max_y)