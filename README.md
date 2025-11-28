# - FallCall - Projet détection de chutes depuis le lit 

## Cadre du projet

### Objectif simplifié
Créer un système simple qui analyse la vidéo d'une caméra USB pour détecter quand une personne âgée tombe de son lit la nuit, et envoyer une alerte à une application pour le personnel soignant.

### Ce qu'on fait vraiment
- Analyser une vidéo en direct d'une chambre
- Repérer seulement les chutes qui arrivent quand la personne se lève du lit
- Envoyer une notification sur une appli quand une chute est détectée
- Éviter de déclencher des fausses alertes quand la personne se lève normalement

### Limites
- On ne détecte que les chutes près du lit (2-3 mètres max)
- On utilise juste une caméra USB standard
- Le système aide les soignants, mais ne les remplace pas

## Jeu de données

### Données existantes qu'on peut utiliser
On va commencer avec des vidéos publiques de chutes qu'on trouve en ligne, notamment :
- **FallVision** : contient des vidéos de chutes depuis un lit
- **SisFall** : données de capteurs de mouvement

### Nos propres enregistrements
Pour rendre le système plus fiable, on va filmer :
- **10-15 chutes simulées** : avec des volontaires (amis/famille)
- **20-30 levers normaux** : comment une personne se lève sans tomber
- **Quelques heures de vidéo** : plutôt que des centaines

## Validation simple

### Tests de base
1. **Test avec nos vidéos simulées** : Vérifier si le système détecte bien les chutes qu'on a filmées
2. **Test avec des levers normaux** : S'assurer qu'il ne déclenche pas d'alerte quand tout va bien
3. **Test dans différentes conditions** :
   - Avec les lumières éteintes
   - Avec différents types de lits
   - Avec plusieurs personnes

### Ce qu'on mesure
- **Détection des vraies chutes** : Au moins 9 sur 10
- **Fausses alertes** : Pas plus de 1 sur 20 levers normaux
- **Temps de réponse** : Alerte en moins de 30 secondes

### Tests pratiques
- Faire fonctionner le système plusieurs nuits de suite
- Tester avec l'application d'alerte réelle
- Vérifier que tout marche même si la caméra bouge un peu

L'idée est de garder les choses simples et efficaces, en se concentrant sur ce qui marche vraiment pour détecter les chutes depuis le lit.
