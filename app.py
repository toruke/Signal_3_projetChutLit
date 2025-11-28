from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

last_alert = None


@app.route("/")
def index():
    # Affiche la page principale FallCall
    return render_template("index.html")


@app.route("/api/alert", methods=["POST"])
def api_alert():
    """
    Reçoit une alerte depuis main.py :
    {
        "frame": ...,
        "time": ...,
        "source": "videos\\chute_1.mp4"
    }
    """
    global last_alert
    data = request.get_json()

    print("🆕 Nouvelle alerte reçue :", data)

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    last_alert = {
        "frame": data.get("frame"),
        "time": data.get("time"),
        "source": data.get("source"),
        "received_at": datetime.now().isoformat(timespec="seconds"),
    }

    return jsonify({"status": "alert_saved"}), 201


@app.route("/api/last-alert", methods=["GET"])
def api_last_alert():
    """
    Renvoie la dernière alerte connue, au format :
    {
      "alert": {...} ou null,
      "hasAlert": true/false
    }
    """
    if last_alert is None:
        return jsonify({"alert": None, "hasAlert": False}), 200
    return jsonify({"alert": last_alert, "hasAlert": True}), 200


if __name__ == "__main__":
    app.run(debug=True)
