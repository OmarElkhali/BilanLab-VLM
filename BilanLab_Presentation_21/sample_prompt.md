# Prompt de la diapositive témoin 15

Outil confirmé : image_gen intégré. Générer une seule diapositive 16:9 en français, avec l'image `outputs_vlm/figures/01_exactitude_et_validation.png` comme entrée stricte de contenu. L'image a été inspectée avec view_image avant génération.

Créer une composition de soutenance claire sur fond blanc. Palette d'habillage : bleu nuit #142838, vert pétrole #137D72, gris ardoise #5C6F80, ambre discret pour l'incident réseau. Titres sans empattement, grands et lisibles. Une figure principale très grande, des annotations courtes et de l'espace. Pas de cartes façon tableau de bord, pas de faux logo, pas de numéro de page.

Image 1 est la preuve expérimentale stricte : intégrer la figure fournie, sans la redessiner ni changer une valeur, un axe, une légende, une couleur, un libellé ou un point. Conserver les deux panneaux et toutes les lignes de la matrice. Composer uniquement l'environnement de la figure.

Texte à afficher :

- Petit repère : RÉSULTATS EXPÉRIMENTAUX
- Titre : Fiabilité des techniques de prompt
- Sous-titre : 6 variantes, 3 répétitions, un seul bilan
- Annotation principale : 4 variantes : 107/107 à chaque répétition
- Annotation complémentaire : JSON mode : 65/107 au premier essai. Une page perdue sur incident réseau.
- Note de bas de page : Baseline rejetée par le format. Ces mesures portent sur un seul bilan utilisé aussi pendant le développement.

Hiérarchie de lecture : titre, grande figure, interprétation. Les quatre variantes du commentaire sont rôle, contraintes, exemple fictif et schéma contraint. Le défaut de JSON mode est un incident réseau et ne doit pas être décrit comme une preuve d'échec de lecture du prompt. Le résultat nul de la baseline décrit le pipeline strict, pas une absence de reconnaissance des chiffres.
