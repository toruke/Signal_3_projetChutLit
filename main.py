import cv2
import os
import matplotlib.pyplot as plt
import requests
from playsound import playsound

VIDEO_PATH = os.path.join("videos", "chute_1.mp4")
DY_THRESHOLD = 30
DEBUG = False
DISPLAY_VIDEO = True
OUTPUT_DIR = "output"
ALERT_API_URL = "http://127.0.0.1:5000/api/alert"

BASE_DIR = os.path.dirname(__file__)
ALERT_MP3_PATH = os.path.join(BASE_DIR, "static", "alert.mp3")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Impossible d'ouvrir la vidéo :", VIDEO_PATH)
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30.0
print(f"FPS = {fps}")

display_delay = int(1000 / fps)
if display_delay < 1:
    display_delay = 1

prev_gray = None
y_centers = []
frame_indices = []
frame_idx = 0

fall_detected = False
fall_frame = None
fall_time_sec = None
max_dy = -999

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        _, motion_mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        moments = cv2.moments(motion_mask)

        if moments["m00"] != 0:
            x_center = int(moments["m10"] / moments["m00"])
            y_center = int(moments["m01"] / moments["m00"])

            y_centers.append(y_center)
            frame_indices.append(frame_idx)

            if len(y_centers) >= 2:
                dy = y_centers[-1] - y_centers[-2]

                if DEBUG:
                    print(f"Frame {frame_idx} : y={y_center}, dy={dy}")

                if dy > max_dy:
                    max_dy = dy
                    fall_frame = frame_idx

                if (not fall_detected) and dy > DY_THRESHOLD:
                    fall_detected = True
                    fall_time_sec = frame_idx / fps

                    print("🚨 CHUTE DETECTEE !")
                    print(f"Frame : {fall_frame}")
                    print(f"dy max : {dy:.2f}")
                    print(f"Temps : {fall_time_sec:.2f}s")

                    try:
                        playsound(ALERT_MP3_PATH, block=False)
                        print("🔊 alert.mp3 joué")
                    except Exception as e:
                        print("⚠️ Son impossible :", e)

                    try:
                        resp = requests.post(
                            ALERT_API_URL,
                            json={
                                "frame": fall_frame,
                                "time": fall_time_sec,
                                "source": VIDEO_PATH
                            },
                            timeout=2
                        )
                        print("Alerte envoyée :", resp.status_code)
                    except Exception as e:
                        print("⚠️ Envoi impossible :", e)

    prev_gray = gray.copy()
    frame_idx += 1

    if DISPLAY_VIDEO:
        cv2.imshow("FallCall", frame)
        key = cv2.waitKey(display_delay) & 0xFF
        if key == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()

os.makedirs(OUTPUT_DIR, exist_ok=True)

if len(y_centers) > 0:
    plt.figure()
    plt.plot(frame_indices, y_centers)
    plt.gca().invert_yaxis()
    plt.xlabel("Frame")
    plt.ylabel("y")
    plt.grid(True)
    graph_path = os.path.join(OUTPUT_DIR, "yc_gravite.png")
    plt.savefig(graph_path)
    plt.close()
    print("Graphe :", graph_path)

result_path = os.path.join(OUTPUT_DIR, "resultat_chute.txt")
with open(result_path, "w", encoding="utf-8") as f:
    if fall_detected and fall_frame is not None and fall_time_sec is not None:
        f.wr
