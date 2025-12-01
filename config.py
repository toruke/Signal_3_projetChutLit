import os

# =========================================
#         CONFIGURATION GLOBALE
# =========================================

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATS_DIR = os.path.join(OUTPUT_DIR, "stats")
ALERT_API_URL = "http://127.0.0.1:5000/api/alert"
ALERT_MP3_PATH = os.path.join(BASE_DIR, "static", "alert.mp3")

# Paramètres Généraux
ROTATE_VIDEO = True
WINDOW_SCALE = 0.4
DEBUG = True
DISPLAY_VIDEO = True

# Paramètres de Détection
ANALYSIS_STRIDE = 5
CONSECUTIVE_VALIDATIONS = 5 
DARKNESS_THRESHOLD = 20
MAX_DY = 250  
SMOOTHING_WINDOW = 5 

# Réglages Image (Gamma/Contrast)
USER_GAMMA = 2.9
USER_BRIGHTNESS = 200
USER_CONTRAST = -67

# =========================================
#     PARAMÈTRES JOUR / NUIT
# =========================================

# --- MODE JOUR ---
DAY_BLUR = (5, 5)
DAY_THRESHOLD = 20
DAY_CLAHE = 1.0 
DAY_MIN_AREA = 5000000 
DY_DAY_THRESHOLD = 45

# --- MODE NUIT ---
NIGHT_BLUR = (3, 3)
NIGHT_THRESHOLD = 10
NIGHT_CLAHE = 3.5
NIGHT_MIN_AREA = 2000000 
DY_NIGHT_THRESHOLD = 20

TEST_CASES = {
    "chute_lumiere_lente_1.MOV" : True,
    "chute_lumiere_lente_2.MOV" : True,
    "chute_lumiere_loyde_1.MOV" : True,
    "chute_lumiere_loyde_2.MOV" : True,
    "chute_lumiere_loyde_3.MOV" : True,
    "chute_lumiere_loyde_bizzare.MOV" : True,
    "chute_lumiere_obstacle.mp4" : True,
    "chute_lumiere_retourne_loyde.MOV" : True,
    "pas_de_chute_lumiere_reveille_loyde.MOV" : False,
    "chute_noir_basic_1.mp4" : True,
    "chute_noir_basic_2.mp4" : True,
    "chute_noir_lente.mp4" : True,
    "pas_de_chute_lumiere_glissade.MOV" : False,
    "pas_de_chute_lumiere_assis_couche.MOV" : False,
    "pas_de_chute_lumiere_couche.MOV" : False,
    "pas_de_chute_lumiere_coussin.mp4" : False,
    "pas_de_chute_lumiere_eau.mp4" : False,
    "pas_de_chute_lumiere_lever_1.MOV" : False,
    "pas_de_chute_lumiere_lever_2.MOV" : False,
    "pas_de_chute_lumiere_loyde_objet.MOV" : False,
    "pas_de_chute_lumiere_loyde_rattrapage_bizzare.MOV" : False,
    "pas_de_chute_lumiere_mouvement_amples.MOV" : False,
    "pas_de_chute_lumiere_mouvement_fort.MOV" : False,
    "pas_de_chute_lumiere_mouvment_leger.MOV" : False,
    "pas_de_chute_lumiere_pipi.mp4" : False,
    "pas_de_chute_lumiere_retourne.mp4" : False,
    "pas_de_chute_lumiere_saut_1.MOV" : False,
    "pas_de_chute_lumiere_saut_2.MOV" : False,
    "pas_de_chute_noir_coussin.mp4" : False,
    "pas_de_chute_noir_eau.mp4" : False,
    "pas_de_chute_noir_mouvement.mp4" : False,
    "pas_de_chute_noir_retourne.mp4" : False,
    "pas_de_chute_penombre_multimouv.mp4" : False
}