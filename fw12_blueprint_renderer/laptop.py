"""Framework Laptop 12 - per-laptop configuration (everything else is the shared engine in scripts/)."""

SLUG, TITLE, WATERMARK = "fw12", "LAPTOP 12", "12"
SOURCE_LINE = "SOURCE  GITHUB.COM/FRAMEWORKCOMPUTER/FRAMEWORK-LAPTOP-12   /   ASSEMBLY SF_360_ID_D_ASM   /   CC BY 4.0"
NOTE_LINE = "{used} PARTS"

SOURCES = {"s": "system", "m": "mainboard", "b": "battery", "k": "keysparts"}
USE_ALL = ["s", "m", "b", "k"]
FORCE_GROUP = {"m": "MAINBOARD", "b": "BATTERY", "k": "KEYS"}
LOGO_SOURCE, LOGO_PART = "s", "SF_360_ID_D_LOGO"
# The 12 is a 360-degree convertible with a dual-axis hinge. Pivots read from the cylindrical faces of the hinge covers (CAD Y, Z): lid pivot and base pivot.
# The hinge covers are the link between them: the link turns half the lid angle about the base pivot, the lid the other half about the link's far end.
# At 360 degrees the lid has moved 2 x 10.3 mm down: under the base, cover against the feet, screen facing outward = tablet mode.
HINGE_CAD = (3.1, 3.55)                        # lid pivot
HINGE2_CAD = (-7.2, 3.55)                      # base pivot (link rotates about this)
LID_ANGLE = 360.0
# while the lid opens (one continuous motion) the base turns the opposite way about the hinge axis, so the machine arrives in tablet mode screen-up (no separate turn-over stage)
FLIP = dict(center=(0.0, -3.6, 3.55), angle=180.0, axis="width", follow_lid=True)
TIMING = dict(T_OPEN0=1.0, T_OPEN1=4.0, T_DIMS=5.0, T_EXPLODE=7.8, T_HOLD=11.2, T_COLLAPSE=13.4, T_CLOSE0=13.9, T_CLOSE1=16.9)   # one slower opening (3 s), same three still holds
def extra_instances(SRC): return []

DROP = r"^(?!)$"
PATH_RULES = []
GROUPS = [
 ("A_COVER",  "LID COVER",         "lid", -140, r"^(SF_360_ID_D_A_PART|SF_360_ID_D_LOGO)$"),
 ("A_TPU",    "LID TPU BUMPER",              "lid", -168, r"^SF_360_ID_D_A_TPU$"),
 ("PANEL",    "DISPLAY PANEL",               "lid", -202, r"^SF_360_ID_D_PANEL$"),
 ("BEZEL",    "DISPLAY BEZEL + CAMERA",      "lid", -234, r"^SF_360_ID_D_(B_PART|B_DOWN|B_DOWN_TPU|CAM_SH_BTN|SPK_SH_BTN|CAM_LENS)$"),
 ("HINGE",    "HINGE COVERS (LINK)",         "link",  30, r"^SF_360_ID_D_HC_[RL]$"),      # the hinge link: turns by half the lid angle
 ("KEYS",     "KEYBOARD",    "base",  50, r"(?!)"),          # Framework's 12 CAD has no keycaps: rebuilt from the cover's key openings (scripts/keys_from_openings.py)
 ("C_COVER",  "INPUT COVER",      "base",  26, r"^SF_360_ID_D_C_PART$"),
 ("HAPTIC",   "TOUCHPAD",                    "base",  12, r"^SF_360_ID_D_TP$"),
 ("C_INNER",  "WALLS, SPEAKER MESH + FIN",   "base", -18, r"^SF_360_ID_D_(C_RB_[LR]|FAKE_FIN_L|MESH_[LR]|REAR_WALL_[LR])$"),
 ("MAINBOARD","MAINBOARD",                   "base", -52, r"(?!)"),
 ("BATTERY",  "BATTERY",                     "base", -52, r"(?!)"),
 ("D_COVER",  "D-COVER",           "base", -88, r"^SF_360_ID_D_(D_PART|D_TPU|PWR_BTN|EX_BTN_[LR]|R_LED_LENS|L_LED_LENS)$"),
 ("CARDS_R",  "EXPANSION CARDS",             "base", -88, r"^SF_360_ID_D_EX_R[12]$"),
 ("CARDS_L",  "EXPANSION CARDS",             "base", -88, r"^SF_360_ID_D_EX_L[12]$"),
 ("FEET",     "RUBBER FEET",                 "base",-108, r"^SF_360_ID_D_(F_RB_[RL]|R_RB_R)$"),
]
GROUP_SLIDE = {"CARDS_R": (110.0, 0.0, "D_COVER"), "CARDS_L": (-110.0, 0.0, "D_COVER")}

POSES = {"closed": (35.0, 24.0, 540.0, (0.0, -107.0, -3.0), 0.0),
         "via": (32.0, 28.0, 900.0, (0.0, -10.0, 45.0), 0.0),           # halfway through the opening
         "open": (30.0, 34.0, 700.0, (0.0, 107.0, 10.0), 0.0),          # tablet mode: machine now lies behind the hinge, screen up
         "exploded": (48.0, 30.0, 1040.0, (0.0, 100.0, 25.0), 0.0)}

LEFT = ["KEYS", "C_COVER", "HAPTIC", "C_INNER", "MAINBOARD", "BATTERY", "D_COVER", "FEET"]
INTERNAL = ["C_INNER", "MAINBOARD", "BATTERY"]      # not rendered until they have moved apart (they would show through the key gaps)
RIGHT = ["A_COVER", "A_TPU", "PANEL", "BEZEL", "HINGE", "CARDS_R"]
LABEL_TEXT = {"KEYS": {"id": "KEYCAP_*", "detail": "{auto}"},
              "D_COVER": {"id": "SF_360_ID_D_D_PART"},
              "MAINBOARD": {"id": "FRAMEWORK_LAPTOP_12_MB_V01_ASM"},
              "BATTERY": {"id": "LFR20_BATTERY_BOX_50W"},
              "CARDS_R": {"id": "SF_360_ID_D_EX_[RL][12]", "detail": "31.3 x 30.0 x 6.7 MM  /  4 CARDS"}}

# ---- source CAD (downloaded into cad/ by scripts/fetch_cad.py; git-ignored) and the recipe that turns it into the cad/*.npz meshes (scripts/rebuild_cad.py)
CAD_FILES = {"system.stp": ("Framework-Laptop-12", "Framework Laptop 12 CAD.stp"),
             "battery.stp": ("Framework-Laptop-12", "Battery/Framework_Laptop_12_50_Battery.stp"),
             "mainboard.stp": ("Framework-Laptop-12", "Mainboard/FRAMEWORK_LAPTOP_12_MAINBOARD_V01.stp")}
REBUILD = [("export", "system.stp", "system"), ("export", "battery.stp", "battery"), ("export", "mainboard.stp", "mainboard"),
           ("tool", "keys_from_openings.py"),
           ("edges", "system"), ("edges", "battery"), ("edges", "mainboard"), ("edges", "keysparts"), ("logo",)]

SOURCES_MD = """* `Framework Laptop 12 CAD.stp` (Framework-Laptop-12 repo) - chassis, lid, input cover, expansion cards, feet
* `Battery/Framework_Laptop_12_50_Battery.stp` - battery
* `Mainboard/FRAMEWORK_LAPTOP_12_MAINBOARD_V01.stp` - mainboard (full 3D model, same chassis coordinate frame)
* Keycaps: the 12 CAD has none (the input cover is one solid with empty openings), so they are RECONSTRUCTED from the cover's 76 key openings (`scripts/keys_from_openings.py`)"""
