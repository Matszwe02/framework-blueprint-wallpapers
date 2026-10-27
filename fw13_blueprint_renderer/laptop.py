"""Framework Laptop 13 - per-laptop configuration (everything else is the shared engine in scripts/)."""

SLUG, TITLE, WATERMARK = "fw13", "LAPTOP 13", "13"
SOURCE_LINE = "SOURCE  GITHUB.COM/FRAMEWORKCOMPUTER/FRAMEWORK-LAPTOP-13   /   ASSEMBLY GFW00_3H_ID_MAIN_ASM   /   CC BY 4.0"
NOTE_LINE = "{used} PARTS"

SOURCES = {"s": "system", "m": "mbparts", "b": "bparts"}
USE_ALL = ["s", "m", "b"]
FORCE_GROUP = {"m": "MAINBOARD", "b": "BATTERY"}
LOGO_SOURCE, LOGO_PART = "s", "GFW00_3H_NB_ID_COVER_LOGO_1"
HINGE_CAD = (-4.0, 4.2)                        # same chassis / hinge as the Laptop 13 Pro
LID_ANGLE = 105.0
def extra_instances(SRC): return []

DROP = r"^(GFW00_3H_NB_ID_FRAME_REFER_1)$"      # duplicate of the hinge frame
PATH_RULES = []
GROUPS = [
 ("A_COVER",  "ALUMINIUM LID COVER",         "lid",  150, r"^(GFW_NB_ID_COVER_A|GFW00_3H_NB_ID_COVER_LOGO_1)$"),
 ("PLATES",   "HINGE PLATES + LID FRAME",    "lid",  118, r"^(GFW00_3H_NB_ID_HINGE_PLATE_[LR]_1|GFW00_3H_NB_ID_BEZEL_1_2)$"),
 ("PANEL",    "DISPLAY PANEL",               "lid",   86, r"^GFW00_3H_NB_ID_BEZEL_1_1$"),
 ("BEZEL",    "DISPLAY BEZEL + CAMERA",      "lid",   54, r"^GFW00_3H_NB_ID_BEZEL_(1_3|ALS_LENS_1|CAM_LENS_1|CAM_SWITCH|MIC_SWITCH|MIC_BRK_1|CAM_BRK_1|LED_1)$"),
 ("HINGE",    "HINGE CAP",                   "lid",   30, r"^GFW00_3H_NB_ID_BEZEL_HINGE_CAP_$"),
 ("KEYS",     "KEYBOARD",                    "base",  26, r"^FRAMEWORK_ID_KEYBOARD_ANSI_V.*$"),
 ("FPR",      "FINGERPRINT READER",          "base",  26, r"^GFW00_3H_NB_ID_C_COVER_REFER_4$"),
 ("HAPTIC",   "TOUCHPAD",                    "base",  12, r"^GFW00_3H_NB_ID_C_COVER_REFER_3$"),
 ("C_COVER",  "ALUMINIUM C-COVER",           "base",   0, r"^GFW00_3H_NB_ID_C_COVER_REFER_2$"),
 ("FRAME",    "HINGE FRAME",                 "base", -18, r"^GFW00_3H_NB_ID_FRAME_1$"),
 ("MAINBOARD","MAINBOARD",                   "base", -68, r"(?!)"),
 ("BATTERY",  "BATTERY",                     "base", -68, r"(?!)"),
 ("D_COVER",  "ALUMINIUM D-COVER",           "base", -88, r"^(GFW00_3H_NB_ID_D_COVER_REFER_[234]|GFW00_3H_NB_ID_CARD_LED_LENS_[23])$"),
 ("CARDS_R",  "EXPANSION CARDS",             "base", -88, r"^GFW00_3H_NB_ID_(USBC|SD)_CARD_1$"),
 ("CARDS_L",  "EXPANSION CARDS",             "base", -88, r"^GFW00_3H_NB_ID_(USBA|HDMI)_CARD_1$"),
]
GROUP_SLIDE = {"CARDS_R": (60.0, 0.0, "D_COVER"), "CARDS_L": (-60.0, 0.0, "D_COVER")}

POSES = {"closed": (35.0, 24.0, 560.0, (0.0, -115.0, -3.0), 0.0),
         "open": (29.0, 21.0, 770.0, (0.0, -70.0, 80.0), 0.0),
         "exploded": (58.0, 20.0, 1050.0, (0.0, -85.0, 38.0), 0.05)}

LEFT = ["KEYS", "HAPTIC", "C_COVER", "FRAME", "BATTERY", "D_COVER"]
RIGHT = ["A_COVER", "PLATES", "PANEL", "BEZEL", "HINGE", "FPR", "CARDS_R"]
LABEL_TEXT = {"D_COVER": {"id": "GFW00_3H_NB_ID_D_COVER_REFER_2"},
              "KEYS": {"id": "FRAMEWORK_ID_KEYBOARD_ANSI_V*"},
              "BATTERY": {"id": "FW13_BATTERY_3S1P"},
              "CARDS_R": {"id": "GFW00_3H_NB_ID_*_CARD_1", "detail": "30.0 x 30.0 x 6.8 MM  /  4 CARDS  /  USB-C, SD, USB-A, HDMI"}}

# ---- source CAD (downloaded into cad/ by scripts/fetch_cad.py; git-ignored) and the recipe that turns it into the cad/*.npz meshes (scripts/rebuild_cad.py)
CAD_FILES = {"system.stp": ("Framework-Laptop-13", "Framework Laptop 13 CAD.stp"),
             "battery.stp": ("Framework-Laptop-13", "Battery/FWKNAQ9_G01_20210911.stp")}
REBUILD = [("export", "system.stp", "system"), ("export", "battery.stp", "bparts"),
           ("tool", "mb_mesh.py"),
           ("edges", "system"), ("edges", "bparts"), ("edges", "mbparts"), ("logo",)]

SOURCES_MD = """* `Framework Laptop 13 CAD.stp` (Framework-Laptop-13 repo) - chassis shell, display bezel, keyboard, hinge frame and the four expansion cards (USB-C, SD, USB-A, HDMI)
* `Battery/FWKNAQ9_G01_20210911.stp` - battery
* `cad/mainboard.step` - detailed 3D mainboard ('Framework mainboard v2' by ManelTo, printables.com/model/1058946, CC BY 4.0);
  its placement (centred between the card slots, fan at the hinge side) is inferred."""
