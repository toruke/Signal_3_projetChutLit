# Signal_3_projetChutLit

# Cadre du projet 
## Objectif principal
Développer un systeme automatisé capable de détecter en temps réel les chutes d'une personne depuis sont lit, avec alert rapide pour les soignants ou personnes consernées par la personne , afin de réduire le temps d'intervention et minimiser les conséquences physiques et ou psychologiques.

## Personnes cibler
Personnes agées en institution (EHPAD, maisons de retraite) ou à domicile, particulièrement celles souffrant de troubles cognitifs (démence) ou de problèmes de mobilité.

## Limites du système
Le système se concentrera exclusivement sur la détection de chutes liées au lit (sortie de lit et chute au sol), et non sur toutes les chutes dans l'invironnement domestique. La détection couvrira une zone définie autour du lit (environ 2-3 mètres). Le système ne remplace pas la surveillance humaine mais sert d'outil d'alerte complémentaire.

## Contraintes pour l'utilisateur
Le système doit être non intrusif et respectueux de la vie privée. 

----
# Constitution du jeu de données

#### liens pour la detections des chutes
* https://www.sciencedirect.com/science/article/pii/S2352340924008552
* https://www.frontiersin.org/journals/aging-neuroscience/articles/10.3389/fnagi.2021.692865/full
* https://www.sciencedirect.com/science/article/pii/S2352340925001726
## Datasets publics existants
**FallVision Dataset**: comprend des vidéos de chutes depuis un lit, une chaise et debout avec 17 points-clés du corps humain. **SisFall et KFall**: datasets incluant des chutes simulées et activités quotidiennes avec capteurs inertiels (accéléromètres, gyroscopes). **GMDCSA-24**: dataset vidéo avec chutes et activités non-chute (ADL).[](https://www.frontiersin.org/journals/aging-neuroscience/articles/10.3389/fnagi.2021.692865/full)

​

## Collecte de données personnalisées

Pour valider votre système dans votre contexte spécifique, vous devrez constituer votre propre dataset:[](https://pmc.ncbi.nlm.nih.gov/articles/PMC6068511/)

**Chutes simulées**: recruter des volontaires jeunes adultes (20-30 participants) pour simuler 15-20 types de chutes depuis le lit avec différents scénarios (chute latérale, en avant, en arrière). **Activités quotidiennes (ADL)**: enregistrer 16-20 activités normales comme se retourner dans le lit, s'asseoir au bord du lit, se lever normalement. **Durée**: minimum 100-200 heures d'enregistrement pour obtenir un dataset robuste.[](https://pmc.ncbi.nlm.nih.gov/articles/PMC4118339/)


-------
# Stratégie de validation
**Tests avec données personnel**: utiliser les données simulées pour évaluer la performance initiale avec validation croisée (leave-one-out ou k-fold)

**Tests multi-contextes**: tester avec différents types de lits, matelas, éclairages et configurations de chambre. **Tests multi-utilisateurs**: valider sur des personnes d'âges, tailles et conditions physiques variées. **Tests de durabilité**: évaluer la stabilité du système sur plusieurs semaines avec suivi des dégradations de performance. **Tests d'occlusion**: pour les systèmes visuels, tester avec obstacles, obscurité, etc.
