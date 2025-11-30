import os
import cv2
import numpy as np
from collections import deque
import concurrent.futures
import time

# =========================================
#         CONFIGURATION DU TEST
# =========================================

VIDEOS_DIR = os.path.join("videos")

TEST_CASES = {
    "chute_lumiere_lente_1.MOV" : True,
    "chute_lumiere_lente_2.MOV" : True,
    "chute_lumiere_loyde_1.MOV" : True,
    "chute_lumiere_loyde_2.MOV" : True,
    "chute_lumiere_loyde_3.MOV" : True,
    "chute_lumiere_loyde_bizzare.MOV" : True,
    "chute_lumiere_obstacle.mp4" : True,
    "chute_lumiere_retourne_loyde.MOV" : True,
    "chute_lumiere_reveille_loyde.MOV" : True,
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

# =========================================
#   PARAMÈTRES
# =========================================

ROTATE_VIDEO = True
WINDOW_SCALE = 0.6
USER_GAMMA = 2.9
USER_BRIGHTNESS = 200
USER_CONTRAST = -67
ANALYSIS_STRIDE = 5
CONSECUTIVE_VALIDATIONS = 5
DARKNESS_THRESHOLD = 30
DAY_BLUR, DAY_THRESHOLD, DAY_MIN_AREA, DY_DAY_THRESHOLD = (5, 5), 30, 5000000, 50
NIGHT_BLUR, NIGHT_THRESHOLD, NIGHT_MIN_AREA, DY_NIGHT_THRESHOLD = (7, 7), 20, 2000000, 20

# =========================================
#   FONCTIONS
# =========================================

def adjust_gamma(image, gamma=1.0):
    if gamma == 0: return image
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def apply_user_settings(frame_gray):
    frame = adjust_gamma(frame_gray, gamma=USER_GAMMA)
    alpha = 1.0 + (USER_CONTRAST / 100.0)
    beta = USER_BRIGHTNESS
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    frame = clahe.apply(frame)
    return frame

def apply_light_condition(gray, brightness, darkness_threshold):
    if brightness < darkness_threshold:
        gray_proc = apply_user_settings(gray)
        return (gray_proc, NIGHT_THRESHOLD, NIGHT_MIN_AREA, DY_NIGHT_THRESHOLD)
    else:
        gray_proc = cv2.GaussianBlur(gray, DAY_BLUR, 0)
        return (gray_proc, DAY_THRESHOLD, DAY_MIN_AREA, DY_DAY_THRESHOLD)

# =========================================
#   MOTEUR D'ANALYSE
# =========================================

def analyze_video(video_filename):
    path = os.path.join(VIDEOS_DIR, video_filename)
    if not os.path.exists(path): return None 

    cap = cv2.VideoCapture(path)
    prev_gray = None
    y_history = deque(maxlen=ANALYSIS_STRIDE + 1)
    fall_counter = 0
    detected = False

    while True:
        ret, frame = cap.read()
        if not ret: break

        if ROTATE_VIDEO:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        gray_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray_raw)
        (gray_active, threshold_pixel, min_area_mode, dy_threshold_mode) = apply_light_condition(gray_raw, avg_brightness, DARKNESS_THRESHOLD)

        if prev_gray is not None:
            diff = cv2.absdiff(gray_active, prev_gray)
            _, motion_mask = cv2.threshold(diff, threshold_pixel, 255, cv2.THRESH_BINARY)
            kernel = np.ones((5, 5), np.uint8)
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
            moments = cv2.moments(motion_mask)
            area = moments["m00"]

            if area > min_area_mode:
                y_center = int(moments["m01"] / moments["m00"])
                # Extraction Bounding Box pour vérif forme
                x, y, w, h = cv2.boundingRect(motion_mask)
                is_horizontal = w*1.2 >= h # Condition de forme

                y_history.append(y_center)

                if len(y_history) > ANALYSIS_STRIDE:
                    current_dy = y_history[-1] - y_history[0]
                    if abs(y_history[-1] - y_history[-2]) < 3: current_dy = 0

                    # Condition combinée : Vitesse ET Forme Horizontale
                    if current_dy > dy_threshold_mode and is_horizontal:
                        fall_counter += 1
                    else:
                        if fall_counter > 0: fall_counter -= 1

                    if fall_counter >= CONSECUTIVE_VALIDATIONS:
                        detected = True
                        break 
            else:
                if len(y_history) > 0: y_history.popleft() 
                fall_counter = 0

        prev_gray = gray_active.copy()

    cap.release()
    return detected

# =========================================
#   LANCEMENT DU TEST
# =========================================

def process_video_task(item):
    filename, expected = item
    result = analyze_video(filename)
    return (filename, expected, result)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- DÉBUT DE LA SUITE DE TESTS (MODE PARALLÈLE - FILTRE FORME) ---")
    cpu_count = os.cpu_count()
    print(f"Utilisation de {cpu_count} processeurs en simultané 🚀")
    print("-" * 60)

    success_count = 0
    file_errors = 0
    total_videos = len(TEST_CASES)
    start_time = time.time()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        tasks = list(TEST_CASES.items())
        results_iterator = executor.map(process_video_task, tasks)

        for filename, expected_result, actual_result in results_iterator:
            status_symbol = ""
            status_text = ""
            if actual_result is None:
                status_symbol = "⚠️"
                status_text = "FICHIER INTROUVABLE"
                file_errors += 1
            elif actual_result == expected_result:
                status_symbol = "✅"
                status_text = "OK"
                success_count += 1
            else:
                status_symbol = "❌"
                attendu = "CHUTE" if expected_result else "RIEN"
                obtenu = "CHUTE" if actual_result else "RIEN"
                status_text = f"ERREUR (Attendu: {attendu} | Obtenu: {obtenu})"
            print(f"{status_symbol} [{filename[:35].ljust(35)}] : {status_text}")

    end_time = time.time()
    duration = end_time - start_time
    score = (success_count / total_videos) * 100

    print("-" * 60)
    if file_errors > 0: print(f"⚠️ ATTENTION : {file_errors} fichiers n'ont pas été trouvés.")
    print(f"Temps total : {duration:.2f} secondes")
    print(f"RESULTAT FINAL : {score:.1f}% de réussite ({success_count}/{total_videos})")
    print("=" * 60)