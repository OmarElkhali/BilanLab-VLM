# Compte rendu du TP sur l’extraction de bilans avec un VLM

**ENSAM Casablanca — Module Transformers et LLMs**

**Groupe 9 : Omar Elkhali · Jamila Ouzzane · Ayoub Moutik**

**Date : 15 novembre 2026**

## Accès au notebook de présentation

[Ouvrir Presentation_Projet_BilanLab.ipynb sur GitHub](https://github.com/OmarElkhali/BilanLab-VLM/blob/main/Presentation_Projet_BilanLab.ipynb)

Adresse complète : https://github.com/OmarElkhali/BilanLab-VLM/blob/main/Presentation_Projet_BilanLab.ipynb

Le notebook contient 18 sections, 19 cellules de code, 14 visuels, 31 tableaux et les archives des 55 expériences. Sa lecture ne nécessite ni clé API ni Ollama.

## Objectif et synthèse

Nous avons extrait les postes d’un bilan marocain à partir de deux pages, puis vérifié le JSON, les montants, les états de cellules et les égalités comptables. Le fichier de l’énoncé est nommé TP5_Extraction_Bilans_VLM.docx ; son titre intérieur indique TP 3. Ce compte rendu répond aux huit questions de sa section 6.

La livraison API et une nouvelle méthode locale hybride retrouvent les 107 montants de référence. L’OCR local seul est déjà exact sur ce document. L’ancien résultat négatif de Qwen seul reste conservé : nous avons amélioré le pipeline, sans entraîner le modèle ni démontrer un gain de précision propre à Qwen.

| Méthode | Montants exacts acceptés | Durée document | Portée de la mesure |
|---|---|---|---|
| Gemini 3.1 Flash-Lite | 107/107 | 31,69 s | Livraison hors benchmark |
| Qwen seul sur CPU | 0/107 | 864,54 s | 34/107 corrects avant rejet |
| OCR local seul | 107/107 | 8,40 s | Un essai |
| OCR et relecture Qwen | 107/107 | 16,04 s | Médiane de trois essais |

Les résultats décrivent un seul bilan, utilisé aussi au développement. Les trois répétitions hybrides et le scan dégradé ne constituent pas des documents indépendants. Qwen était déjà chargé lors des nouveaux essais ; les durées ne forment pas un benchmark matériel apparié à froid.

<!-- pagebreak -->

## Question 1 Les pièges d’un bilan scanné

**Quels pièges présente un bilan scanné (qualité, tableaux, unités en milliers, postes vides) ?**

Un scan flou, peu contrasté, incliné ou trop réduit dégrade la lecture des chiffres, des virgules et des signes. Les tableaux à plusieurs colonnes peuvent provoquer des décalages entre postes, brut, amortissements et nets. Une confusion entre N et N−1 peut donner des montants plausibles mais faux. Les totaux et sous-totaux créent aussi un risque de double comptage.

Une case blanche ne signifie pas automatiquement zéro. Au passif, les colonnes brut et amortissements sont absentes : cet état doit être distingué d’une case vide ou illisible. Enfin, une unité en milliers changerait l’échelle des montants ; nous ne la déduisons jamais du seul ordre de grandeur.

Nous préparons des images à 200 DPI, conservons les signes et distinguons quatre états de cellule. L’unité du document n’étant pas confirmée, elle reste « inconnue » et aucune conversion en MAD n’est appliquée. Les seuls fichiers transmis au VLM distant sont des PNG neufs avec masquage dans les pixels : les masques visuels du PDF original ne supprimaient pas toutes les informations de sa couche texte.

## Question 2 Le schéma JSON et sa justification

**Quel schéma JSON avez-vous conçu pour représenter un bilan ? Justifiez vos champs.**

Nous avons d’abord exécuté le contrat minimal demandé, avec exactement les quatre champs suivants pour chaque ligne.

| Champ minimal | Rôle |
|---|---|
| poste | Conserver le libellé comptable |
| rubrique | Distinguer actif et passif |
| montant_net_N | Représenter le net de l’exercice courant |
| montant_net_N1 | Permettre la comparaison avec l’exercice précédent |

Les montants sont des chaînes décimales signées à deux décimales ; une case absente vaut null. Le JSON minimal contient 49 lignes d’actif et 41 de passif, soit les 90 lignes imprimées.

Le contrat enrichi ajoute id, parent_id, type_ligne, brut N, amortissements N et un état pour chaque colonne : lu, vide, illisible ou non_applicable. Il conserve aussi l’exercice, l’unité, les avertissements et la provenance. Ces champs permettent de détecter les doublons, contrôler les sommes et distinguer les causes d’absence d’un montant.

La version normalisée contient 88 postes, car Trésorerie et Total III décrivent le même agrégat imprimé deux fois sur chaque page. Leur fusion est explicite. Le catalogue fournit seulement identifiants, libellés et hiérarchie ; aucun montant de référence n’entre dans les prompts.

<!-- pagebreak -->

## Question 3 Les techniques de prompt et leurs résultats

**Quelles techniques de prompt ont amélioré la fiabilité (rôle, contraintes, few-shot, JSON mode) ?**

Nous avons comparé six variantes cumulatives sur les mêmes images, avec trois répétitions chacune : 18 essais. La température est fixée à zéro, l’ordre est mélangé avec une graine 42 et le benchmark ne comporte aucun réessai de validation. La livraison finale relue reste hors de ce benchmark.

| Variante | Apport principal | Montants exacts sur les trois essais |
|---|---|---|
| Baseline | Consigne simple | 0/107 ; 0/107 ; 0/107 |
| Rôle système | Transcription comptable explicite | 107/107 ; 107/107 ; 107/107 |
| Contraintes | États, colonnes, signes et absence de calcul inventé | 107/107 ; 107/107 ; 107/107 |
| Few-shot | Exemple fictif de structure | 107/107 ; 107/107 ; 107/107 |
| JSON mode | Sortie JSON imposée | 65/107 ; 107/107 ; 107/107 |
| Schéma contraint | Contrat structuré à la génération | 107/107 ; 107/107 ; 107/107 |

Le score nul de la baseline concerne le pipeline strict : des réponses entourées de Markdown sont rejetées. Il ne démontre pas l’absence totale de lecture des chiffres. Le résultat à 65/107 du mode JSON est lié à une page manquante lors d’un incident de connexion ; nous ne l’attribuons pas uniquement au prompt.

Sur ce bilan, le rôle système suffit déjà à obtenir le score maximal dans les trois répétitions. Les contraintes et le few-shot rendent les règles explicites, mais ces variantes cumulatives et ce corpus unique ne permettent pas d’isoler leur effet causal ni d’annoncer un gain universel.

## Question 4 La validité du JSON et le décodage contraint

**Comment garantir un JSON valide à 100 % : « demander gentiment » vs décodage contraint ?**

Une consigne seule ne contrôle pas la forme finale : le modèle peut ajouter des explications, des blocs Markdown ou omettre des champs. Le mode JSON contraint la syntaxe ; un schéma de génération précise aussi les types, propriétés obligatoires et valeurs autorisées. Gemini fournit des sorties structurées ; Ollama accepte un schéma dans le paramètre format. [1, 2]

Nous appliquons ensuite une validation indépendante : analyse JSON stricte, rejet des clés dupliquées et des constantes non JSON, validation jsonschema, couverture des postes, absence de doublons, cohérence des états et plausibilité de l’année. Une génération tronquée ou non conforme est rejetée et journalisée.

Nous garantissons ainsi la conformité des objets acceptés au contrat vérifié. Nous ne promettons pas que 100 % des requêtes aboutissent : erreurs réseau, refus et troncatures restent possibles. Un JSON syntaxiquement correct peut aussi contenir de faux montants ; les contrôles comptables et l’évaluation demeurent nécessaires.

<!-- pagebreak -->

## Question 5 Vérifier sans tout annoter

**Comment vérifier l’extraction SANS tout annoter (contrôle actif = passif, cohérence des totaux) ?**

Nous exploitons les relations comptables du document : somme des enfants directs égale au sous-total, somme des grandes rubriques égale au total général, brut moins amortissements égal au net à l’actif, et actif égal au passif pour chaque exercice. Les contrôles comparent des postes de même exercice et de même unité.

Le code utilise Decimal pour éviter les erreurs binaires de calcul. La tolérance comptable est de 0,01 dans l’unité imprimée. Les cases vides sont traitées comme null dans la donnée ; seules les sommes de contrôle les interprètent comme zéro. Une valeur illisible rend le contrôle indéterminé. Les lignes sans données ne sont pas comptées comme une preuve numérique réussie.

La livraison API et le résultat hybride obtiennent 66 contrôles numériques cohérents. Le total actif et le total passif valent chacun 20 702 296,47 en N, et 21 253 217,96 en N−1. Aucune prédiction n’est modifiée pour rendre ces égalités vraies. Deux erreurs compensées peuvent conserver un total correct : ces tests détectent des incohérences mais ne remplacent pas une référence indépendante.

## Question 6 Le local le matériel et la comparaison avec l’API

**(Local) Quel VLM/moteur ? Contraintes VRAM (piège MoE) ? Latence vs API ?**

Nous avons utilisé Ollama et qwen3-vl:4b-instruct, un modèle dense de 4 milliards de paramètres, quantifié Q4_K_M. Il a tourné sur CPU Ryzen 5 5600G, sans VRAM utilisée par Ollama. Il ne s’agit pas d’une exécution GPU/MoE ; FreeToken n’a pas été exécuté. Cette différence avec la configuration évoquée par l’énoncé constitue une limite du bonus local.

Pour un modèle MoE, le routage n’active qu’une partie des experts par token, mais ne signifie pas que seuls ces experts doivent être stockés. Dans une configuration entièrement en VRAM, il faut héberger tous les poids, puis ajouter le cache et les buffers. Une configuration avec déchargement vers RAM/CPU doit être distinguée et mesurée séparément.

Qwen seul a pris 864,54 s et produit une sortie rejetée. La livraison API prend 31,69 s. Nous avons ensuite ajouté une méthode locale légère : RapidOCR lit les cellules, le code les aligne par géométrie, puis Qwen relit les quatre cellules de plus faible confiance OCR avec leurs recadrages et propositions. Un désaccord devient illisible, sans correction par le gold.

Les trois essais hybrides prennent 18,09, 16,04 et 15,81 s, soit 16,04 s de médiane. L’OCR seul est déjà exact en 8,40 s ; aucun gain causal de précision de Qwen n’est démontré. Qwen était déjà chargé. Les temps comparent des pipelines et conditions différents, sans prouver une accélération générale du VLM seul.

<!-- pagebreak -->

## Question 7 Exactitude et types d’erreurs

**Taux d’exactitude sur votre échantillon ? Quels types d’erreurs dominent ?**

La référence comprend 88 postes, 107 montants numériques, dont 74 nets, et 352 états de cellules. L’égalité à la référence est exacte avec Decimal, sans la tolérance utilisée pour les contrôles comptables. Les pages rejetées restent au dénominateur afin de ne pas améliorer artificiellement le score.

| Indicateur | Livraison API | Hybride local sur chacun des trois essais |
|---|---|---|
| Montants numériques exacts | 107/107 | 107/107 |
| Nets N et N−1 exacts | 74/74 | 74/74 |
| Postes présents | 88/88 | 88/88 |
| États et valeurs exacts | 352/352 | 352/352 |
| Contrôles numériques cohérents | 66 | 66 |

Pour Qwen seul, le diagnostic brut retrouve seulement 34/107 montants, soit environ 31,8 %, avant rejet des pages. Les erreurs dominantes sont des NA dans des colonnes applicables (210 cas), des montants décalés entre lignes, des chiffres mal lus et une année 3112. La baseline souffre surtout d’un défaut de format accepté ; le réseau provoque aussi des pages manquantes.

Les scores parfaits portent sur un seul bilan également utilisé au développement, avec une référence sans double annotation indépendante. Ils ne démontrent donc pas une généralisation à d’autres entreprises ou mises en page.

## Question 8 Confidentialité et recommandation pour un cabinet marocain

**API vs local : que recommandez-vous pour un cabinet marocain soumis à la confidentialité (CNDP) ?**

Nous recommandons d’évaluer d’abord un traitement local lorsque la confidentialité l’exige et que la qualité a été validée sur les documents du cabinet. Sur notre PC et ce bilan, l’OCR local suffit déjà ; la relecture Qwen est une option à justifier par des essais plus difficiles. Les accès, journaux, sauvegardes, secrets et durées de conservation doivent rester maîtrisés.

Une API peut être retenue si le traitement et les transmissions sont autorisés, après minimisation des données et examen des conditions du fournisseur, des destinataires et de la conservation. Pour les données personnelles transférées à l’étranger, la CNDP précise des conditions et démarches ; l’autorisation de transfert s’articule avec le traitement sous-jacent déclaré ou autorisé. [3]

Notre recommandation technique ne vaut pas validation juridique. Le masquage doit supprimer réellement l’information transmise, pas seulement la recouvrir dans un PDF. Un dépôt privé ne transforme pas un document original en document anonymisé ; son accès doit rester limité aux personnes autorisées.

<!-- pagebreak -->

## Bilan des extensions et des livrables

Le test API sur scan synthétique dégradé retrouve 107/107 montants en 65,88 s. Le lot traite deux fichiers, l’original et un dérivé raster : il s’agit d’un test de traitement par lot sur une seule entreprise, pas d’un corpus multi-entreprises. La relecture parcourt aussi les pages entièrement rejetées ; ses propositions restent séparées du résultat initial.

L’application BilanLab permet d’importer, masquer, comparer et exporter. Son moteur TypeScript et ses images diffèrent du notebook Python : son chrono d’exemple de 16,05 s ne doit pas remplacer les temps Python. La méthode OCR et relecture Qwen est disponible dans le notebook technique et en ligne de commande ; le bouton Qwen du site conserve le VLM seul.

La livraison API consomme 5 935 tokens d’entrée et 3 359 de sortie. Au tarif standard documenté de 0,25 USD par million en entrée et 1,50 USD en sortie, l’estimation vaut 0,00652225 USD. Ce montant n’est pas une facture ; une requête sans compteur garde un coût inconnu, et le coût énergétique ou matériel local n’a pas été mesuré. [4]

| Livrable | Contenu |
|---|---|
| Presentation_Projet_BilanLab.ipynb | Présentation autonome, résultats complets et réponses brutes |
| TP_Extraction_Bilans_VLM_Groupe9.ipynb | Implémentation complète et expériences reproductibles |
| outputs_vlm | JSON extraits, mesures, contrôles et journaux |
| BilanLab_Presentation_21 | Soutenance PowerPoint et notes orales |
| webapp | Code de l’application et exemple raster masqué |

## Conclusion du groupe

Nous avons réalisé l’extraction API et la validation demandées, exécuté le bonus local sur le matériel disponible et documenté ses limites. L’analyse de l’échec de Qwen seul nous a conduits à une solution locale hybride plus adaptée au CPU, tout en montrant que l’OCR seul était déjà suffisant ici. Nous conservons les essais négatifs et distinguons les mesures des perspectives.

La suite prioritaire est de constituer un corpus indépendant de bilans et de mises en page variées, faire doublement annoter la référence et mesurer mémoire, énergie et erreurs sur des documents inconnus. Aucun entraînement, test GPU/MoE, validation indépendante multi-entreprises ou certification CNDP n’est revendiqué.

## Références

- Énoncé local : TP5_Extraction_Bilans_VLM.docx, section 6 ; bilan_group_9.pdf, clôture au 31/12/2024. Mesures et archives du projet du 15 novembre 2026.
- [1] [Gemini Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output), documentation officielle consultée le 15 novembre 2026.
- [2] [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs), documentation officielle consultée le 15 novembre 2026.
- [3] [CNDP Transfert de données à l’étranger](https://www.cndp.ma/transfert-de-donnees-a-letranger/), source officielle consultée le 15 novembre 2026.
- [4] [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite), tarif standard du modèle utilisé.
- [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) ; [documentation RapidOCR](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/).
- [Dépôt privé du groupe](https://github.com/OmarElkhali/BilanLab-VLM) et [notebook de présentation](https://github.com/OmarElkhali/BilanLab-VLM/blob/main/Presentation_Projet_BilanLab.ipynb).
