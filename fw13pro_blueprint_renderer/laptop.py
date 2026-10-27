"""Framework Laptop 13 Pro - per-laptop configuration (everything else is the shared engine in scripts/)."""
import numpy as np

SLUG, TITLE, WATERMARK = "fw13pro", "LAPTOP 13 PRO", "13 PRO"
SOURCE_LINE = "SOURCE  GITHUB.COM/FRAMEWORKCOMPUTER/FRAMEWORK-LAPTOP-13   /   ASSEMBLY SAKURA_MAIN_ASM   /   CC BY 4.0"
NOTE_LINE = "{used} PARTS"

# geometry sources: key -> exported mesh set in cad/ (see export_parts.py / extract_edges.py)
SOURCES = {"p": "parts", "c": "cparts", "m": "mbparts", "b": "bparts"}
USE_ALL = ["p", "m", "b"]                      # sources whose every instance is used ("c" only through extra_instances)
FORCE_GROUP = {"m": "MAINBOARD", "b": "BATTERY"}
LOGO_SOURCE, LOGO_PART = "p", "POC_P_13_LOGO_1"
HINGE_CAD = (-4.0, 4.2)                        # hinge pin axis (CAD Y, Z) -- read from the hinge bracket's cylindrical faces
LID_ANGLE = 105.0

def extra_instances(SRC):
    """Official USB-C card model (Laptop 13 system CAD, same chassis envelope) in all four slots; left side turned 180 deg about the slot centre."""
    base = [i for i in SRC["c"][1]["instances"] if i["name"] == "GFW00_3H_NB_ID_USBC_CARD_1"][0]
    M0 = np.vstack([np.array(base["m"]), [0, 0, 0, 1]]); out = []; cz = 42.8
    for side in "RL":
        for row in (0, 1):
            T = np.eye(4); T[2, 3] = 40.6 * row
            R = np.diag([-1.0, 1, -1, 1]); R[2, 3] = 2 * cz
            M = T @ (R if side == "L" else np.eye(4)) @ M0
            out.append({"proto": base["proto"], "name": f"USBC_CARD_{side}", "path": "classic/" + base["name"], "m": M[:3].tolist(), "src": "c"})
    return out

DROP = r"^(SAKURA_LOG_UP_AL_JYT|SAKURA_LOG_UP_AL_LITEON|LFP30_GFW30_.*|LFP30_LOGO)$"          # supplier variants / duplicate sets
PATH_RULES = [("BEZEL", "BEZEL_CAP_SUB", "HINGE")]
# group id -> (label, side, explode offset along lid/base normal [mm], name regex)
GROUPS = [
 ("A_COVER",  "ALUMINIUM LID COVER",         "lid",  150, r"^(POC_13_LCD_COVER_AL_1|POC_P_13_LOGO_1)$"),
 ("MAGNETS",  "LID MAGNETS + HINGE PLATES",  "lid",  126, r"^(POC_P_13_LCD_(MAGNET|MG_SIDE|SLEEP_MG|MG_HINGE|MG_CAM)_1|POC_P_13_LOG_LOW_MAGNET_1|POC_P_13_LCD_HINGE_PLATE_[LR]_1|IFGP6_LCD_.*)$"),
 ("PANEL_BRK","PANEL BRACKETS + ADHESIVE",   "lid",  102, r"^(POC_P_13_LCD_PANEL_BRK_L_1|POC_13_LCD_PANEL_BRK_R_1|POC_P?_?13_PANEL_ADHESIVE_.*|LFP30_PANEL_SPONGE_.*)$"),
 ("PANEL",    "DISPLAY PANEL",               "lid",   78, r"^(POC_13_BOE_.*|135LCM_.*|GFW30_135_FHD__HADS_A)$"),
 ("BEZEL",    "DISPLAY BEZEL + CAMERA",      "lid",   54, r"^(GFW30_LCD_BEZEL_1|GFW30_LCD_CAMERA_LENS_1|GFW30_LCD_BEZEL_ALS_LENS_1|GFW30_(MIC|CAMERA)_BTN.*|GFW30_LCD_MAGNET_BRK_1|GFW30_LCD_MAGNET_BRK_SIDE_1|GFW30_LCD_MG_BRK_SIDE_ADHESIVE_|GFW30_LCD_LED_LENS.*|GFW30_LCD_BEZEL_ADHESIVE_1)$"),
 ("HINGE",    "HINGES + BEZEL CAP",          "lid",   30, r"^(LFP30_HINGE_L_LCD_BRK|LFP30_LCD_HINGE_SUP_BRK_L2|GFW30_LCD_BEZEL_CAP_1|GFW30_LCD_MAGNET_BRK_HINGE_1|GFW30_LCD_MAGNET_BRK_CAP_1|30_SCREW_.*)$"),
 ("KEYS",     "KEYBOARD",                    "base",  26, r"^GFW30_KB_283X111X3-85_1_\d+$"),
 ("FPR",      "FINGERPRINT READER",          "base",  26, r"^(LILAC_FPR_ASSY_.*|GFW30_UP_SWITCH_RUBBER_1)$"),
 ("HAPTIC",   "HAPTIC TOUCHPAD",             "base",  12, r"^00_LILAC_HAPTIC_.*$"),
 ("C_COVER",  "ALUMINIUM C-COVER",           "base",   0, r"^SAKURA_LOG_UP_AL$"),
 ("C_INNER",  "GASKETS, FOAM + MYLAR",       "base", -18, r"^(GFW30_UP_RF_GASKET_1|SAKURA_LOG_UP_CU_FOIL|IFGP6_USB_IO_BRK_GASKET|GFW30_UP_NOISE_MYLAR_1|LFP30_LOG_UP_TP_SPONGE|LFP30_UP_SUPPORT_RUBBER)$"),
 ("RF_MESH",  "RF SHIELD MESH",              "base", -34, r"^GFW30_RF_METAL_MESH_1$"),
 ("CARDS",    "CARD BRACKETS + LATCHES",     "base", -50, r"^(LFP30_LOW_IO_CARD_BRK_[LR]_1|LFP30_LOG_LOW_IO_LATCH.*|LFP30_LOG_LOW_CARD_LENS)$"),
 ("MAINBOARD","MAINBOARD",                   "base", -68, r"(?!)"),          # assigned by source (3D board model), not by name
 ("BATTERY",  "BATTERY",                     "base", -68, r"(?!)"),          # assigned by source (official battery STEP), not by name
 ("D_COVER",  "ALUMINIUM D-COVER",           "base", -88, r"^LFP30_LOG_D_AL$"),
 ("CARDS_R",  "USB-C EXPANSION CARDS",       "base", -88, r"^USBC_CARD_R$"),
 ("CARDS_L",  "USB-C EXPANSION CARDS",       "base", -88, r"^USBC_CARD_L$"),
 ("FEET",     "RUBBER FEET",                 "base",-108, r"^LFP30_D_FOOT_.*$"),
]
GROUP_SLIDE = {"CARDS_R": (60.0, 0.0, "D_COVER"), "CARDS_L": (-60.0, 0.0, "D_COVER")}      # cards ride with the D-cover, then slide straight out sideways

# camera waypoints: (azimuth deg, elevation deg, ortho width mm, target (Blender xyz), horizontal shift)
POSES = {"closed": (35.0, 24.0, 560.0, (0.0, -115.0, -3.0), 0.0),
         "open": (29.0, 21.0, 770.0, (0.0, -70.0, 80.0), 0.0),
         "exploded": (58.0, 20.0, 1050.0, (0.0, -85.0, 38.0), 0.05)}

LEFT = ["KEYS", "HAPTIC", "C_COVER", "C_INNER", "BATTERY", "D_COVER", "FEET"]
RIGHT = ["A_COVER", "MAGNETS", "PANEL_BRK", "PANEL", "BEZEL", "HINGE", "FPR", "CARDS_R"]
LABEL_TEXT = {"KEYS": {"id": "GFW30_KB_283X111X3-85_1_*"},
              "BATTERY": {"id": "FW13_BATTERY_3S1P"},
              "CARDS_R": {"id": "GFW00_3H_NB_ID_USBC_CARD_1", "detail": "30.0 x 30.0 x 6.8 MM  /  4 PARTS"}}

# ---- source CAD (downloaded into cad/ by scripts/fetch_cad.py; git-ignored) and the recipe that turns it into the cad/*.npz meshes (scripts/rebuild_cad.py)
CAD_FILES = {"pro.stp": ("Framework-Laptop-13", "Framework Laptop 13 Pro CAD.stp"),
             "classic.stp": ("Framework-Laptop-13", "Framework Laptop 13 CAD.stp"),
             "battery.stp": ("Framework-Laptop-13", "Battery/FWKNAQ9_G01_20210911.stp")}
REBUILD = [("export", "pro.stp", "parts"), ("export", "classic.stp", "cparts"), ("export", "battery.stp", "bparts"),
           ("tool", "mb_mesh.py"),
           ("edges", "parts"), ("edges", "cparts"), ("edges", "bparts"), ("edges", "mbparts"), ("logo",)]

SOURCES_MD = """* `Framework Laptop 13 Pro CAD.stp` (Framework-Laptop-13 repo) - chassis, display, keyboard, haptic pad, gear logo outline, ...
* `Framework Laptop 13 CAD.stp` - the four USB-C expansion cards (the Pro CAD has none)
* `Battery/FWKNAQ9_G01_20210911.stp` - Laptop 13 battery
* `cad/mainboard.step` - detailed 3D mainboard ('Framework mainboard v2' by ManelTo, printables.com/model/1058946, CC BY 4.0);
  its placement (centred between the card slots, fan at the hinge side) is inferred."""
