# Extraction de bilans marocains avec un VLM

## Version révisée du 15 novembre 2026

Le notebook distingue la version minimale à quatre champs demandée par le TP et les améliorations du pipeline. Une nouvelle campagne relance six stratégies de prompting avec trois répétitions, Qwen local, un scan dégradé et un lot technique. Les nouvelles inférences sont identifiées dans `outputs_vlm/campagne_courante.json` ; les échecs historiques restent archivés. Le notebook contient les tableaux complets, graphiques, journaux et réponses brutes, avec les limites du corpus.

Pour l'environnement isolé Windows : `py -3.12 -m venv .venv`, puis `.venv\Scripts\python -m pip install -r requirements-lock.txt`. Le fichier verrouillé enregistre les versions de la nouvelle exécution. Pour relire sans Python, ouvrir l'export HTML du même nom. Le notebook reste le livrable principal.

## Application web

Lancer `demarrer_application.cmd`, puis ouvrir **http://127.0.0.1:5173**. Dans Configuration, saisir sa clé Gemini de session. Les six méthodes API et Qwen via Ollama local affichent leurs durées réelles, le JSON et les contrôles. Voir `webapp/README.md`.

Le projet transforme les deux pages du bilan fourni en JSON, vérifie leur structure et leurs égalités comptables, puis mesure la fidélité à une référence annotée. Le notebook explique les choix, les difficultés rencontrées et les huit questions du TP.

## Ouvrir les résultats

Extraire l’archive complète du projet, puis ouvrir `TP_Extraction_Bilans_VLM_Groupe9.ipynb`. Le dossier `outputs_vlm` est nécessaire pour recalculer les mesures depuis les archives ; le notebook seul conserve les sorties visibles mais ne contient pas toutes les réponses brutes. Les résultats sauvegardés sont visibles sans clé API. Le mode de remise relit les expériences présentes dans `outputs_vlm/runs` ; les interrupteurs de nouvelle inférence sont désactivés. Le notebook contient aussi le PDF original compressé pour le restaurer si nécessaire dans Colab ou VS Code.

Le début du notebook contient une synthèse visuelle : indicateurs, comparaison API/local, graphiques de prompting, tableaux du bilan, erreurs et tests de robustesse. Les volets dépliables donnent accès aux 88 postes et au JSON complet. Cette synthèse utilise les résultats enregistrés et ne relance pas les modèles.

Les résultats de synthèse se trouvent dans :

- `outputs_vlm/compte_rendu.md` : compte-rendu et limites ;
- `outputs_vlm/resultats_finaux.json` : numérateurs, dénominateurs, contrôles et latences ;
- `outputs_vlm/comparaison_finale.csv` : série de comparaison retenue ;
- `outputs_vlm/comparaison.csv` : toutes les expériences, y compris les échecs de développement ;
- `outputs_vlm/batch_manifest.json` : traitement du PDF original et d'un scan synthétique dérivé ;
- `outputs_vlm/runs/*/bilan.json` : un résultat par document et expérience ;
- les journaux, réponses brutes, contrôles et CSV d'erreurs de chaque expérience.

Les cellules numériques de référence sont évaluées en incluant les pages rejetées au dénominateur. Un taux nul à la baseline peut être causé par un JSON entouré de Markdown : il mesure l'échec du pipeline strict, pas nécessairement une incapacité à lire les chiffres.

## Reproduire

Utiliser Python 3.12 ou un runtime Colab récent et les dépendances de `requirements.txt`. Exécuter les cellules dans l'ordre. Sans activation des interrupteurs, la relecture des archives ne déclenche aucune inférence.

Avec l'interpréteur Python de l'environnement choisi :

```text
python -m pip install -r requirements.txt
python scripts/executer_notebook.py
python scripts/verifier_livrables.py
```

Le dernier script contrôle les livrables et reconstruit l'archive de remise. Les poids des modèles ne sont pas inclus dans cette archive ; Ollama les gère séparément, et leurs identifiants sont enregistrés dans `outputs_vlm/ollama_snapshot.json`.

Pour refaire les appels Gemini, configurer `GEMINI_API_KEY` dans l'environnement ou utiliser la saisie masquée prévue dans le notebook. Ne pas écrire la clé dans le fichier. Le modèle réellement évalué est `gemini-3.1-flash-lite`. Relire les images masquées avant de mettre `API_IMAGES_REVIEWED = True`, puis activer `RUN_API`. Les ablations, la dégradation, la relecture et le lot ont des interrupteurs séparés.

Pour une nouvelle inférence Qwen seul, démarrer Ollama sur la même machine que le kernel, installer `qwen3-vl:4b-instruct` avec `ollama pull qwen3-vl:4b-instruct`, puis activer `RUN_LOCAL`. Cet essai historique échoue à la validation métier en 864,54 s. Il reste conservé pour comparaison.

### Nouvelle solution locale CPU, mesurée

L'extension `scripts/local_hybride.py` utilise RapidOCR sur les PNG masqués, l'alignement géométrique des cellules et une relecture Qwen des quatre cellules de plus faible confiance OCR. Trois essais donnent chacun **107/107 montants**, **352/352 états et valeurs** et **66 contrôles cohérents**, en **18,09 / 16,04 / 15,81 s**, soit **16,04 s de médiane**. L'OCR seul obtient déjà 107/107 en **8,40 s**. Le gain vient de cette nouvelle méthode ; aucun gain de précision propre à Qwen ni entraînement n'est démontré. Qwen reçoit les propositions OCR, jamais les montants de référence.

```text
python -m pip install -r requirements-local.txt
python scripts/local_hybride.py --repeats 3
```

Les résultats, les tableaux complets et le graphe comparatif sont dans la dernière section du notebook. `outputs_vlm/optimisation_locale/synthese.json` conserve les mesures. La méthode est disponible dans le notebook et en CLI ; le bouton Qwen du site conserve le moteur VLM seul. Les temps ne sont pas un benchmark à froid apparié : Qwen était déjà chargé. Un seul bilan a servi au développement et les colonnes sont adaptées à son modèle normal. Tester d'autres documents reste nécessaire.

## Présentation et collaboration

La soutenance de **21 diapositives** est dans `BilanLab_Presentation_21/BilanLab_Presentation_21.pptx`, avec notes orales intégrées et sources dans `speech.md`. Les diapositives sont des images complètes, produites avec image_gen ; les textes et graphes ne sont pas des objets séparés modifiables.

Le dépôt GitHub est privé. Collaborateurs demandés : **Jamila-Ouzzane** et **AyoubMoutik** ; une invitation doit être acceptée par son destinataire avant que l'accès soit effectif.

L'exécution pilotée de cette remise est locale sous Windows ; elle ne constitue pas une validation d'un runtime Colab ni d'un GPU. Dans Colab, `127.0.0.1` désigne Colab et ne donne pas accès à Ollama sur le PC.

## Périmètre et limites

Un seul bilan réel est fourni. Les deux entrées du lot technique représentent ce même bilan sous deux formes ; elles ne constituent pas deux entreprises indépendantes. Le même document a servi aux ajustements et à l'évaluation, sans double annotation indépendante. Les scores ne démontrent donc pas une généralisation à d'autres bilans.

L'unité monétaire n'étant pas explicitement confirmée dans le document, les valeurs restent dans l'unité imprimée. Aucun montant n'est converti arbitrairement en MAD. Le coût API utilise une estimation au tarif standard publié ; la facture réelle et le coût matériel/électrique local ne sont pas mesurés.

Le notebook contient le PDF original, dont des informations masquées visuellement restent dans la couche texte. La compression et base64 ne constituent pas une anonymisation. Seuls les PNG neufs et masqués sont transmis au VLM distant. Le dépôt reste privé et son accès est réservé aux collaborateurs autorisés.
