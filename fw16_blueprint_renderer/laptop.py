"""Framework Laptop 16 (with Graphics Module) - per-laptop configuration (everything else is the shared engine in scripts/)."""

import numpy as np

SLUG, TITLE, WATERMARK = "fw16", "LAPTOP 16", "16"
SOURCE_LINE = "SOURCE  GITHUB.COM/FRAMEWORKCOMPUTER/FRAMEWORK-LAPTOP-16   /   ASSEMBLY IFW70_ID_D_ALL_ASM (GRAPHICS MODULE)   /   CC BY 4.0"
NOTE_LINE = "{used} PARTS"

SOURCES = {"s": "system", "m": "mainboard", "h": "hinge", "c": "cards", "e": "bestparts"}
USE_ALL = ["s", "m", "h", "e"]
FORCE_GROUP = {"m": "MAINBOARD", "e": "BATTERY"}
LOGO_SOURCE, LOGO_PART = "s", "GFW30_LOGO"
HINGE_CAD = (1.0, 4.1)                         # lid hinge pivot (CAD Y, Z): common axis of the lid bracket's cylindrical faces in the official hinge CAD
LID_ANGLE = 105.0
def extra_instances(SRC):
    """Six expansion cards (official card models from the Laptop 13 system CAD - same card form factor) in the 16's side slots. Slot centres (CAD z) are the
    three card receptacles per side on the official 16 mainboard (pitch 34.9 mm); cards enter from the side edge (x +-148.3 .. +-178.3)."""
    byname = {i["name"]: i for i in SRC["c"][1]["instances"]}
    out = []
    for side, names in (("R", ["USBC", "SD", "USBC"]), ("L", ["USBA", "HDMI", "USBA"])):
        for slot, kind in enumerate(names):
            base = byname[f"GFW00_3H_NB_ID_{kind}_CARD_1"]; M = np.vstack([np.array(base["m"]), [0, 0, 0, 1]])
            z0 = 96.65 + 34.9 * slot - 15.0                              # card z-start for this slot
            z_orig = 68.4 if kind in ("USBA", "SD") else 27.8            # card z-start in the 13's CAD
            T = np.eye(4); T[0, 3] = 30.0 if side == "R" else -30.0; T[1, 3] = -2.15; T[2, 3] = z0 - z_orig
            out.append({"proto": base["proto"], "name": f"CARD_{side}_{kind}", "path": "cards/" + base["name"], "m": (T @ M)[:3].tolist(), "src": "c"})
    return out

DROP = r"^(EXPANSION_CARD_COV1|IFW70_ID_D_KBCAP|IFW70_ID_D_NUMKB_FRAME_RGB|IFW70_ID_D_NUMKB_FRAME_RGB_PC|IFW70_ID_D_NUMKB_FRAME_PC|IFW70_ID_D_EXC_BTN_ADD018|FW_LOTUS_ID_NUMPAD_1_\d+_1)$"   # duplicate variants / per-key copies of merged parts
PATH_RULES = []
GROUPS = [
 ("A_COVER",   "LID COVER",                       "lid",  150, r"^(IFW70_ID_D_ACOVER|GFW30_LOGO|IFW70_ID_D_ANT_MYLAR)$"),
 ("PANEL",     "DISPLAY PANEL",                   "lid",  112, r"^IFW70_ID_D_SCREEN_GLASS$"),
 ("BEZEL",     "DISPLAY BEZEL + CAMERA",          "lid",   74, r"^(IFW70_ID_D_BEZEL|IFW70_ID_D_SWITH_PLATE|IFW70_ID_D_SWITCH|IFGP6_ID_D_CAMERALENS)$"),
 ("HINGE",     "HINGE CAP + LID BRACKET",         "lid",   36, r"^(IFW70_ID_D_HINGECAP|IFGP6_LCD_BRACKET_L)$"),
 ("KEYS",      "KEYBOARD + NUMPAD",               "base",  42, r"^(FW_LOTUS_ID_KEYBOARD|FW_LOTUS_ID_NUMPAD)$"),
 ("C_COVER",   "PALMREST + HINGE CAPS",           "base",  28, r"^(IFW70_ID_D_KBCAP_FINAL|IFW70_ID_D_LOGUP_CAP|IFW70_ID_D_LOGUP_FRONT|IFW70_ID_D_POWERBTN|IFW_ID_D_LOGUP_INNERCAP|IFW70_ID_D_SHELF_CAP_INNER|IFW70_ID_D_SHELF_CAP_OUTER)$"),
 ("FRAMES",    "INPUT FRAMES + UPPER PLATE",      "base",  14, r"^(IFW70_ID_D_KB_FRAME|IFW70_ID_D_NUMKB_FRAME|IFW70_ID_D_UPPLATE_N0613|IFW70_ID_D_UPP_FILM_COVER|IFW70_ID_D_UPP_FILM_MYL)$"),
 ("TOUCHPAD",  "TOUCHPAD PLATE",                  "base",   0, r"^(IFW70_ID_D_TP_PLATE|IFW70_ID_D_TPMYLAR|IFW70_ID_D_TP_SPACE_2|IFW70_ID_D_PULLTAPE)$"),
 ("HINGE_BASE","HINGE LINKS + BASE BRACKETS",     "base", -18, r"^(SOLID|SHELL|IFGP6_BASE_BRACKET_(R|L|L_2)|IFGP6_HINGE_RIVET)$"),
 ("MAINBOARD", "MAINBOARD",                       "base", -52, r"(?!)"),
 ("BATTERY",   "BATTERY",              "base", -52, r"(?!)"),          # no official battery CAD: sized from the free space in the chassis (scripts/battery_estimate.py)
 ("D_COVER",   "D-COVER",              "base", -86, r"^(IFW70_ID_D_DDOOR|IFW70_ID_D_EXC_BTN|IFW70_ID_D_SIDELED_[RL])$"),
 ("GPU",       "GRAPHICS MODULE",                 "base", -86, r"^(IFW70_ID_D_MXM|IFW70_ID_D_MXM_TOP)$"),
 ("CARDS_R",   "EXPANSION CARDS",                 "base", -86, r"^CARD_R_.*$"),
 ("CARDS_L",   "EXPANSION CARDS",                 "base", -86, r"^CARD_L_.*$"),
 ("BOTTOM",    "SHELF COVER + FEET",              "base",-114, r"^(IFW70_ID_D_MXM_BOT_COVER_1123|IFW70_ID_D_MXM_FRONT_FOOT|IFW70_ID_D_MXM_REAR_FOOT_1123)$"),
]
GROUP_SLIDE = {"GPU": (0.0, -85.0, "D_COVER"), "CARDS_R": (95.0, 0.0, "D_COVER"), "CARDS_L": (-95.0, 0.0, "D_COVER")}        # the graphics module rides with the D-cover, then slides straight out of the rear bay
INTERNAL = ["MAINBOARD", "BATTERY"]                              # not rendered until it has moved apart (it would show through the key gaps)

POSES = {"closed": (35.0, 24.0, 680.0, (0.0, -125.0, -5.0), 0.0),
         "open": (29.0, 21.0, 975.0, (0.0, -80.0, 100.0), 0.0),
         "exploded": (58.0, 20.0, 1300.0, (0.0, -92.0, 46.0), 0.05)}

LEFT = ["KEYS", "C_COVER", "FRAMES", "TOUCHPAD", "MAINBOARD", "BATTERY", "D_COVER", "BOTTOM"]
RIGHT = ["A_COVER", "PANEL", "BEZEL", "HINGE", "HINGE_BASE", "CARDS_R", "GPU"]
LABEL_TEXT = {"BATTERY": {"id": "FW16_BATTERY_4S1P", "detail": "{auto}"},
              "HINGE_BASE": {"id": "IFGP6_BASE_BRACKET_R"},
              "MAINBOARD": {"id": "IFGP6_MB_PCB"},
              "KEYS": {"id": "FW_LOTUS_ID_KEYBOARD"},
              "GPU": {"id": "IFW70_ID_D_MXM"},
              "CARDS_R": {"id": "EXPANSION_CARD", "detail": "30.0 x 30.0 x 6.8 MM  /  6 CARDS  /  USB-C, SD, USB-A, HDMI"}}

# ---- source CAD (downloaded into cad/ by scripts/fetch_cad.py; git-ignored; zips are extracted) and the recipe that turns it into the cad/*.npz meshes (scripts/rebuild_cad.py)
CAD_FILES = {"system_gpu.zip": ("Framework-Laptop-16", "Framework Laptop 16 with Graphics Module CAD.zip"),
             "mainboard.stp": ("Framework-Laptop-16", "Mainboard/Framework_Laptop_16_Mainboard_3D.stp"),
             "hinge.stp": ("Framework-Laptop-16", "Hinges/framework_laptop_16_hinge_assy_asm.stp"),
             "cards.stp": ("Framework-Laptop-13", "Framework Laptop 13 CAD.stp")}
REBUILD = [("export", "system_gpu/Framework_16_all_DIS_asm_0408.stp", "system"), ("export", "mainboard.stp", "mainboard"),
           ("export", "hinge.stp", "hinge"), ("export", "cards.stp", "cards"),
           ("tool", "battery_estimate.py"),
           ("edges", "system"), ("edges", "mainboard"), ("edges", "hinge"), ("edges", "cards"), ("edges", "bestparts"), ("logo",)]

SOURCES_MD = """* `Framework Laptop 16 with Graphics Module CAD.zip` -> `Framework_16_all_DIS_asm_0408.stp` (Framework-Laptop-16 repo) - chassis, lid, keyboard + numpad, touchpad, graphics module
* `Hinges/framework_laptop_16_hinge_assy_asm.stp` - hinge assembly
* `Mainboard/Framework_Laptop_16_Mainboard_3D.stp` - mainboard (full 3D model, same chassis coordinate frame)
* `Framework Laptop 13 CAD.stp` card models (USB-C, SD, USB-A, HDMI) - the 16 uses the same expansion-card form factor; slots from the mainboard receptacles
* There is no battery model or dimensions in Framework's Laptop 16 CAD (only 85 Wh / 4S1P). The battery shown is an ESTIMATE: four cells sized to the free pocket in the chassis (`scripts/battery_estimate.py`)."""
