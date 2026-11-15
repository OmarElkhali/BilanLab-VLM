# Présentation de soutenance BilanLab

Cette présentation en français compte exactement 21 diapositives, couverture et conclusion comprises. Elle explique le besoin, le bilan, les responsabilités du code, les contrats JSON, les modèles, la validation, les expériences, les résultats et les limites. La dernière partie présente aussi l'application web comme une extension du TP.

## Présenter le projet

Ouvrir `BilanLab_Presentation_21.pptx` dans PowerPoint et activer le mode présentateur pour consulter les notes orales. Le fichier `speech.md` contient le même texte, page par page, avec les liens de référence utiles.

Le discours prévu dure environ 18 à 22 minutes, selon le rythme et les commentaires sur les graphiques. Les pages 13, 15 et 17 portent les principaux résultats. La page 16 explique la variabilité des durées et les coûts estimables. La page 21 formule la recommandation et les limites.

Chaque diapositive est une image complète, produite avec l'outil image_gen intégré conformément au skill codex-ppt. Les titres, chiffres et graphiques ne sont donc pas éditables comme des objets séparés. Les notes restent du texte dans le PowerPoint et dans `speech.md`.

## Fichiers

- `BilanLab_Presentation_21.pptx` : présentation de 21 pages avec notes intégrées.
- `origin_image/slide_01.png` à `slide_21.png` : images finales.
- `outline.md` : plan et affectation des figures approuvés.
- `speech.md` : explications orales et sources.
- `deck_spec.json` et `prompts/` : contrats de génération.
- `slide_jobs.json` et `slide_run_state.json` : provenance et état enregistrés par les scripts du skill.
- `verification_presentation.json` : contrôles structurels et limites de vérification.

## Interprétation des résultats

L'extraction API de livraison retrouve 107/107 montants, avec 66 contrôles conformes et une durée de 31,69 s. Elle est distincte du premier incident de connexion et du benchmark de 18 essais. L'ancien Qwen seul reste négatif : 34/107 montants bruts corrects, mais aucune page acceptée. La nouvelle méthode OCR CPU + relecture ciblée par Qwen obtient 107/107, 352/352 états et valeurs et 66 contrôles sur trois essais, avec une médiane de 16,04 s. L'OCR seul était déjà exact en 8,40 s : ce n'est pas un gain de précision démontré de Qwen seul. Les pages 17, 19 et 21 et leurs notes ont été révisées après ces mesures. Le scan synthétique et le lot ne constituent pas des entreprises supplémentaires.

Les chiffres décrivent un seul bilan utilisé aussi pendant le développement, avec une référence de travail sans double annotation indépendante. Aucune généralisation à tous les bilans ni validation juridique n'est revendiquée. Les mesures web ne remplacent pas les mesures Python.
