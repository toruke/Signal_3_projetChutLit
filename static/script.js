async function refreshStatus() {
  try {
    const response = await fetch('/api/last-alert');
    const data = await response.json();

    // data.hasAlert (booléen) + data.alert (objet ou null)
    const statusText = document.getElementById('status-text'); // l’élément qui affiche le texte
    const timeSpan   = document.getElementById('time-span');   // optionnel si tu as des spans
    const sourceSpan = document.getElementById('source-span');

    if (data.hasAlert && data.alert) {
      const alert = data.alert;

      statusText.textContent = "Chute détectée !";
      statusText.style.color = "#ff4d4d"; // rouge

      // Détails optionnels
      if (timeSpan) {
        timeSpan.textContent = alert.time.toFixed(2) + " s";
      }
      if (sourceSpan) {
        sourceSpan.textContent = alert.source || "source inconnue";
      }
    } else {
      statusText.textContent = "Aucune chute détectée.";
      statusText.style.color = "#4caf50"; // vert
      if (timeSpan) timeSpan.textContent = "";
      if (sourceSpan) sourceSpan.textContent = "";
    }
  } catch (err) {
    console.error("Erreur lors de l’appel /api/last-alert :", err);
  }
}

// Bouton "Rafraîchir maintenant"
const refreshBtn = document.getElementById('refresh-btn');
if (refreshBtn) {
  refreshBtn.addEventListener('click', refreshStatus);
}

// Rafraîchissement auto toutes les 5 secondes
setInterval(refreshStatus, 1000);
refreshStatus();
