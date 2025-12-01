import os
import cv2
import numpy as np
import requests
import pygame
import matplotlib.pyplot as plt
from collections import deque
import config as cfg

# =========================================
#   SELECTION INTERACTIVE DE LA VIDEO
# =========================================

def select_video():
    print(f"\n--- SELECTION VIDEO ({cfg.VIDEOS_DIR}) ---")
    
    # Récupérer la liste des fichiers vidéo
    try:
        files = [f for f in os.listdir(cfg.VIDEOS_DIR) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    except FileNotFoundError:
        print(f"❌ Erreur : Le dossier '{cfg.VIDEOS_DIR}' n'existe pas.")
        return None

    if not files:
        print("❌ Aucune vidéo trouvée dans le dossier.")
        return None

    # Afficher la liste numérotée
    for i, f in enumerate(files):
        print(f"[{i+1}] {f}")
    
    print("[0] Quitter")

    # Demander le choix à l'utilisateur
    while True:
        try:
            choice = int(input("\nEntrez le numéro de la vidéo : "))
            if choice == 0:
                return None
            if 1 <= choice <= len(files):
                selected_file = files[choice - 1]
                return os.path.join(cfg.VIDEOS_DIR, selected_file)
            print("❌ Numéro invalide.")
        except ValueError:
            print("❌ Veuillez entrer un nombre entier.")

# Appel de la fonction de sélection
VIDEO_PATH = select_video()

if VIDEO_PATH is None:
    print("Au revoir !")
    exit() # Arrête le script proprement

print(f"\n✅ Lancement de : {os.path.basename(VIDEO_PATH)}")

# =========================================
#   INITIALISATION AUDIO / VIDEO
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

# =========================================
#   FONCTION LOCALES
# =========================================

def apply_light_condition(gray, brightness):
    """
    Retourne les paramètres et aussi les INFOS D'AFFICHAGE (Textes, Couleurs)
    """
    if brightness < cfg.DARKNESS_THRESHOLD:
        gray_proc = cv2.GaussianBlur(gray, cfg.NIGHT_BLUR, 0)
        clahe = cv2.createCLAHE(clipLimit=cfg.NIGHT_CLAHE, tileGridSize=(8, 8))
        gray_proc = clahe.apply(gray_proc)
        return (gray_proc, "MODE NUIT", (0, 165, 255), cfg.NIGHT_THRESHOLD, cfg.NIGHT_MIN_AREA, cfg.DY_NIGHT_THRESHOLD)
    else:
        gray_proc = cv2.GaussianBlur(gray, cfg.DAY_BLUR, 0)
        return (gray_proc, "MODE JOUR", (0, 255, 0), cfg.DAY_THRESHOLD, cfg.DAY_MIN_AREA, cfg.DY_DAY_THRESHOLD)

# =========================================
#        BOUCLE PRINCIPALE
# =========================================

prev_gray = None
frame_idx = 0
fall_detected = False
fall_frame_info = "Aucune chute"
fall_detected_frame = None

y_history = deque(maxlen=cfg.ANALYSIS_STRIDE + 1)
y_buffer_smooth = deque(maxlen=cfg.SMOOTHING_WINDOW)

fall_counter = 0
current_dy = 0
posture_text = "---"

# Data pour le graph final
data_frames, data_dy, data_brightness, data_area = [], [], [], []

print("--- Analyse Hybride (Interface Complète) ---")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    area = 0 
    posture_text = "---"
    
    if cfg.ROTATE_VIDEO:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

    gray_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray_raw)

    (gray_active, 
     mode_text, 
     color_mode, 
     threshold_pixel, 
     min_area_mode, 
     dy_threshold_mode) = apply_light_condition(gray_raw, avg_brightness)

    display_frame = cv2.cvtColor(gray_active, cv2.COLOR_GRAY2BGR) if mode_text == "MODE NUIT" else frame

    if prev_gray is not None:
        diff = cv2.absdiff(gray_active, prev_gray)
        _, motion_mask = cv2.threshold(diff, threshold_pixel, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
        moments = cv2.moments(motion_mask)
        area = moments["m00"]

        if area > min_area_mode:
            y_raw = int(moments["m01"] / moments["m00"])
            x_center = int(moments["m10"] / moments["m00"])
            
            y_buffer_smooth.append(y_raw)
            y_smooth = int(sum(y_buffer_smooth) / len(y_buffer_smooth))
            
            x, y, w, h = cv2.boundingRect(motion_mask)
            is_horizontal = w*1.2 >= h 
            posture_text = "COUCHE" if is_horizontal else "DEBOUT"
            
            if cfg.DISPLAY_VIDEO:
                color_rect = (0, 0, 255) if is_horizontal else (0, 255, 0)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), color_rect, 2)
                cv2.circle(display_frame, (x_center, y_smooth), 8, (0, 0, 255), -1) 

            y_history.append(y_smooth)

            if len(y_history) > cfg.ANALYSIS_STRIDE:
                current_dy = y_history[-1] - y_history[0]
                if abs(y_history[-1] - y_history[-2]) < 3: current_dy = 0

                if (current_dy > dy_threshold_mode) and (current_dy < cfg.MAX_DY) and is_horizontal:
                    fall_counter += 1
                else:
                    if fall_counter > 0: fall_counter -= 1

                if (not fall_detected) and fall_counter >= cfg.CONSECUTIVE_VALIDATIONS:
                    fall_detected = True
                    fall_detected_frame = frame_idx
                    fall_frame_info = f"CHUTE: Frame {frame_idx}"
                    print(f"\n🚨 CHUTE VALIDÉE (Frame {frame_idx})")
                    try:
                        pygame.mixer.music.load(cfg.ALERT_MP3_PATH)
                        pygame.mixer.music.play()
                        requests.post(cfg.ALERT_API_URL, json={"frame": frame_idx, "source": VIDEO_PATH}, timeout=1)
                    except: pass
        else:
            if len(y_history) > 0: y_history.popleft()
            y_buffer_smooth.clear()
            fall_counter = 0
            current_dy = 0

    prev_gray = gray_active.copy()
    
    data_frames.append(frame_idx)
    data_dy.append(current_dy)
    data_brightness.append(avg_brightness)
    data_area.append(area)
    
    frame_idx += 1

    if cfg.DISPLAY_VIDEO:
        height, width = display_frame.shape[:2]
        resized_frame = cv2.resize(display_frame, (int(width * cfg.WINDOW_SCALE), int(height * cfg.WINDOW_SCALE)))
        
        overlay = resized_frame.copy()
        cv2.rectangle(overlay, (0, 0), (320, 230), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, resized_frame, 0.4, 0, resized_frame)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        cv2.putText(resized_frame, f"Frame: {frame_idx}", (10, 30), font, 0.6, (255, 255, 255), 1)
        cv2.putText(resized_frame, f"{mode_text} (Lum: {avg_brightness:.0f})", (10, 60), font, 0.6, color_mode, 2)
        
        if current_dy > cfg.MAX_DY:
            color_dy = (0, 0, 255) ; txt_dy = f"dy: {current_dy} (IGNORED)"
        elif current_dy > dy_threshold_mode:
            color_dy = (0, 165, 255) ; txt_dy = f"dy: {current_dy} (> {dy_threshold_mode})"
        else:
            color_dy = (0, 255, 0) ; txt_dy = f"dy: {current_dy} (Seuil {dy_threshold_mode})"
        cv2.putText(resized_frame, txt_dy, (10, 90), font, 0.6, color_dy, 2)

        color_area = (0, 255, 255) if area > min_area_mode else (150, 150, 150)
        cv2.putText(resized_frame, f"Area: {int(area)}", (10, 120), font, 0.6, color_area, 1)
        cv2.putText(resized_frame, f"Min Area: {min_area_mode}", (10, 140), font, 0.5, color_area, 1)

        color_pos = (0, 0, 255) if posture_text == "COUCHE" else (0, 255, 0)
        cv2.putText(resized_frame, f"Pos: {posture_text}", (10, 170), font, 0.6, color_pos, 2)

        color_alert = (255, 255, 255) if not fall_detected else (0, 0, 255)
        cv2.putText(resized_frame, fall_frame_info, (10, 210), font, 0.7, color_alert, 2)

        cv2.imshow("FallCall", resized_frame)
        if cv2.waitKey(display_delay) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()

# =========================================
#       GENERATION DU GRAPHIQUE
# =========================================
print("📊 Génération du graphique...")
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

if len(data_frames) > 0:
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    ax1.plot(data_frames, data_dy, label="Vitesse (dy)", color="blue")
    ax1.axhline(y=cfg.DY_DAY_THRESHOLD, color='green', linestyle='--', label="Seuil Jour")
    ax1.axhline(y=cfg.DY_NIGHT_THRESHOLD, color='orange', linestyle='--', label="Seuil Nuit")
    ax1.set_ylabel("Vitesse (px/s)")
    if fall_detected_frame:
        ax1.axvline(x=fall_detected_frame, color='red', linewidth=2, label="Chute")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(data_frames, data_area, label="Surface", color="purple")
    ax2.axhline(y=cfg.DAY_MIN_AREA, color='green', linestyle='--')
    ax2.axhline(y=cfg.NIGHT_MIN_AREA, color='orange', linestyle='--')
    ax2.set_ylabel("Pixels²")
    ax2.grid(True)

    ax3.plot(data_frames, data_brightness, label="Luminosité", color="gold")
    ax3.axhline(y=cfg.DARKNESS_THRESHOLD, color='black', linestyle='--')
    ax3.fill_between(data_frames, 0, cfg.DARKNESS_THRESHOLD, color='gray', alpha=0.2)
    ax3.set_ylabel("Lum")
    ax3.grid(True)

    filename_clean = os.path.splitext(os.path.basename(VIDEO_PATH))[0]
    graph_path = os.path.join(cfg.OUTPUT_DIR, f"{filename_clean}_analyse.png")
    plt.savefig(graph_path)
    plt.close()
    print(f"✅ Graphique : {graph_path}")
    try: os.startfile(graph_path)
    except: pass