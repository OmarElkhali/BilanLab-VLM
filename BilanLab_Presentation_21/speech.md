# Notes orales de soutenance BilanLab

## Slide 1: Extraction de bilans marocains avec un VLM

Bonjour. Nous présentons BilanLab, un projet qui transforme les tableaux d'un bilan marocain en données JSON vérifiables. Notre objectif est d'expliquer comment un modèle visuel peut lire les postes et les montants, puis comment le code contrôle ce qu'il a produit.

Le point central de ce travail est la fiabilité. Une réponse peut ressembler à du JSON tout en contenant un montant faux ou une colonne décalée. Nous allons donc suivre le document jusqu'à l'évaluation, puis présenter les résultats de l'API et du modèle local, y compris leurs échecs.

## Slide 2: Objectif métier et exigences du TP

Le besoin est de récupérer des données comptables sans recopier chaque montant à la main. Pour être utile, la sortie doit conserver la rubrique, le poste, la période et la valeur correcte. Le TP organise ce travail en quatre parties.

Nous commençons par comprendre et préparer le document. Nous construisons ensuite les requêtes API et comparons les techniques de prompt. Le chemin local est un bonus que nous avons réellement exécuté avec Ollama. Enfin, nous validons le JSON, vérifions les égalités comptables et mesurons les erreurs sur une référence.

Le notebook, les fichiers JSON et le compte-rendu permettent de retrouver ces étapes. L'application web sera présentée à la fin comme une extension, distincte du minimum demandé dans le TP.

## Slide 3: Le bilan étudié et ses colonnes

Voici les deux pages effectivement utilisées. À gauche, l'actif comporte le brut, les amortissements et provisions, le net de l'exercice et le net de l'exercice précédent. À droite, le passif présente les deux exercices sans colonnes brut et amortissements. Cette différence doit être conservée dans le schéma.

L'exercice se clôture le 31 décembre 2024. Une difficulté importante concerne l'unité : nous ne l'avons pas confirmée sur le document. Nous conservons donc les valeurs dans l'unité imprimée au lieu d'inventer une conversion en dirhams ou en milliers de dirhams.

Nous disposons d'un seul bilan réel. Ses variantes techniques ne représentent pas d'autres entreprises. Toutes les conclusions expérimentales doivent rester dans ce périmètre.

## Slide 4: Les difficultés de lecture d'un bilan

Les erreurs possibles ne viennent pas seulement de la reconnaissance des chiffres. Un montant correctement lu mais placé dans N au lieu de N−1 reste une erreur. Un signe négatif oublié change aussi le sens de la donnée.

Les cases vides demandent une attention particulière. Une case vide ne signifie pas qu'un zéro est imprimé. Une colonne qui n'existe pas, comme le brut au passif, constitue encore un autre cas. Enfin, une cellule illisible ne doit pas être remplie par un calcul supposé logique.

Les sous-totaux créent un dernier piège. Si nous additionnons un sous-total et ses propres détails, nous comptons les mêmes montants deux fois. Le modèle de données et les contrôles vont répondre à chacune de ces difficultés.

## Slide 5: Architecture du pipeline et responsabilités du code

Nous lisons ce schéma de gauche à droite. `load_pdf` charge le document, puis `prepare_images` produit des images lisibles et masquées. Les clients REST transmettent ensuite les images à Gemini ou au moteur local Ollama. Le code reçoit du texte et doit vérifier qu'il constitue un objet acceptable.

`strict_json` contrôle le parsing, `validate_page` applique le contrat et les règles métier, `arithmetic_checks` teste les égalités et `evaluate` compare les prédictions à la référence. Chaque fonction a donc une responsabilité précise.

La séparation du bas est essentielle. Le catalogue fournit des identifiants et des libellés, sans montants annotés. La référence contient les valeurs attendues et intervient uniquement dans l'évaluation. Nous n'utilisons pas ces valeurs pour compléter une réponse manquante du modèle.

## Slide 6: Prétraitement et anonymisation réelle

Nous rendons les pages avec PyMuPDF à 200 DPI pour conserver une lecture suffisamment fine des tableaux. Nous appliquons ensuite des masques aux pixels des zones d'identité et sauvegardons de nouvelles images PNG.

Cette étape répond à un problème concret du PDF fourni : des informations cachées visuellement restaient présentes dans sa couche texte. Envoyer directement ce PDF aurait donc transmis davantage que l'image visible. Le chemin API utilise uniquement les PNG préparés, après inspection.

Le code propose aussi un renforcement de contraste, mais cette option n'était pas activée dans l'expérience principale. Nous distinguons les possibilités du code des traitements réellement utilisés. La dégradation synthétique que nous avons effectivement testée sera présentée plus loin.

## Slide 7: Le schéma JSON minimal demandé par le TP

Cette première version respecte directement les quatre champs demandés : poste, rubrique, montant net N et montant net N−1. L'exemple des créances clients montre comment les valeurs deviennent accessibles à un programme, avec des chaînes décimales canoniques.

Nous avons réellement demandé cette sortie au VLM sans catalogue. Le fichier obtenu contient 49 lignes à l'actif et 41 au passif. Ce sont des lignes de transcription visibles, avant normalisation comptable.

Ce schéma est simple à exploiter, mais il a une limite : `null` ne permet pas à lui seul de savoir si une case est vide ou illisible. Il manque aussi les informations de parenté pour calculer les sous-totaux. C'est pourquoi nous proposons ensuite un schéma enrichi, en expliquant ce que chaque ajout apporte.

## Slide 8: Le schéma enrichi et les 88 postes canoniques

Nous ajoutons un identifiant stable et un parent pour chaque poste. Le type de ligne indique s'il s'agit d'un détail, d'un sous-total ou d'un total. Les montants bruts et les amortissements permettent de vérifier le net. Un état de lecture accompagne chaque cellule.

La figure décrit ces états dans la référence. Les cellules lues contiennent un montant. Les cellules vides, illisibles et non applicables restent distinguées, sans imputation automatique. Le calcul exact utilise des valeurs décimales, pas des arrondis flottants.

Le passage de 90 lignes imprimées à 88 postes canoniques vient des couples Trésorerie et Total III répétés sur chaque page. Nous représentons chaque masse une seule fois par A_III ou P_III. La référence évalue ainsi 107 montants, dont 74 nets, et 352 états/valeurs. Ce choix de normalisation doit être expliqué avant d'interpréter la complétude.

## Slide 9: Les six techniques de prompting

Nous comparons d'abord une consigne simple, puis un rôle système spécialisé en transcription comptable. Nous ajoutons les contraintes de lecture, notamment les colonnes, signes et états. L'étape suivante apporte un exemple fictif, séparé du bilan évalué.

Les deux dernières variantes utilisent des paramètres natifs du fournisseur. Le mode JSON demande une réponse de ce type. Le schéma contraint précise en plus la structure attendue pendant la génération. Dans tous les cas, notre validateur reste nécessaire après réception.

Cette expérience est cumulative : les variantes enrichissent progressivement une même base. Nous pouvons décrire les résultats des configurations testées, mais pas attribuer un effet causal indépendant à chaque élément. Nous ne présentons pas non plus les montants annotés dans les prompts.

Source technique : https://ai.google.dev/gemini-api/docs/structured-output

## Slide 10: Les deux chemins d'inférence

Le chemin API utilise Gemini 3.1 Flash-Lite par une requête REST. Nous transmettons les PNG et enregistrons la réponse, sa terminaison, sa durée et les compteurs de tokens retournés.

Le chemin local utilise Ollama avec Qwen3-VL 4B Instruct quantifié en Q4_K_M. Sur cette machine, l'exécution est CPU : le diagnostic indique zéro mémoire vidéo utilisée. Nous limitons aussi le côté maximal des images locales à 1400 pixels. Cette comparaison oppose donc deux solutions complètes, avec des modèles et résolutions différents, et non le seul lieu de déploiement.

Le modèle choisi est dense. Pour un modèle MoE, il faudrait considérer les poids de tous les experts à héberger ainsi que les caches et l'encodeur visuel, pas seulement les paramètres activés à chaque token. Nous n'avons pas exécuté cette configuration MoE.

Sources : outputs_vlm/ollama_snapshot_campagne.json ; https://docs.ollama.com/capabilities/structured-outputs ; https://github.com/QwenLM/Qwen3-VL

## Slide 11: Validation du JSON et contrôles comptables

Nous commençons par un parsing strict : les clôtures Markdown, clés dupliquées et sorties interrompues ne deviennent pas silencieusement des réussites. Nous vérifions ensuite le schéma, la couverture des postes, les années et la cohérence entre les valeurs et les états.

Les contrôles comptables portent sur les enfants directs des sous-totaux, sur brut moins amortissements égal au net, et sur l'égalité actif/passif dans les deux exercices. Les calculs utilisent Decimal. La tolérance d'un centime concerne uniquement les sommes ; l'évaluation d'exactitude demande une égalité stricte avec la référence.

La partie grise de la figure indique des contrôles sans données numériques, pas des écarts. Le notebook montre aussi un contre-exemple technique : déplacer une valeur entre deux postes peut préserver les totaux tout en rendant la transcription fausse. L'équilibre reste donc un signal de cohérence, pas une preuve de fidélité.

## Slide 12: Protocole de la nouvelle campagne

La nouvelle campagne comporte six variantes et trois répétitions, soit 18 expériences de prompting. Nous conservons le même document, les mêmes images et le même modèle avec une température de zéro. L'ordre est mélangé avec une graine fixée à 42 pour ne pas toujours passer les méthodes dans la même succession.

Le benchmark n'utilise pas de réessai de validation. Une panne réseau ou une page rejetée reste au dénominateur. Les journaux permettent de distinguer ces causes au lieu d'attribuer toute baisse de score au raisonnement du modèle.

Trois répétitions décrivent une variabilité de session ; elles ne remplacent pas un corpus indépendant. Le local CPU et la série API se sont aussi chevauchés. Nous conservons ce contexte plutôt que de présenter une mesure de laboratoire parfaitement isolée.

## Slide 13: Résultat API de livraison

Le résultat de livraison retrouve les 107 montants évalués, les 74 nets et les 88 postes canoniques. Les 66 contrôles numériques exploitables sont conformes, sans écart ni indétermination dans cet essai. Le traitement des deux pages a pris 31,69 secondes.

La provenance est importante : il s'agit de l'expérience `principal_relecture`, réalisée après un incident de connexion sur le premier essai principal. Nous avons conservé cet échec initial et séparé la nouvelle extraction du benchmark de prompting. Le résultat de livraison ne remplace donc pas rétroactivement une tentative échouée dans les statistiques.

Ces chiffres établissent la réussite sur le bilan fourni et sa référence de travail. Ils ne garantissent pas une exactitude identique pour tous les bilans marocains. Nous pouvons maintenant regarder ce que le JSON permet de restituer concrètement.

## Slide 14: Le bilan extrait devient lisible et exploitable

La figure provient des montants extraits et présente uniquement les grandes masses exclusives. À gauche, l'actif distingue l'immobilisé, l'actif circulant hors trésorerie et la trésorerie. À droite, le passif présente le financement permanent, le passif circulant et la trésorerie passive.

Les deux couleurs permettent de comparer les exercices. Le total actif et passif est de 20 702 296,47 pour N, contre 21 253 217,96 pour N−1. Ces valeurs restent dans l'unité imprimée, qui n'a pas été confirmée.

L'intérêt est de montrer qu'un JSON bien structuré peut alimenter des tableaux et graphiques sans nouvelle saisie. Nous évitons de sommer détails et sous-totaux ensemble. Cette visualisation démontre l'exploitation des données extraites, sans proposer une décision d'investissement à partir de ce seul document.

## Slide 15: Fiabilité comparée des techniques de prompt

À gauche, chaque case indique le nombre de montants exacts acceptés sur 107. Les lignes représentent les méthodes et les colonnes les répétitions. Le rôle, les contraintes, le few-shot et le schéma atteignent 107 sur les trois essais de cette campagne.

La baseline reste à zéro dans le pipeline strict, notamment parce que ses réponses comportent un format rejeté. Cela ne prouve pas qu'elle n'a reconnu aucun chiffre. Le mode JSON obtient 65 au premier essai, puis 107 et 107 : une page a été perdue sur incident réseau lors de la première répétition.

À droite, nous distinguons le parsing, le schéma et l'acceptation. Mon interprétation est que le rôle et un contrat explicite rendent l'extraction plus exploitable sur ce cas. Le plafond atteint par plusieurs variantes empêche de démontrer un gain supplémentaire universel du few-shot ou du schéma. Tous ces résultats restent liés à un seul bilan.

## Slide 16: Vitesse, variabilité et coût estimable

Nous regardons les points individuels avant les moyennes. Chaque durée correspond à une tentative réelle, et les médianes résument trois répétitions. Les variations du rôle ou de la baseline montrent pourquoi une seule mesure pouvait donner une impression trompeuse.

La latence inclut le transport et le traitement de la requête ; une panne consomme aussi du temps. Nous ne concluons donc pas qu'une technique est toujours plus rapide à partir de trois essais sur le même document. La comparaison API/local dépend aussi des modèles, de la résolution et du matériel.

Pour le coût API, le notebook applique aux compteurs connus le tarif standard de 0,25 USD par million de tokens d'entrée et 1,50 USD en sortie, raisonnement compris, documenté pour Gemini 3.1 Flash-Lite. L'extraction de livraison compte 5 935 tokens d'entrée et 3 359 de sortie, soit environ 0,00652 USD à ce tarif. Une requête sans compteurs conserve un coût inconnu. C'est une estimation, pas la facture du compte. Le coût électrique et matériel local n'a pas été mesuré.

Source tarifaire : https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite

## Slide 17: Une solution locale rapide : OCR et relecture ciblée

Nous avons conservé l'ancien essai : Qwen seul, sur page entière, prend 864,54 secondes et échoue à la validation stricte, malgré 34 montants bruts corrects. Des recadrages de quatre lignes réduisent le temps, mais le modèle remplit encore des cases vides. Cela montre pourquoi accélérer uniquement la génération ne suffit pas.

La nouvelle méthode lit les pixels avec RapidOCR sur CPU. Les coordonnées associent chaque nombre à un libellé du catalogue et à une colonne. Le catalogue ne fournit aucun montant. Les cases sans détection restent vides ; les colonnes absentes du passif sont explicitement non applicables. Qwen reçoit ensuite un recadrage des quatre cellules de plus faible confiance et leurs propositions OCR. Si les deux lectures divergent, nous déclarons la cellule illisible plutôt que de choisir en fonction de la référence.

Les trois extractions hybrides retrouvent chacune 107 montants sur 107, 352 états et valeurs sur 352, et 66 contrôles cohérents. Leurs durées sont 18,09, 16,04 et 15,81 secondes, soit une médiane de 16,04 secondes. Le graphique montre aussi que l'OCR seul est déjà exact sur ce bilan, en 8,40 secondes. Nous n'avons donc pas démontré un gain causal de précision apporté par Qwen : sa relecture est assistée et corrélée aux propositions OCR.

Mon choix sur ce PC est de privilégier cette lecture locale légère, avec Qwen en relecture ciblée si nécessaire. Il s'agit d'une amélioration du pipeline, sans entraînement du VLM. Qwen était déjà chargé pendant ces essais ; les colonnes sont adaptées au modèle normal fourni et nous n'avons toujours qu'un seul bilan. La comparaison des temps reste descriptive.

Sources techniques : https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/ ; https://docs.ollama.com/capabilities/structured-outputs

## Slide 18: Robustesse, relecture et traitement par lot

Les deux images comparent la même zone avant et après une dégradation synthétique. Nous avons réduit la résolution intermédiaire, ajouté du flou et abaissé le contraste. L'API retrouve encore les 107 montants dans cet essai, en 65,88 secondes. Cela constitue une preuve de robustesse à cette transformation précise.

Nous avons aussi corrigé une erreur du mécanisme de relecture : il ignorait auparavant les pages entièrement rejetées, puisqu'elles étaient absentes de la liste acceptée. Il parcourt maintenant les images d'origine et peut proposer une nouvelle lecture. Les propositions restent séparées du résultat initial et du benchmark.

Enfin, le lot technique a traité deux fichiers, l'original et un PDF de scan dérivé. C'est une file de deux entrées réussies, mais un seul bilan distinct. Une validation multi-entreprises exige encore d'autres documents réels.

## Slide 19: Confidentialité et choix de déploiement

Pour un cabinet, le choix ne dépend pas uniquement de la vitesse. Il faut déterminer les données transmises et les conditions de traitement. Le défaut de masque du PDF montre pourquoi nous devons contrôler le contenu réel, y compris les couches invisibles.

Avec une API distante, nous réduisons les données envoyées et examinons les conditions du fournisseur, la conservation et les formalités applicables. La loi 09-08 concerne les données à caractère personnel. La confidentialité commerciale doit également être prise en compte. La CNDP décrit les démarches de transfert et rappelle l'articulation avec le traitement sous-jacent.

Le local limite les transmissions, mais demande des accès maîtrisés, une gestion des secrets et une politique de conservation. Sur ce PC, la nouvelle extraction OCR locale donne un résultat exact sur le document fourni ; Qwen peut relire les cellules incertaines. Cette solution permet de conserver les images sur la machine, après installation préalable des poids. L'API reste une autre solution validée sur ce cas quand son usage est autorisé. Ni la réussite sur un bilan ni le choix du local ne constituent une certification juridique.

Sources officielles : https://www.cndp.ma/transfert-de-donnees-a-letranger/ ; https://www.cndp.ma/wp-content/uploads/2023/11/Loi-09-08-Fr.pdf

## Slide 20: BilanLab, l'application web du projet

L'application rend le pipeline accessible sans parcourir le code. L'utilisateur dépose un bilan, inspecte les pages et masque les zones sensibles avant de choisir les méthodes. Il voit ensuite les durées, les tableaux, le JSON, les contrôles et les réponses brutes, avec un export des résultats.

La capture montre une exécution réelle de l'exemple reconnu. Sur un autre document sans référence annotée, l'application affiche les contrôles mais n'invente pas un pourcentage d'exactitude. Les rubriques de présentation expliquent aussi l'architecture et les limites.

Cette application est une extension du TP. Son moteur TypeScript, ses images préparées dans le navigateur et son contrat diffèrent du pipeline Python. Son chrono ne doit donc pas être substitué aux mesures du notebook. L'objectif est de démontrer l'usage du projet, tout en conservant cette distinction expérimentale.

## Slide 21: Conclusion, limites et suite du projet

La contribution du projet est une chaîne vérifiable : lecture visuelle, représentation explicite, contrôles indépendants et évaluation exacte. Sur le bilan fourni, l'API produit une extraction validée. Après analyse de l'échec de Qwen seul, une méthode hybride OCR et relecture ciblée atteint aussi 107 montants exacts sur 107, avec une médiane de 16,04 secondes sur trois essais.

L'OCR seul était déjà exact sur cet exemple : nous évitons d'attribuer à Qwen un bénéfice non démontré. Le résultat négatif initial reste consultable. La prochaine étape la plus utile est d'élargir le corpus à des entreprises indépendantes, de varier les mises en page et de faire relire la référence par deux annotateurs. Il reste aussi à mesurer la mémoire et le coût énergétique réels.

Mon point de vue est qu'un résultat crédible doit être accompagné de son périmètre et de ses erreurs, pas uniquement d'un pourcentage. Les limites sont explicites : un seul bilan, une référence utilisée en développement et des coordonnées de colonnes adaptées au document. Merci, nous pouvons maintenant discuter de ces choix et des questions du TP.
