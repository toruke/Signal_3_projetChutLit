import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import concurrent.futures
import time
import config as cfg 
# =========================================
#   FONCTIONS (Identique Main)
# =========================================

def apply_light_condition(gray, brightness):
    if brightness < cfg.DARKNESS_THRESHOLD:
        gray_proc = cv2.GaussianBlur(gray, cfg.NIGHT_BLUR, 0)
        clahe = cv2.createCLAHE(clipLimit=cfg.NIGHT_CLAHE, tileGridSize=(8, 8))
        gray_proc = clahe.apply(gray_proc)
        return (gray_proc, cfg.NIGHT_THRESHOLD, cfg.NIGHT_MIN_AREA, cfg.DY_NIGHT_THRESHOLD)
    else:
        gray_proc = cv2.GaussianBlur(gray, cfg.DAY_BLUR, 0)
        return (gray_proc, cfg.DAY_THRESHOLD, cfg.DAY_MIN_AREA, cfg.DY_DAY_THRESHOLD)

# =========================================
#   MOTEUR D'ANALYSE (Avec enregistrement Stats)
# =========================================

def analyze_video(video_filename):
    path = os.path.join(cfg.VIDEOS_DIR, video_filename)
    if not os.path.exists(path): return None 

    cap = cv2.VideoCapture(path)
    prev_gray = None
    
    y_history = deque(maxlen=cfg.ANALYSIS_STRIDE + 1)
    y_buffer_smooth = deque(maxlen=cfg.SMOOTHING_WINDOW)
    
    fall_counter = 0
    detected = False
    detected_frame = None

    # Data pour stats
    data_frames, data_dy, data_area, data_lum = [], [], [], []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        current_dy = 0
        area = 0
        
        if cfg.ROTATE_VIDEO:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        gray_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray_raw)
        
        (gray_active, threshold_pixel, min_area_mode, dy_threshold_mode) = apply_light_condition(gray_raw, avg_brightness)

        if prev_gray is not None:
            diff = cv2.absdiff(gray_active, prev_gray)
            _, motion_mask = cv2.threshold(diff, threshold_pixel, 255, cv2.THRESH_BINARY)
            kernel = np.ones((5, 5), np.uint8)
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
            moments = cv2.moments(motion_mask)
            area = moments["m00"]

            if area > min_area_mode:
                y_raw = int(moments["m01"] / moments["m00"])
                
                # Lissage
                y_buffer_smooth.append(y_raw)
                y_smooth = int(sum(y_buffer_smooth) / len(y_buffer_smooth))
                
                # Forme
                x, y, w, h = cv2.boundingRect(motion_mask)
                is_horizontal = w*1.2 >= h 

                y_history.append(y_smooth)

                if len(y_history) > cfg.ANALYSIS_STRIDE:
                    current_dy = y_history[-1] - y_history[0]
                    if abs(y_history[-1] - y_history[-2]) < 3: current_dy = 0

                    if (current_dy > dy_threshold_mode) and (current_dy < cfg.MAX_DY) and is_horizontal:
                        fall_counter += 1
                    else:
                        if fall_counter > 0: fall_counter -= 1

                    if fall_counter >= cfg.CONSECUTIVE_VALIDATIONS:
                        if not detected: 
                            detected = True
                            detected_frame = frame_idx
            else:
                if len(y_history) > 0: y_history.popleft() 
                y_buffer_smooth.clear()
                fall_counter = 0

        prev_gray = gray_active.copy()
        
        # Enregistrement Stats
        data_frames.append(frame_idx)
        data_dy.append(current_dy)
        data_area.append(area)
        data_lum.append(avg_brightness)
        
        frame_idx += 1

    cap.release()
    
    # --- GENERATION GRAPHIQUE SILENCIEUSE ---
    generate_stat_graph(video_filename, data_frames, data_dy, data_area, data_lum, detected_frame)
    
    return detected

def generate_stat_graph(filename, frames, dys, areas, lums, fall_frame):
    os.makedirs(cfg.STATS_DIR, exist_ok=True)
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    fig.suptitle(f"Analyse : {filename}")

    # DY
    ax1.plot(frames, dys, color='blue', label='dy')
    ax1.axhline(y=cfg.DY_DAY_THRESHOLD, color='green', linestyle='--', alpha=0.5, label='Seuil Jour')
    ax1.axhline(y=cfg.DY_NIGHT_THRESHOLD, color='orange', linestyle='--', alpha=0.5, label='Seuil Nuit')
    ax1.set_ylabel("Vitesse")
    if fall_frame:
        ax1.axvline(x=fall_frame, color='red', linewidth=2, label='Chute')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # AREA
    ax2.plot(frames, areas, color='purple', label='Area')
    ax2.axhline(y=cfg.DAY_MIN_AREA, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=cfg.NIGHT_MIN_AREA, color='orange', linestyle='--', alpha=0.5)
    ax2.set_ylabel("Pixels²")
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)

    # LUM
    ax3.plot(frames, lums, color='gold', label='Luminosité')
    ax3.axhline(y=cfg.DARKNESS_THRESHOLD, color='black', linestyle='--')
    ax3.fill_between(frames, 0, cfg.DARKNESS_THRESHOLD, color='gray', alpha=0.2)
    ax3.set_ylabel("Lum")
    ax3.set_xlabel("Frames")
    ax3.grid(True, alpha=0.3)

    clean_name = os.path.splitext(filename)[0]
    save_path = os.path.join(cfg.STATS_DIR, f"{clean_name}-stats.png")
    plt.savefig(save_path)
    plt.close()

# =========================================
#   LANCEMENT DU TEST
# =========================================

def process_video_task(item):
    filename, expected = item
    result = analyze_video(filename)
    return (filename, expected, result)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- SUITE DE TESTS + GENERATION STATS ---")
    
    # Nettoyage dossier stats
    if os.path.exists(cfg.STATS_DIR):
        for f in os.listdir(cfg.STATS_DIR):
            try:
                os.remove(os.path.join(cfg.STATS_DIR, f))
            except: pass
    
    success_count = 0
    # Correction ICI : Utilisation de TEST_CASES importé, pas cfg.TEST_CASES
    total_videos = len(cfg.TEST_CASES)
    
    start_time = time.time()  # <--- DÉBUT CHRONO

    with concurrent.futures.ProcessPoolExecutor() as executor:
        tasks = list(cfg.TEST_CASES.items())
        results = executor.map(process_video_task, tasks)

        for filename, expected, result in results:
            if result is None:
                print(f"⚠️  {filename.ljust(35)} : INTROUVABLE")
            elif result == expected:
                print(f"✅ {filename.ljust(35)} : OK")
                success_count += 1
            else:
                attendu = "CHUTE" if expected else "RIEN"
                recu = "CHUTE" if result else "RIEN"
                print(f"❌ {filename.ljust(35)} : ERREUR (Attendu: {attendu}, Reçu: {recu})")

    end_time = time.time()    # <--- FIN CHRONO
    duration = end_time - start_time

    score = (success_count / total_videos) * 100
    print("-" * 60)
    print(f"TEMPS TOTAL : {duration:.2f} secondes")
    print(f"SCORE FINAL : {score:.1f}% ({success_count}/{total_videos})")
    print(f"Les graphiques d'analyse sont dans : {cfg.STATS_DIR}")
    print("=" * 60)