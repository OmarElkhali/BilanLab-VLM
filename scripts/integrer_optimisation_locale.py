"""Ajoute une analyse reproductible sans écraser le benchmark historique du TP."""
from pathlib import Path
import textwrap
import nbformat

root = Path(__file__).resolve().parent.parent
path = root/'TP_Extraction_Bilans_VLM_Groupe9.ipynb'
nb = nbformat.read(path, as_version=4)
nb.cells = [c for c in nb.cells if not c.get('id', '').startswith('optimlocal-')]
for cell in nb.cells:
    cell.source = cell.source.replace(
        "Le correctif de regex rétablit la contrainte syntaxique, mais ne résout pas les erreurs de lecture du petit VLM. La solution exploitable retenue pour ce bilan est l'API Gemini avec validation indépendante. Si un déploiement local est impératif, il faut évaluer un modèle plus performant sur du matériel adapté et des recadrages avec en-têtes conservés, puis faire vérifier les anomalies humainement. Ces améliorations supplémentaires ne sont pas présentées comme exécutées.",
        "Le correctif de regex ne résout pas la lecture de Qwen seul. Ce résultat historique reste négatif. Une nouvelle méthode OCR CPU avec relecture ciblée par Qwen a ensuite été exécutée : voir la dernière section du notebook et outputs_vlm/optimisation_locale/synthese.json. Elle est évaluée séparément du benchmark API et de ce premier essai local.")
    cell.source = cell.source.replace(
        "utiliser le JSON API validé. Un modèle local plus performant, des recadrages avec en-têtes et une vérification humaine sont des pistes supplémentaires ; leurs performances n'ont pas été mesurées ici.",
        "conserver cet échec de Qwen seul. La dernière section présente une méthode locale OCR + relecture ciblée par Qwen, mesurée séparément avec ses limites.")
    cell.source = cell.source.replace(
        "Les recadrages par blocs et un modèle local plus performant restent des pistes non exécutées.",
        "Des pilotes recadrés et une méthode locale OCR + Qwen ont ensuite été exécutés ; leurs résultats sont détaillés dans la dernière section, sans remplacer cet essai de Qwen seul.")


def add(kind, source):
    cell = (nbformat.v4.new_code_cell if kind == 'code' else nbformat.v4.new_markdown_cell)(textwrap.dedent(source).strip())
    cell.id = f'optimlocal-{len(nb.cells)}'
    nb.cells.append(cell)


add('markdown', '''
## Amélioration locale — OCR CPU et relecture ciblée par Qwen

**Cette extension est distincte du VLM seul et du benchmark API.** Elle répond à la contrainte du PC : Ryzen 5 5600G, environ 14 Go de RAM utilisables, aucun GPU dédié utilisé par Ollama. L'ancien essai Qwen de 864,54 s et ses erreurs sont conservés.

Pourquoi cette solution ? Sur une page entière, le petit modèle confond les lignes et remplit des cases blanches. Un pilote recadré de quatre lignes a réduit la durée, mais a encore inventé deux montants dans des cases vides. Un schéma contenant une chaîne numérique non bornée a aussi entraîné une génération incomplète. Augmenter seulement le budget de tokens ne résout donc pas la lecture.

La solution CPU utilise **RapidOCR (détection et reconnaissance ONNX)** pour obtenir textes, positions et confiances. Le programme associe les libellés au catalogue sans montants, puis les nombres à la ligne et à la colonne les plus proches. Les cases sans détection restent vides, les colonnes absentes du passif restent non applicables. Qwen3-VL relit les quatre cellules ayant les scores OCR les plus faibles, à partir d'un recadrage et des propositions OCR. Un désaccord devient `illisible` ; aucun montant n'est corrigé à l'aide de la référence ou pour équilibrer les comptes.

**Ce n'est pas un entraînement ni une amélioration démontrée de Qwen seul.** L'OCR fournit déjà les bonnes valeurs sur cet exemple. La relecture assistée est corrélée à l'OCR et ne constitue pas une annotation indépendante. Les coordonnées de colonnes correspondent au modèle normal fourni ; une autre mise en page doit être testée. Les nombres cachés dans la couche texte PDF ne sont pas utilisés par cette méthode.

Sources techniques : [RapidOCR](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/), [sorties structurées Ollama](https://docs.ollama.com/capabilities/structured-outputs). Installation supplémentaire pour relancer : `python -m pip install -r requirements-local.txt`. Les poids OCR et Ollama doivent être installés avant une utilisation sans réseau.
''')
add('code', '''
from scripts.local_hybride import extract as extract_local_hybrid, assemble_page, amount, normalize
import inspect
from IPython.display import Code

# Contrôles ciblés : décimales, signe et conservation d'un libellé significatif.
assert amount("-20 171,22") == "-20171.22"
assert normalize("Banques (Soldes créditeurs)") == normalize("Banques soldes créditeurs")
try:
    amount("123,4")
except ValueError:
    pass
else:
    raise AssertionError("Montant OCR ambigu accepté")
display(Code(inspect.getsource(assemble_page), language="python"))
''')
add('markdown', '''
### Exécution locale et archives auditables

Le bouton de relance reste désactivé dans la remise. Les trois exécutions hybrides ont réellement eu lieu ; la cellule suivante les relit et les évalue. La durée inclut le chargement des modèles OCR, l'OCR des deux images, l'alignement et la relecture Qwen ; elle exclut la préparation initiale des PNG, le téléchargement des poids et la notation après extraction. Qwen était déjà chargé après les pilotes : la comparaison avec l'ancien essai est indicative, sans protocole matériel à froid identique.

Les trois essais portent sur le même bilan : ils vérifient la répétabilité, pas la généralisation. L'essai OCR seul mesure sa contribution séparément. La confiance OCR sert à choisir les cellules à relire ; elle n'est pas une probabilité garantie d'exactitude.
''')
add('code', '''
RUN_LOCAL_HYBRID = False
LOCAL_OPT = OUT / "optimisation_locale"
if RUN_LOCAL_HYBRID:
    # Aucun accès à REFERENCE dans la fonction d'inférence.
    local_raw = extract_local_hybrid(IMAGES, CATALOGUE)
    dump_json(LOCAL_OPT / f"hybride_{time.time_ns()}.json", local_raw)

hybrid_paths = sorted(LOCAL_OPT.glob("hybride_[0-9]*.json"))
first_trial = LOCAL_OPT / "hybride_essai_1.json"
if first_trial.is_file():
    hybrid_paths = [first_trial] + hybrid_paths
hybrid_paths = hybrid_paths[-3:]  # trois dernières exécutions, sans supprimer les archives précédentes
assert len(hybrid_paths) >= 3, "Trois répétitions réelles sont attendues."

def evaluate_local_archive(raw):
    result = {"source_sha256": SOURCE_SHA256, "document_complet": True, "pages": []}
    for page in raw["pages"]:
        expanded = expand_transport({k:v for k,v in page.items() if k != "page"})
        validate_page(expanded)
        result["pages"].append({"page":page["page"], **expanded})
    metrics, errors = evaluate(result)
    checks = arithmetic_checks(result)
    return result, metrics, errors, checks

LOCAL_TRIALS = []
for trial, archive_path in enumerate(hybrid_paths, 1):
    raw = json.loads(archive_path.read_text(encoding="utf-8"))
    result, metrics, errors, checks = evaluate_local_archive(raw)
    LOCAL_TRIALS.append({"essai":trial, "archive":archive_path.name,
        "duree_s":raw["wall_seconds"], "ocr_s":raw["ocr_seconds"],
        "qwen_s":raw["review"]["seconds"], "accords_qwen":sum(r["accord"] for r in raw["review"]["reviews"]),
        **metrics, "controles_ok":sum(c["statut"]=="ok" for c in checks),
        "ecarts":sum(c["statut"]=="ecart" for c in checks), "erreurs_cellules":len(errors)})
    if trial == 1:
        LOCAL_HYBRID_RESULT, LOCAL_HYBRID_RAW = result, raw
        LOCAL_HYBRID_CHECKS, LOCAL_HYBRID_ERRORS = checks, errors
full_table(pd.DataFrame(LOCAL_TRIALS), "Toutes les répétitions hybrides réellement exécutées")
dump_json(LOCAL_OPT / "hybride_bilan.json", LOCAL_HYBRID_RESULT)
dump_json(LOCAL_OPT / "hybride_controles.json", LOCAL_HYBRID_CHECKS)
dump_json(LOCAL_OPT / "hybride_erreurs.json", LOCAL_HYBRID_ERRORS)
''')
add('markdown', '''
### Résultats, durée et contribution de chaque méthode

Les barres d'exactitude utilisent le même dénominateur de 107 montants, y compris les pages rejetées. L'OCR seul et la méthode hybride sont des méthodes supplémentaires, pas de nouvelles variantes du benchmark de prompting. La valeur API correspond à la livraison Python hors benchmark ; son temps n'est pas celui de l'application web. Le facteur de durée est descriptif de cette machine et de ces essais, sans estimation de significativité ni promesse sur un autre document.
''')
add('code', '''
ocr_raw = json.loads((LOCAL_OPT/"ocr_brut.json").read_text(encoding="utf-8"))
_, ocr_metrics, ocr_errors, ocr_checks = evaluate_local_archive(ocr_raw)
old_local = next(r for r in CURRENT_RESULTS if r["backend"] == "local")
api_delivery = next(r for r in CURRENT_RESULTS if r["label"] == "principal_relecture")
hybrid_median = statistics.median(r["duree_s"] for r in LOCAL_TRIALS)
LOCAL_COMPARISON = [
    {"methode":"Qwen seul / page entière", "montants_exacts":evaluate(old_local)[0]["numeric_correct"], "duree_s":old_local["wall_seconds"], "repetitions":1},
    {"methode":"OCR CPU seul", "montants_exacts":ocr_metrics["numeric_correct"], "duree_s":ocr_raw["wall_seconds"], "repetitions":1},
    {"methode":"OCR + Qwen ciblé", "montants_exacts":min(r["numeric_correct"] for r in LOCAL_TRIALS), "duree_s":hybrid_median, "repetitions":len(LOCAL_TRIALS)},
    {"methode":"API / livraison Python", "montants_exacts":evaluate(api_delivery)[0]["numeric_correct"], "duree_s":api_delivery["wall_seconds"], "repetitions":1},
]
full_table(pd.DataFrame(LOCAL_COMPARISON), "Comparaison : un même bilan, quatre méthodes et périmètres explicités")
fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
names = [r["methode"] for r in LOCAL_COMPARISON]
colors = ["#b77216", "#7795b1", "#137d72", "#254c69"]
axes[0].barh(names, [r["montants_exacts"] for r in LOCAL_COMPARISON], color=colors)
axes[0].set(xlim=(0, 120), xlabel="Montants exactement égaux à la référence / 107", title="Fidélité du pipeline strict")
for i, r in enumerate(LOCAL_COMPARISON):
    axes[0].text(r["montants_exacts"]+2, i, f'{r["montants_exacts"]}/107', va="center")
axes[1].barh(names, [r["duree_s"] for r in LOCAL_COMPARISON], color=colors)
axes[1].set(xscale="log", xlabel="Secondes — échelle logarithmique", title="Durée mesurée ; hybride = médiane de 3 essais")
for i, r in enumerate(LOCAL_COMPARISON):
    axes[1].text(r["duree_s"]*1.08, i, f'{r["duree_s"]:.2f} s', va="center")
axes[1].set_xlim(.5, 3000)
finish_figure(fig, "12_optimisation_locale")

LOCAL_SUMMARY = {"methode":"OCR CPU + relecture Qwen assistée par propositions OCR", "trials":LOCAL_TRIALS,
    "comparison":LOCAL_COMPARISON, "median_seconds":hybrid_median,
    "ratio_duree_ancien_sur_hybride":old_local["wall_seconds"]/hybrid_median,
    "ocr_only_metrics":ocr_metrics, "ocr_only_errors":len(ocr_errors),
    "qwen_deja_charge":True, "nouveau_benchmark_prompting":False,
    "limites":["Un seul bilan utilisé au développement", "Colonnes adaptées au modèle normal fourni", "Qwen assisté par OCR, sans gain causal de précision démontré", "Ancien temps non apparié à froid"]}
dump_json(LOCAL_OPT/"synthese.json", LOCAL_SUMMARY)
display(Markdown(f"**Médiane hybride : {hybrid_median:.2f} s.** Le rapport descriptif avec l'ancien essai est {old_local['wall_seconds']/hybrid_median:.1f}× ; ce n'est pas une accélération garantie de Qwen seul."))
''')
add('markdown', '''
### Toutes les valeurs et les preuves de relecture

Les tableaux suivants exposent les 88 lignes, les contrôles, les quatre décisions de Qwen et les détections OCR complètes. Un accord OCR/Qwen est une relecture assistée, pas deux sources indépendantes. Une absence de détection ne garantit pas une case vide sur un document inconnu : un corpus indépendant et une revue humaine restent nécessaires avant utilisation réelle.
''')
add('code', '''
full_table(pd.DataFrame([r for p in LOCAL_HYBRID_RESULT["pages"] for r in p["lignes"]]), "Les 88 postes de l'extraction locale hybride")
full_table(pd.DataFrame(LOCAL_HYBRID_CHECKS), "Tous les contrôles comptables locaux")
full_table(pd.DataFrame([{k:r[k] for k in ("page","id","column","score","value","qwen","accord")} for r in LOCAL_HYBRID_RAW["review"]["reviews"]]), "Les quatre cellules réellement relues par Qwen")
full_table(pd.DataFrame([{**r,"page":i} for i,rows in enumerate(LOCAL_HYBRID_RAW["detections"],1) for r in rows]), "Toutes les détections OCR : texte, géométrie et confiance")
display(Code(LOCAL_HYBRID_RAW["review"]["raw"]["message"]["content"], language="json"))
assert all(r["numeric_correct"] == 107 and r["erreurs_cellules"] == 0 and r["controles_ok"] == 66 for r in LOCAL_TRIALS)
print("Vérifié : 3 essais, 107/107 montants, 352/352 états/valeurs et 66 contrôles cohérents par essai.")
report_path = OUT / "compte_rendu.md"
report = report_path.read_text(encoding="utf-8").split("## Extension locale mesurée")[0]
report += f"\\n## Extension locale mesurée\\n\\nOCR CPU + Qwen en relecture ciblée : trois essais exacts à 107/107 montants, 352/352 états et valeurs et 66 contrôles ; médiane {hybrid_median:.2f} s. OCR seul déjà exact en {ocr_raw['wall_seconds']:.2f} s. Qwen était déjà chargé, et le catalogue et les colonnes sont adaptés au bilan fourni. Il ne s'agit pas d'un gain démontré de Qwen seul ni d'un corpus indépendant. Voir optimisation_locale/synthese.json et la dernière section du notebook.\\n"
report_path.write_text(report, encoding="utf-8")
''')
nb.cells[0].source += '\n\n**Extension locale mesurée :** voir la dernière section « Amélioration locale — OCR CPU et relecture ciblée par Qwen ». Elle conserve les échecs du VLM seul et compare les méthodes sans les confondre.' if 'Extension locale mesurée' not in nb.cells[0].source else ''
nbformat.write(nb, path)
print('Analyse locale ajoutée ; exécuter ensuite le notebook en mode archives.')
