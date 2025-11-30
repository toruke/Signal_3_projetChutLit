import os
import cv2
import numpy as np
import requests
import pygame
from collections import deque

# =========================================
#         CONFIGURATION GÉNÉRALE
# =========================================

VIDEO_PATH = os.path.join("videos", "chute_lumiere_lente_1.MOV")

ROTATE_VIDEO = True
WINDOW_SCALE = 0.6

USER_GAMMA = 2.9
USER_BRIGHTNESS = 200
USER_CONTRAST = -67

ANALYSIS_STRIDE = 5
CONSECUTIVE_VALIDATIONS = 5 
DARKNESS_THRESHOLD = 30

DEBUG = True
DISPLAY_VIDEO = True
ALERT_API_URL = "http://127.0.0.1:5000/api/alert"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_MP3_PATH = os.path.join(BASE_DIR, "static", "alert.mp3")

# =========================================
#     PARAMÈTRES JOUR / NUIT
# =========================================

# --- MODE JOUR ---
DAY_BLUR = (5, 5)
DAY_THRESHOLD = 10
DAY_CLAHE = 1.0 
DAY_MIN_AREA = 5000000 
DY_DAY_THRESHOLD = 50 

# --- MODE NUIT ---
NIGHT_BLUR = (7, 7)
NIGHT_THRESHOLD = 5
NIGHT_CLAHE = 8
NIGHT_MIN_AREA = 2000000 
DY_NIGHT_THRESHOLD = 20 

# =========================================
#   FONCTIONS PRÉTRAITEMENT
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
    # 🌙 MODE NUIT
    if brightness < darkness_threshold:
        gray_proc = cv2.GaussianBlur(gray, NIGHT_BLUR, 0)
        clahe = cv2.createCLAHE(clipLimit=NIGHT_CLAHE, tileGridSize=(8, 8))
        gray_proc = clahe.apply(gray_proc)
        return (gray_proc, "MODE NUIT", (0, 165, 255), NIGHT_THRESHOLD, NIGHT_MIN_AREA, DY_NIGHT_THRESHOLD)
    # ☀️ MODE JOUR
    else:
        gray_proc = cv2.GaussianBlur(gray, DAY_BLUR, 0)
        return (gray_proc, "MODE JOUR", (0, 255, 0), DAY_THRESHOLD, DAY_MIN_AREA, DY_DAY_THRESHOLD)

# =========================================
#   INITIALISATION
# =========================================

try:
    pygame.mixer.init()
except Exception as e:
    print(f"⚠️ Erreur init audio : {e}")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Impossible d'ouvrir la vidéo.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
display_delay = max(1, int(1000 / fps))

prev_gray = None
frame_idx = 0
fall_detected = False
fall_frame_info = "Aucune chute"
y_history = deque(maxlen=ANALYSIS_STRIDE + 1)
fall_counter = 0
current_dy = 0
posture_text = "INCONNU" # Pour l'affichage

print("--- Analyse Hybride (Info Complète) ---")

# =========================================
#        BOUCLE PRINCIPALE
# =========================================

while True:
    ret, frame = cap.read()
    if not ret: break
    
    area = 0 
    
    if ROTATE_VIDEO:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

    gray_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray_raw)

    (gray_active, mode_text, color_mode, threshold_pixel, min_area_mode, dy_threshold_mode) = apply_light_condition(gray_raw, avg_brightness, DARKNESS_THRESHOLD)

    display_frame = cv2.cvtColor(gray_active, cv2.COLOR_GRAY2BGR) if mode_text == "MODE NUIT" else frame

    if prev_gray is not None:
        diff = cv2.absdiff(gray_active, prev_gray)
        _, motion_mask = cv2.threshold(diff, threshold_pixel, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
        moments = cv2.moments(motion_mask)
        area = moments["m00"]

        if area > min_area_mode:
            y_center = int(moments["m01"] / moments["m00"])
            x_center = int(moments["m10"] / moments["m00"])
            
            # --- RECUPERATION DU RECTANGLE ---
            x, y, w, h = cv2.boundingRect(motion_mask)
            
            # --- ANALYSE DE FORME (NOUVEAU) ---
            # Si largeur >= hauteur, alors horizontal (couché)
            is_horizontal = w*1.2 >= h  # Condition de forme élargie
            posture_text = "COUCHE" if is_horizontal else "DEBOUT"
            
            # Dessin
            color_rect = (0, 0, 255) if is_horizontal else (0, 255, 0) # Rouge si couché, Vert si debout
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), color_rect, 2)
            cv2.circle(display_frame, (x_center, y_center), 8, (0, 0, 255), -1)

            y_history.append(y_center)

            if len(y_history) > ANALYSIS_STRIDE:
                current_dy = y_history[-1] - y_history[0]
                if abs(y_history[-1] - y_history[-2]) < 3: current_dy = 0

                # --- DETECTION COMBINÉE (VITESSE + POSTURE) ---
                # On ne compte la chute que si :
                # 1. La vitesse est suffisante
                # 2. ET la personne est en position horizontale (filtre saut)
                if current_dy > dy_threshold_mode and is_horizontal:
                    fall_counter += 1
                else:
                    if fall_counter > 0: fall_counter -= 1

                if (not fall_detected) and fall_counter >= CONSECUTIVE_VALIDATIONS:
                    fall_detected = True
                    fall_frame_info = f"CHUTE: Frame {frame_idx}"
                    print(f"\n🚨 CHUTE VALIDÉE (Frame {frame_idx})")
                    try:
                        pygame.mixer.music.load(ALERT_MP3_PATH)
                        pygame.mixer.music.play()
                    except: pass
                    try:
                        requests.post(ALERT_API_URL, json={"frame": frame_idx, "source": VIDEO_PATH}, timeout=1)
                    except: pass
        else:
            if len(y_history) > 0: y_history.popleft()
            fall_counter = 0
            current_dy = 0
            posture_text = "---"

    prev_gray = gray_active.copy()
    frame_idx += 1

    # =========================================
    #       AFFICHAGE
    # =========================================

    if DISPLAY_VIDEO:
        height, width = display_frame.shape[:2]
        resized_frame = cv2.resize(display_frame, (int(width * WINDOW_SCALE), int(height * WINDOW_SCALE)))

        overlay = resized_frame.copy()
        cv2.rectangle(overlay, (0, 0), (280, 210), (0, 0, 0), -1) # Agrandit un peu le fond noir
        cv2.addWeighted(overlay, 0.6, resized_frame, 0.4, 0, resized_frame)

        font = cv2.FONT_HERSHEY_SIMPLEX
        
        cv2.putText(resized_frame, f"Frame: {frame_idx}", (10, 30), font, 0.6, (255, 255, 255), 1)
        cv2.putText(resized_frame, f"Lum: {avg_brightness:.1f}", (10, 60), font, 0.6, color_mode, 1)
        cv2.putText(resized_frame, f"Mode: {mode_text}", (10, 80), font, 0.5, color_mode, 1)

        color_dy = (0, 255, 0) if current_dy < dy_threshold_mode else (0, 0, 255)
        cv2.putText(resized_frame, f"dy: {current_dy} (Seuil {dy_threshold_mode})", (10, 110), font, 0.6, color_dy, 2)
        
        color_area = (0, 255, 255) if area > min_area_mode else (150, 150, 150)
        cv2.putText(resized_frame, f"Area: {int(area)}", (10, 140), font, 0.6, color_area, 1)

        # Affichage Posture
        color_posture = (0, 0, 255) if posture_text == "COUCHE" else (0, 255, 0)
        cv2.putText(resized_frame, f"Pos: {posture_text}", (10, 170), font, 0.6, color_posture, 2)

        color_alert = (255, 255, 255) if not fall_detected else (0, 0, 255)
        cv2.putText(resized_frame, fall_frame_info, (10, 200), font, 0.7, color_alert, 2)

        cv2.imshow("FallCall", resized_frame)
        if cv2.waitKey(display_delay) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()