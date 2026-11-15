# Compte-rendu du TP — Extraction de bilans marocains avec un VLM

## Objectif et livrables

Transformer un bilan en JSON fiable, vérifier les montants et comparer les techniques de prompting. Le notebook, les sorties, les journaux et les évaluations sont livrés avec ce rapport.

## Données et environnement réellement utilisés

Un bilan réel, deux pages, exercice clos le 31/12/2024. Référence de travail : 88 lignes, 107 cellules numériques et 352 états/valeurs. SHA-256 : 794d9172b8ac0aa368241932231bcc6a85204a15843f46a85a923cdcaebcc0fa. Les valeurs sont dans l'unité imprimée, non confirmée ; aucune conversion arbitraire en MAD. L'exécution pilotée a lieu sur le PC Windows en Python 3.12.3, et non dans Colab. Les versions sont enregistrées dans environnement.json.

## Prétraitement et confidentialité

Rendu en PNG à 200 DPI. Masquage des zones d'identité et sauvegarde d'images neuves sans couche texte ni métadonnées. Seuls ces PNG sont transmis à Gemini ; le PDF original contient une couche texte qui rend ses masques initiaux insuffisants. La copie intégrée au notebook reste le document original et doit être partagée en conséquence.

## Méthode et corrections justifiées

Le VLM reçoit le catalogue des libellés sans les montants de référence. Il génère un transport compact id/valeurs, transformé sans imputation en JSON métier poste/rubrique/montants/états/parents. Le signe utilisé comme marqueur non applicable a provoqué une confusion avec un montant négatif ; il a été remplacé par NA. Le catalogue a été limité à la page courante. Une cardinalité de 48 lignes a été refusée par Gemini : elle est contrôlée en Python, tandis que le fournisseur impose le reste du schéma. Les essais initiaux sont conservés et séparés de la série validée.

## Résultats mesurés

L'exactitude numérique utilise une égalité Decimal stricte, sans tolérance. La tolérance d'un centime reste réservée aux contrôles de sommes. Une sortie rejetée ne fournit aucun montant accepté ; les causes exactes figurent dans le journal. Les résultats des trois répétitions sont analysés séparément dans le notebook, sans prétendre généraliser à d'autres bilans.

Les échecs de parsing, de structure et les pages manquantes restent au dénominateur ; une réponse rejetée n'est pas transformée en réussite. Trois répétitions par variante dans la nouvelle campagne, ordre mélangé avec graine 42 ; un seul document distinct. Les dispersions sont descriptives, sans garantie de généralisation.

| Essai | Montants exacts | Nets exacts | Lignes acceptées | Durée (s) |
|---|---:|---:|---:|---:|
| api / baseline / ablation_validee_1 | 0/107 | 0/74 | 0/88 | 125.57 |
| api / baseline / ablation_validee_2 | 0/107 | 0/74 | 0/88 | 9.65 |
| api / baseline / ablation_validee_3 | 0/107 | 0/74 | 0/88 | 39.74 |
| api / constraints / ablation_validee_1 | 107/107 | 74/74 | 88/88 | 11.01 |
| api / constraints / ablation_validee_2 | 107/107 | 74/74 | 88/88 | 12.33 |
| api / constraints / ablation_validee_3 | 107/107 | 74/74 | 88/88 | 10.52 |
| api / fewshot / ablation_validee_1 | 107/107 | 74/74 | 88/88 | 31.29 |
| api / fewshot / ablation_validee_2 | 107/107 | 74/74 | 88/88 | 10.64 |
| api / fewshot / ablation_validee_3 | 107/107 | 74/74 | 88/88 | 27.67 |
| api / json_mode / ablation_validee_1 | 65/107 | 32/74 | 48/88 | 44.20 |
| api / json_mode / ablation_validee_2 | 107/107 | 74/74 | 88/88 | 11.11 |
| api / json_mode / ablation_validee_3 | 107/107 | 74/74 | 88/88 | 14.06 |
| api / role / ablation_validee_1 | 107/107 | 74/74 | 88/88 | 10.59 |
| api / role / ablation_validee_2 | 107/107 | 74/74 | 88/88 | 48.73 |
| api / role / ablation_validee_3 | 107/107 | 74/74 | 88/88 | 50.06 |
| api / schema / ablation_validee_1 | 107/107 | 74/74 | 88/88 | 26.82 |
| api / schema / ablation_validee_2 | 107/107 | 74/74 | 88/88 | 18.30 |
| api / schema / ablation_validee_3 | 107/107 | 74/74 | 88/88 | 9.85 |
| api / schema / scan_degrade_valide | 107/107 | 74/74 | 88/88 | 65.88 |
| api / schema / principal_relecture | 107/107 | 74/74 | 88/88 | 31.69 |
| local / schema / local_verification | 0/107 | 0/74 | 0/88 | 864.54 |

### api / gemini-3.1-flash-lite / ablation_validee_1 / baseline

Cellules numériques : 0/107. Nets : 0/74. Lignes : 0/88. Durée : 125.57 s. Contrôles : 0 conformes, 0 en écart, 2 indéterminés. Erreurs : {"ligne_absente": 352}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / baseline

Cellules numériques : 0/107. Nets : 0/74. Lignes : 0/88. Durée : 9.65 s. Contrôles : 0 conformes, 0 en écart, 2 indéterminés. Erreurs : {"ligne_absente": 352}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / baseline

Cellules numériques : 0/107. Nets : 0/74. Lignes : 0/88. Durée : 39.74 s. Contrôles : 0 conformes, 0 en écart, 2 indéterminés. Erreurs : {"ligne_absente": 352}.

### api / gemini-3.1-flash-lite / ablation_validee_1 / constraints

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 11.01 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / constraints

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 12.33 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / constraints

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 10.52 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_1 / fewshot

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 31.29 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / fewshot

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 10.64 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / fewshot

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 27.67 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_1 / json_mode

Cellules numériques : 65/107. Nets : 32/74. Lignes : 48/88. Durée : 44.20 s. Contrôles : 48 conformes, 0 en écart, 2 indéterminés. Erreurs : {"ligne_absente": 160}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / json_mode

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 11.11 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / json_mode

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 14.06 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_1 / role

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 10.59 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / role

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 48.73 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / role

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 50.06 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_1 / schema

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 26.82 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_2 / schema

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 18.30 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / ablation_validee_3 / schema

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 9.85 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / scan_degrade_valide / schema

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 65.88 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### api / gemini-3.1-flash-lite / principal_relecture / schema

Cellules numériques : 107/107. Nets : 74/74. Lignes : 88/88. Durée : 31.69 s. Contrôles : 66 conformes, 0 en écart, 0 indéterminés. Erreurs : {}.

### local / qwen3-vl:4b-instruct / local_verification / schema

Cellules numériques : 0/107. Nets : 0/74. Lignes : 0/88. Durée : 864.54 s. Contrôles : 0 conformes, 0 en écart, 2 indéterminés. Erreurs : {"ligne_absente": 352}.

## Diagnostic local et décision retenue

Le pipeline strict rejette les pages locales non conformes. Avant ce rejet, 34/107 montants bruts correspondent à la référence. Ce diagnostic ne rend pas ces réponses utilisables : il conserve les champs erronés et ne corrige aucun chiffre. 210 marqueurs NA apparaissent dans des colonnes applicables ; années brutes : [3112, 2024].

Le correctif de regex ne résout pas la lecture de Qwen seul. Ce résultat historique reste négatif. Une nouvelle méthode OCR CPU avec relecture ciblée par Qwen a ensuite été exécutée : voir la dernière section du notebook et outputs_vlm/optimisation_locale/synthese.json. Elle est évaluée séparément du benchmark API et de ce premier essai local.

## Robustesse, relecture et lot

Une version synthétique réduite, floutée et moins contrastée est évaluée séparément. Le lot contient l'original et un PDF raster dégradé dérivé du même bilan : deux entrées techniques, une seule entreprise distincte. Le manifeste établit les succès/échecs sans présenter cette duplication comme un nouveau corpus. Les propositions de relecture restent séparées et ne modifient pas automatiquement une prédiction.

## Coût et comparaison API/local

L'API utilisée est Gemini 3.1 Flash-Lite. Estimation au tarif standard payant vérifié le 15/11/2026 : 0,25 USD/million de tokens d'entrée texte/image et 1,50 USD/million de tokens de sortie, raisonnement compris. Le forfait réel du compte, le cache et les requêtes sans compteur retourné ne sont pas connus : ce n'est pas une facture. Le coût local d'électricité et de matériel n'a pas été mesuré. API et local utilisent des modèles différents : la comparaison porte sur deux solutions, sans isoler l'effet du seul mode de déploiement.

## Réponses aux questions du TP

1. Pièges : scans, colonnes, cellules vides, signes, échelle et hiérarchie. Le prétraitement, les états et les contrôles répondent à ces difficultés. 2. Schéma : postes/rubriques/nets, enrichis de brut, amortissements, états, parents et provenance. 3. Prompts : comparer la série validée dans le tableau, sans attribuer à une seule technique un effet universel. 4. JSON : le schéma de génération et la validation indépendante garantissent la conformité des objets acceptés, pas le succès de chaque requête ni la vérité de chaque montant. 5. Sans annotation exhaustive : sommes des enfants directs, brut-amortissement=net et actif=passif ; les erreurs compensées peuvent subsister. 6. Local : Ollama, modèle et latence réels indiqués dans les résultats ; le piège MoE consiste à sous-estimer les poids à héberger et les caches. 7. Exactitude : numérateurs/dénominateurs et catégories d'erreurs ci-dessus et dans les CSV. 8. Confidentialité : privilégier un local maîtrisé si sa qualité suffit ; une API distante exige de vérifier les données personnelles, les conditions contractuelles et les formalités CNDP applicables.

## Limites et conclusion

Le même document a servi à ajuster et évaluer le pipeline ; les résultats décrivent ce cas et ne constituent pas un test indépendant. La référence a été relue sur le PDF, sans double annotation indépendante. Les transformations dégradées sont synthétiques, les masques et le catalogue sont spécifiques au modèle normal fourni. Aucune nouvelle entreprise, entraînement ou exécution Colab/GPU n'est revendiqué. Avant déploiement : corpus distinct, double annotation, mesure mémoire/énergie et vérification humaine des anomalies.

## Sources

Énoncé local TP5_Extraction_Bilans_VLM.docx ; bilan_group_9.pdf. [Gemini tarifs](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite), [Gemini schéma](https://ai.google.dev/gemini-api/docs/structured-output), [Ollama](https://docs.ollama.com/capabilities/structured-outputs), [CNDP](https://www.cndp.ma/transfert-de-donnees-a-letranger/).

## Extension locale mesurée

OCR CPU + Qwen en relecture ciblée : trois essais exacts à 107/107 montants, 352/352 états et valeurs et 66 contrôles ; médiane 16.04 s. OCR seul déjà exact en 8.40 s. Qwen était déjà chargé, et le catalogue et les colonnes sont adaptés au bilan fourni. Il ne s'agit pas d'un gain démontré de Qwen seul ni d'un corpus indépendant. Voir optimisation_locale/synthese.json et la dernière section du notebook.
