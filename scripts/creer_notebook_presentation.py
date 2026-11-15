"""Construit et exécute un notebook de soutenance autonome depuis les preuves archivées."""
import base64
import hashlib
import json
from pathlib import Path, PureWindowsPath
import textwrap
import zlib

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from traitlets.config import Config

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'outputs_vlm'
TARGET = ROOT/'Presentation_Projet_BilanLab.ipynb'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def relative_run(value):
    return OUT/'runs'/(PureWindowsPath(value).name if '\\' in value else Path(value).name)


main = read(OUT/'bilan_group_9_extrait.json')
runs = []
for folder in sorted((OUT/'runs').iterdir()):
    if not (folder/'bilan.json').is_file():
        continue
    result = read(folder/'bilan.json')
    runs.append({'dossier': folder.name, 'bilan': result,
                 'journal': read(folder/'journal.json') if (folder/'journal.json').is_file() else [],
                 'reponses_brutes': {p.name: p.read_text(encoding='utf-8') for p in sorted(folder.glob('*.txt'))}})
local = read(OUT/'optimisation_locale/synthese.json')
payload = {
    'main': main, 'reference': read(OUT/'reference_annotee.json'),
    'catalogue': read(OUT/'catalogue_sans_montants.json'),
    'minimal': read(OUT/'bilan_group_9_TP_minimal.json'),
    'summary': read(OUT/'resultats_finaux.json'),
    'csv_current': (OUT/'comparaison_finale.csv').read_text(encoding='utf-8-sig'),
    'csv_all': (OUT/'comparaison.csv').read_text(encoding='utf-8-sig'),
    'checks': read(relative_run(main['run_dir'])/'controles_comptables.json'),
    'diagnostic': read(OUT/'diagnostic_local_brut.json'),
    'batch': read(OUT/'batch_manifest.json'), 'campaign': read(OUT/'campagne_courante.json'),
    'local': local, 'hybrid': read(OUT/'optimisation_locale/hybride_bilan.json'),
    'hybrid_checks': read(OUT/'optimisation_locale/hybride_controles.json'),
    'hybrid_raw': read(OUT/'optimisation_locale'/local['trials'][0]['archive']),
    'runs': runs,
    'pilots': {p.name: read(p) for p in sorted((OUT/'optimisation_locale').glob('*reponse.json'))},
    'environment': read(OUT/'environnement.json'), 'hardware': read(OUT/'materiel.json'),
    'figures': {p.stem: base64.b64encode(p.read_bytes()).decode() for p in sorted((OUT/'figures').glob('*.png'))},
    'images': {f'page_{i}': base64.b64encode((OUT/f'images_group9/page_{i:02d}.png').read_bytes()).decode() for i in (1, 2)},
    'app': base64.b64encode((ROOT/'webapp/outputs/resultats-live.png').read_bytes()).decode(),
}
# Retirer les chemins de profil du snapshot ; aucun PDF original ni secret n'est embarqué.
raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace(str(ROOT).replace('\\', '\\\\'), '[projet]').encode()
encoded = base64.b64encode(zlib.compress(raw, 9)).decode()
digest = hashlib.sha256(raw).hexdigest()
nb = nbformat.v4.new_notebook(metadata={
    'kernelspec': {'display_name': 'Python VLM TP', 'language': 'python', 'name': 'vlm-tp'},
    'language_info': {'name': 'python'},
    'title': 'BilanLab — présentation du projet et résultats',
    'description': 'Lecture autonome des résultats mesurés, sans inférence.',
})


def cell(kind, source, *, hidden=False):
    item = (nbformat.v4.new_code_cell if kind == 'code' else nbformat.v4.new_markdown_cell)(textwrap.dedent(source).strip())
    item.metadata['slideshow'] = {'slide_type': 'fragment' if kind == 'code' else 'slide'}
    if hidden:
        item.metadata.update(jupyter={'source_hidden': True}, tags=['hide-input'])
        item.metadata['slideshow']['slide_type'] = 'skip'
    nb.cells.append(item)


cell('markdown', '''
# BilanLab
### Du bilan financier à une extraction structurée et vérifiable

**Groupe 9 · Projet VLM · Soutenance et résultats mesurés · 15 novembre 2026**

Ce notebook présente le projet : le besoin, les choix de code, les méthodes comparées, les résultats et leurs limites. Chaque section comporte uniquement le code nécessaire à l'affichage ou à la vérification des résultats.

**Lecture directe :** les sorties sont déjà enregistrées. Pour les recalculer, exécuter les cellules dans l'ordre avec Python, pandas et IPython. Aucun appel API, téléchargement, accès au PDF original ou chargement de modèle n'est effectué. Les images masquées, graphiques, tableaux et réponses brutes sont intégrés à ce fichier.

Les grands tableaux sont complets et défilables ; les détails techniques se déplient. Le notebook technique `TP_Extraction_Bilans_VLM_Groupe9.ipynb` conserve l'implémentation complète des inférences.
''')

setup = '''
import base64, hashlib, io, json, zlib
from collections import Counter
from decimal import Decimal
from html import escape
import pandas as pd
from IPython.display import HTML, Markdown, display

# Snapshot compressé des seules preuves de résultats ; aucun PDF original ni secret.
SNAPSHOT = __ENCODED__
raw = zlib.decompress(base64.b64decode(SNAPSHOT))
assert hashlib.sha256(raw).hexdigest() == __DIGEST__
D = json.loads(raw)

STYLE = """<style>
.bl{font:15px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#142838!important;background:#fff!important;color-scheme:light;max-width:1200px;padding:18px;box-sizing:border-box}
.bl h3{font-size:21px;color:#137d72;margin:18px 0 10px}.bl p{margin:10px 0}
.bl .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;margin:18px 0}
.bl .kpi{border-top:4px solid #137d72;background:#f1f7f7;padding:18px}.bl .value{display:block;font-size:29px;font-weight:700;line-height:1.3}
.bl .label{display:block;font-size:13px;color:#52697a;margin-top:8px}
.bl .note{background:#edf7f4;border-left:4px solid #137d72;padding:13px 18px;margin:16px 0}
.bl .warn{background:#fff6e7;border-color:#b77216;color:#704b17}
.bl .scroll{overflow:auto;max-height:530px;border:1px solid #dce6eb;margin:12px 0 22px}
.bl table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
.bl th{color:#142838!important;background:#eaf1f5!important;position:sticky;top:0;text-align:left;padding:10px;border-bottom:2px solid #d1dfe6}
.bl td{color:#142838!important;background:#fff!important;padding:9px 10px;border-bottom:1px solid #e2e9ed;vertical-align:top;min-width:85px}
.bl tbody tr:nth-child(even) td{background:#f7fafb!important}.bl img{display:block;max-width:100%;height:auto;margin:16px auto}
.bl details{margin:16px 0;border-top:1px solid #dce6eb;padding-top:12px}.bl summary{cursor:pointer;font-weight:600;color:#175b77}
.bl summary:focus-visible{outline:2px solid #137d72}.bl pre{color:#142838!important;white-space:pre;overflow:auto;max-height:520px;background:#f3f6f8!important;padding:16px;font-size:12px}
.bl .pages{display:flex;gap:16px;align-items:flex-start}.bl .pages img{width:48%}
</style>"""

def panel(content):
    display(HTML(STYLE + '<div class="bl" style="color:#142838;background-color:#ffffff;color-scheme:light">' + content + '</div>'))

def table(data, title, folded=False):
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    content = '<h3>' + escape(title) + '</h3><p>' + str(len(frame)) + ' lignes — aucune troncature des données.</p>'
    content += '<div class="scroll">' + frame.to_html(index=False, na_rep='—', escape=True, max_rows=None, max_cols=None) + '</div>'
    panel('<details><summary>'+escape(title)+'</summary>'+content+'</details>' if folded else content)

def figure(name, caption):
    panel('<img alt="'+escape(caption, quote=True)+'" src="data:image/png;base64,'+D['figures'][name]+'"><p>'+escape(caption)+'</p>')

def details(title, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value
    panel('<details><summary>'+escape(title)+'</summary><pre>'+escape(text)+'</pre></details>')

CURRENT = pd.read_csv(io.StringIO(D['csv_current']))
ALL = pd.read_csv(io.StringIO(D['csv_all']))
BENCH = CURRENT[CURRENT.experience.str.startswith('ablation_validee_')].copy()
ROWS = [r for p in D['main']['pages'] for r in p['lignes']]
COLUMNS = ['montant_brut_N','montant_amort_N','montant_net_N','montant_net_N1']
assert len(ROWS)==88 and len(BENCH)==18 and len(D['local']['trials'])==3
print('Résultats intégrés chargés. Aucun appel à un modèle et aucun fichier externe nécessaire.')
'''
cell('code', setup.replace('__ENCODED__', repr(encoded)).replace('__DIGEST__', repr(digest)), hidden=True)


def section(title, explanation, code):
    cell('markdown', title+'\n\n'+explanation)
    cell('code', code, hidden=True)
    nb.cells[-1].metadata['slideshow'] = {'slide_type': 'fragment'}


section('## 01 — Ce que le projet a obtenu',
    "L'objectif est de transformer un bilan en données structurées puis de vérifier leur fidélité. Les indicateurs ci-dessous décrivent **le document fourni**, utilisé aussi au développement. Ils ne démontrent pas une fiabilité universelle.", '''
metrics = [('2', 'pages de bilan'), ('88', 'postes normalisés'), ('107/107', 'montants API exacts'),
           ('66', 'contrôles numériques cohérents'), ('16,04 s', 'médiane locale hybride / 3 essais')]
panel('<div class="kpis">'+''.join('<div class="kpi"><span class="value">'+v+'</span><span class="label">'+t+'</span></div>' for v,t in metrics)+'</div>'
      +'<div class="note">La solution locale est une méthode hybride OCR + relecture Qwen. L’OCR seul est déjà exact sur ce bilan. L’ancien échec de Qwen seul est conservé.</div>')
table(D['local']['comparison'], 'Les quatre méthodes : exactitude et durée réelle')
''')

section('## 02 — Objectif du TP et travail réalisé',
    "Le projet suit quatre responsabilités : comprendre le document, extraire, vérifier puis comparer. Les améliorations sont présentées comme des extensions du TP. Le fichier de l'énoncé s'appelle TP5, mais son titre intérieur indique TP3.", '''
table([
 {'Partie':'A — Compréhension', 'Travail':'Lire actif/passif, années, signes, colonnes et pièges', 'Preuve':'Deux pages masquées et règles de représentation'},
 {'Partie':'B — Extraction API', 'Travail':'JSON minimal à quatre champs ; six stratégies de prompt', 'Preuve':'90 lignes minimales et 18 essais contrôlés'},
 {'Partie':'C — Local', 'Travail':'Ollama Qwen3-VL 4B Instruct sur CPU', 'Preuve':'Échec initial conservé, puis extension OCR + Qwen mesurée'},
 {'Partie':'D — Validation', 'Travail':'JSON, couverture, états, calculs et référence', 'Preuve':'88 postes, 352 cellules et 66 contrôles numériques'},
 {'Partie':'Extensions', 'Travail':'Scan dégradé, lot technique, interface web et soutenance', 'Preuve':'Journaux, figures, JSON et application'}
], 'Correspondance entre le besoin et les livrables')
''')

section('## 03 — Lire le bilan et protéger son contenu',
    "Les deux pages ci-dessous sont des **PNG masqués dans les pixels**. La clôture est au 31/12/2024. L'actif comporte brut, amortissement, net N et net N−1 ; le passif comporte uniquement les deux nets. L'unité n'est pas confirmée : aucune conversion en MAD n'est inventée. Le PDF original comportait une couche texte sous les masques visuels ; il n'est pas embarqué ici.", '''
panel('<div class="pages">'+''.join('<img alt="Page '+str(i)+' du bilan, identité masquée" src="data:image/png;base64,'+D['images']['page_'+str(i)]+'">' for i in (1,2))+'</div>')
table([
 {'Piège':'Case vide ≠ zéro', 'Réponse':'Conserver null et un état explicite'},
 {'Piège':'Colonne absente du passif', 'Réponse':'État non_applicable, distinct de vide'},
 {'Piège':'Négatifs et espaces de milliers', 'Réponse':'Chaînes décimales signées, puis Decimal'},
 {'Piège':'Totaux et détails', 'Réponse':'Sommer uniquement les enfants directs'},
 {'Piège':'Mauvais masque PDF', 'Réponse':'Transmettre uniquement les PNG neufs contrôlés'}
], 'Difficultés et solutions retenues')
''')

section('## 04 — Architecture : où intervient chaque partie du code',
    "`load_pdf` et `prepare_images` préparent les entrées. Les clients Gemini/Ollama réalisent l'inférence. `validate_page` filtre les objets, `arithmetic_checks` contrôle les calculs et `evaluate` compare aux annotations. Le catalogue contient seulement les libellés et la hiérarchie ; la référence chiffrée reste du côté évaluation. L'extension locale ajoute l'OCR et une relecture ciblée, présentés en section 11.", '''
figure('00_architecture', 'Pipeline principal : préparation → modèle → contrat JSON → contrôles → évaluation.')
''')

section('## 05 — Deux contrats JSON et quatre états de cellule',
    "Le contrat minimal demandé contient **poste, rubrique, montant_net_N, montant_net_N1**. Le pipeline enrichi ajoute les identifiants, les parents, brut/amortissement et les états. Les 90 lignes imprimées deviennent 88 postes : le doublon Trésorerie / Total III est fusionné une fois par page, sans changer les montants.", '''
details('Exemple réel du JSON minimal — premières lignes', D['minimal']['pages'][0]['lignes'][:3])
table([{'État':'lu','Valeur':'Chaîne décimale, y compris 0.00'}, {'État':'vide','Valeur':'null ; case blanche'},
       {'État':'illisible','Valeur':'null ; lecture incertaine'}, {'État':'non_applicable','Valeur':'null ; colonne inexistante'}], 'Conventions de données')
figure('04_etats_et_couverture', 'Répartition des 352 états et couverture des postes.')
details('Catalogue complet sans montants', D['catalogue'])
''')

section('## 06 — Comparer les prompts avec un protocole explicite',
    "Six variantes cumulatives sont comparées, avec trois répétitions par variante : **18 essais** sur les mêmes images. Température 0, ordre mélangé avec graine 42, aucun réessai de validation dans le benchmark. Les répétitions ne sont pas des entreprises indépendantes. La livraison API relue est hors benchmark.", '''
table([
 {'Variante':'baseline', 'Ajout':'Consigne simple, sans rôle système'},
 {'Variante':'role', 'Ajout':'Rôle de transcription comptable'},
 {'Variante':'constraints', 'Ajout':'Règles de lecture et de représentation'},
 {'Variante':'fewshot', 'Ajout':'Exemple fictif, sans montant du bilan'},
 {'Variante':'json_mode', 'Ajout':'Contrainte de sortie JSON'},
 {'Variante':'schema', 'Ajout':'Schéma de génération structuré'}
], 'Les six stratégies et ce qui change')
figure('01_exactitude_et_validation', 'Exactitude et validation des 18 essais : les pages rejetées restent au dénominateur.')
table(BENCH[['variante','experience','numeric_correct','numeric_total','taux_json','taux_schema','taux_acceptation','latence_document_s']], 'Tous les essais du benchmark')
panel('<div class="note warn">Le score strict nul de la baseline est notamment lié au format Markdown rejeté. Il ne prouve pas que le modèle ne sait lire aucun chiffre. Le mode JSON a un essai à 65/107 après une page manquante lors d’un incident réseau.</div>')
''')

section('## 07 — Vitesse et stabilité : regarder tous les essais',
    "Les points individuels rendent les variations visibles. Une panne consomme aussi du temps. Les médianes sur trois répétitions décrivent cette session ; elles ne permettent pas de classer universellement les méthodes.", '''
figure('02_latence_et_stabilite', 'Durées individuelles, médianes et stabilité des stratégies.')
table(BENCH.groupby('variante', sort=False).latence_document_s.agg(['count','mean','median','std','min','max']).reset_index(), 'Statistiques de durée, en secondes')
figure('03_pages_et_echecs', 'Détail des pages et causes de rejet : distinguer transport, syntaxe et validation.')
''')

section('## 08 — Résultat API : toutes les lignes du bilan',
    "L'extraction de livraison `principal_relecture` obtient 107/107 montants et 74/74 nets exacts, avec 88 postes, en 31,69 s. Elle est séparée de l'incident initial et des 18 essais. Les deux tableaux contiennent **toutes les lignes**, avec leurs valeurs imprimées ; les états détaillés sont disponibles juste après.", '''
for nature in ['actif','passif']:
    subset = [r for r in ROWS if r['rubrique']==nature]
    table(pd.DataFrame(subset)[['id','parent_id','poste','type_ligne']+COLUMNS], 'Tous les postes — '+nature)
states = [{'id':r['id'],'poste':r['poste'],'colonne':c,'valeur':r[c],'etat':r['etats'][c]} for r in ROWS for c in COLUMNS]
table(states, 'Les 352 cellules : valeur et état', folded=True)
details('JSON API complet', D['main'])
''')

section('## 09 — Contrôles comptables et vérification exacte',
    "Les contrôles vérifient les sommes des enfants directs, brut − amortissement = net et actif = passif. Ils utilisent Decimal avec une tolérance d'un centime. L'évaluation des montants contre la référence utilise une **égalité exacte**, sans tolérance. Une égalité comptable peut cacher deux erreurs compensées : elle ne remplace pas l'annotation.", '''
gold = {r['id']:r for r in D['reference']['lignes']}
def exact_result(result):
    predicted = {r['id']:r for p in result['pages'] for r in p['lignes']}
    correct = total = cells = 0
    for identifier, expected in gold.items():
        actual = predicted.get(identifier)
        for column in COLUMNS:
            value = expected[column]
            same = actual is not None and actual[column] is not None and value is not None and Decimal(actual[column])==Decimal(value)
            if value is not None:
                total += 1; correct += bool(same)
            cells += bool(actual is not None and actual['etats'][column]==expected['etats'][column]
                          and (same if value is not None else actual[column] is None))
    return {'montants_exacts':correct,'montants_attendus':total,'cellules_exactes':cells,'cellules_attendues':352,'postes':len(predicted)}

verification = exact_result(D['main'])
assert verification['montants_exacts']==107 and verification['cellules_exactes']==352
table([verification], 'Vérification recalculée à partir du JSON intégré')
figure('05_controles_comptables', '66 contrôles numériques cohérents ; les contrôles sans données restent distingués.')
table(D['checks'], 'Tous les contrôles comptables et leurs écarts')
''')

section('## 10 — Comprendre l’échec initial de Qwen seul',
    "Qwen3-VL 4B Instruct, quantifié Q4_K_M, a été exécuté sur CPU avec images plafonnées à 1400 pixels. La lecture brute retrouve 34/107 montants, mais les pages sont rejetées : 210 marqueurs NA dans des colonnes applicables et une année 3112. La durée est 864,54 s. Ce résultat concerne un modèle dense, sans exécution GPU/MoE.", '''
figure('06_concordance_et_local', 'Concordance API et diagnostic local avant rejet : ne pas confondre les deux niveaux.')
table(D['diagnostic']['erreurs'], 'Tous les écarts numériques bruts de Qwen seul')
details('Diagnostic brut complet', D['diagnostic'])
details('Pilotes recadrés : réponses réellement obtenues', D['pilots'])
panel('<div class="note warn">Les pilotes de quatre lignes réduisent la génération mais inventent encore deux cases remplies. Une correction du JSON ne résout pas à elle seule la lecture des pixels.</div>')
''')

section('## 11 — La solution locale retenue : OCR et relecture ciblée',
    "RapidOCR lit les textes, positions et confiances. Le code associe les montants aux cellules par géométrie et par libellés du catalogue. Qwen relit ensuite les **quatre cellules de plus faible confiance**, avec leurs images et les propositions OCR. Un désaccord est marqué illisible. Aucun montant de référence ni calcul d'équilibrage n'est utilisé pour corriger la sortie. **L'OCR seul était déjà exact ici** : aucun gain causal de précision de Qwen n'est démontré.", '''
figure('12_optimisation_locale', 'Comparer les pipelines : OCR seul, OCR + Qwen, Qwen seul et API.')
table(D['local']['trials'], 'Les trois essais hybrides complets, sans sélectionner le meilleur')
assert exact_result(D['hybrid'])['montants_exacts']==107
assert exact_result(D['hybrid'])['cellules_exactes']==352
table([exact_result(D['hybrid'])], 'Vérification recalculée du JSON local hybride')
reviews = D['hybrid_raw']['review']['reviews']
table([{k:r[k] for k in ['page','id','column','score','value','qwen','accord']} for r in reviews], 'Les quatre cellules relues et les décisions de Qwen')
details('Réponse brute de la relecture Qwen', D['hybrid_raw']['review']['raw'])
panel('<div class="note warn">Trois essais sur un seul bilan ; Qwen était déjà chargé. Les coordonnées de colonnes sont adaptées au modèle normal fourni. Le rapport de durée avec l’ancien essai n’est pas un benchmark matériel apparié à froid.</div>')
''')

section('## 12 — Toutes les preuves de l’extraction locale',
    "Les tableaux suivants permettent de contrôler les détections, les lignes finales et les calculs. Une confiance OCR n'est pas une probabilité garantie d'exactitude. Une absence de détection peut devenir une fausse case vide sur un document inconnu ; il faut donc valider d'autres mises en page.", '''
table([r for p in D['hybrid']['pages'] for r in p['lignes']], 'Les 88 postes locaux, avec leurs états', folded=True)
table(D['hybrid_checks'], 'Tous les contrôles du résultat hybride', folded=True)
table([{**r,'page':i} for i,rows in enumerate(D['hybrid_raw']['detections'],1) for r in rows], 'Toutes les détections OCR : texte, position et score', folded=True)
table(D['hybrid_raw']['evidence'], 'Tous les montants OCR alignés aux cellules', folded=True)
details('JSON local hybride complet', D['hybrid'])
''')

section('## 13 — Exploiter les montants extraits',
    "Le total actif/passif N vaut 20 702 296,47, contre 21 253 217,96 en N−1, soit environ −2,59 %. Les créances clients représentent environ 88,40 % de l'actif N. Il s'agit d'une description du document, sans inventer d'unité ni produire de recommandation financière.", '''
figure('07_structure_bilan', 'Composition du bilan et évolution entre N et N−1, dans l’unité imprimée.')
by_id = {r['id']:r for r in ROWS}
table([{k:r[k] for k in ['id','poste','montant_net_N','montant_net_N1']} for r in ROWS if r['type_ligne'] in ['total','sous_total']], 'Tous les totaux et sous-totaux des deux exercices')
''')

section('## 14 — Robustesse, lot et version minimale du TP',
    "Le scan synthétique réduit, flouté et moins contrasté reste exact dans l'essai API à 65,88 s. Le lot contient deux fichiers du même bilan : original et scan dérivé. Il ne constitue pas deux entreprises. La version minimale à quatre champs conserve les 90 lignes imprimées avant normalisation.", '''
figure('09_scan_original_et_degrade', 'Même zone : original et dégradation synthétique.')
table([r for r in D['summary'] if r['experience'] in ['scan_degrade_valide','batch_valide']], 'Résultats des tests de robustesse et du lot')
table(D['batch'], 'Les deux entrées du lot technique')
table([{'page':p['page'],**r} for p in D['minimal']['pages'] for r in p['lignes']], 'Les 90 lignes du JSON minimal réellement extrait', folded=True)
''')

section('## 15 — Tokens, coût et limites de la comparaison',
    "L'estimation API utilise les compteurs connus et les tarifs documentés au 15/11/2026 : 0,25 USD par million de tokens d'entrée et 1,50 USD en sortie. Une donnée de coût inconnue reste absente, pas zéro. La livraison compte 5 935 tokens d'entrée et 3 359 de sortie, soit environ 0,00652 USD à ce tarif. Ce n'est pas une facture ; le coût matériel et électrique local n'est pas mesuré.", '''
figure('08_cout_et_compromis', 'Compromis mesuré entre durée, exactitude et coût estimable.')
table(CURRENT[['backend','variante','experience','tokens_entree_connus','tokens_sortie_connus','cout_api_estime_usd','latence_document_s','numeric_correct']], 'Tous les compteurs et coûts estimables de la campagne')
''')

section('## 16 — Journaux et résultats complets, y compris les échecs',
    "Cette section conserve toutes les expériences archivées, puis tous les journaux et réponses brutes. La campagne actuelle et les essais historiques sont distingués. Les archives ne sont pas de nouveaux documents indépendants ; un essai rejeté n'est pas remplacé par une sortie réparée à partir du gold.", '''
table(CURRENT, 'Toutes les mesures de la campagne actuelle', folded=True)
table(ALL, 'Toutes les mesures historiques disponibles', folded=True)
attempts = [{'dossier':r['dossier'],'experience':r['bilan'].get('label'),**log} for r in D['runs'] for log in r['journal']]
table(attempts, 'Tous les journaux de tentatives de pages', folded=True)
body = ''
for run in D['runs']:
    title = run['bilan'].get('backend','')+' / '+run['bilan'].get('label','')+' / '+run['dossier']
    body += '<details><summary>'+escape(title)+'</summary><pre>'+escape(json.dumps(run,ensure_ascii=False,indent=2))+'</pre></details>'
panel('<details><summary>Archives complètes : '+str(len(D['runs']))+' expériences, JSON et réponses brutes</summary>'+body+'</details>')
''')

section('## 17 — BilanLab : rendre le projet utilisable',
    "L'application permet d'importer un bilan, de masquer les zones sensibles, de comparer les méthodes, de lire les contrôles et d'exporter le JSON. La capture ci-dessous est une exécution réelle : 88 postes, 107/107 et 66 contrôles, en 16,05 s. **Ce chrono web diffère des chronos Python**. La nouvelle méthode OCR + Qwen est disponible dans le notebook technique et en CLI ; le bouton Qwen du site utilise encore le VLM seul.", '''
panel('<img alt="Capture réelle de BilanLab : comparaison et tableau des postes" src="data:image/png;base64,'+D['app']+'">')
table([
 {'Livrable':'Notebook technique', 'Rôle':'Code complet, fonctions, inférences facultatives et expériences'},
 {'Livrable':'Ce notebook de présentation', 'Rôle':'Parcours de soutenance autonome, graphiques et toutes les preuves'},
 {'Livrable':'Application web', 'Rôle':'Importer, masquer, comparer et exporter'},
 {'Livrable':'PowerPoint de 21 diapositives', 'Rôle':'Soutenance visuelle avec notes orales'},
 {'Livrable':'Dépôt GitHub privé', 'Rôle':'Sources, résultats et collaboration autorisée'}
], 'Comment utiliser les différents livrables')
''')

section('## 18 — Conclusion et réponses à défendre',
    "Le résultat exploitable vient de la lecture, du contrat explicite et des vérifications. Sur ce bilan, l'API et le nouveau pipeline local hybride sont exacts. L'OCR seul est déjà suffisant ici ; conserver Qwen en relecture n'est utile que si son bénéfice est vérifié sur des cas plus difficiles. La suite prioritaire est un corpus indépendant avec plusieurs mises en page et une double annotation.", '''
table([
 {'Question':'Quels pièges ?', 'Réponse':'Colonnes, cases vides, signes, échelle, masques et hiérarchie.'},
 {'Question':'Quel schéma ?', 'Réponse':'Quatre champs minimaux ; contrat enrichi avec états et provenance.'},
 {'Question':'Quel prompt ?', 'Réponse':'Comparer les 18 essais et les échecs, sans effet universel attribué à une seule technique.'},
 {'Question':'Le JSON garantit-il la vérité ?', 'Réponse':'Il garantit une structure contrôlée ; les chiffres doivent encore être vérifiés.'},
 {'Question':'Sans annotation exhaustive ?', 'Réponse':'Contrôles comptables utiles, mais erreurs compensées possibles.'},
 {'Question':'Pourquoi le local hybride ?', 'Réponse':'OCR léger sur CPU, Qwen ciblé ; le VLM seul initial reste insuffisant.'},
 {'Question':'Comment noter ?', 'Réponse':'107 montants, 74 nets et 352 états/valeurs ; égalité exacte et pages rejetées au dénominateur.'},
 {'Question':'Quelle confidentialité ?', 'Réponse':'Pixels réellement masqués, accès maîtrisés et conditions/API/formalités à vérifier.'}
], 'Les huit réponses essentielles du TP')
table([
 {'Limite':'Un seul bilan réel', 'Conséquence':'Aucune généralisation démontrée'},
 {'Limite':'Référence utilisée au développement, sans double annotation', 'Conséquence':'Ce n’est pas un test indépendant'},
 {'Limite':'Colonnes et catalogue adaptés au modèle fourni', 'Conséquence':'Valider d’autres mises en page'},
 {'Limite':'Qwen déjà chargé lors des nouveaux essais', 'Conséquence':'Temps descriptifs, sans comparaison appariée à froid'},
 {'Limite':'Relecture Qwen assistée par OCR', 'Conséquence':'Pas de seconde annotation indépendante ni gain causal démontré'},
 {'Limite':'Coût local non mesuré', 'Conséquence':'Ne pas affirmer que le local est gratuit'}
], 'Limites qui changent l’interprétation des scores')
details('Environnement de la campagne et matériel enregistré', {'environment':D['environment'],'hardware':D['hardware']})
assert all(r['numeric_correct']==107 and r['controles_ok']==66 and r['erreurs_cellules']==0 for r in D['local']['trials'])
print('Présentation vérifiée : API 107/107 ; local hybride 107/107 sur 3 essais ; données et preuves intégrées.')
''')
cell('markdown', '''
### Sources et accès au projet

- Énoncé : `TP5_Extraction_Bilans_VLM.docx` ; données : bilan Groupe 9, deux pages, clôture 2024.
- [Documentation Gemini : sorties structurées](https://ai.google.dev/gemini-api/docs/structured-output) et [tarifs](https://ai.google.dev/gemini-api/docs/pricing).
- [Documentation Ollama](https://docs.ollama.com/capabilities/structured-outputs) et [RapidOCR](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/).
- [CNDP : transfert de données à l'étranger](https://www.cndp.ma/transfert-de-donnees-a-letranger/) ; ces éléments ne constituent pas une certification juridique.
- [Dépôt privé BilanLab-VLM](https://github.com/OmarElkhali/BilanLab-VLM), accessible aux collaborateurs autorisés.

**Fin de la présentation — questions et discussion.**
''')

nbformat.write(nb, TARGET)
client = NotebookClient(nb, timeout=300, kernel_name='vlm-tp', resources={'metadata': {'path': str(ROOT)}})
client.execute()
nbformat.validate(nb)
code = [c for c in nb.cells if c.cell_type=='code']
assert len(code)==19 and all(c.execution_count is not None for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
nbformat.write(nb, TARGET)
config = Config()
config.TagRemovePreprocessor.remove_input_tags = {'hide-input'}
html, _ = HTMLExporter(config=config, template_name='lab').from_notebook_node(nb)
TARGET.with_suffix('.html').write_text(html, encoding='utf-8')
report = {'notebook': TARGET.name, 'cellules_totales': len(nb.cells), 'cellules_code': len(code),
          'erreurs': 0, 'sections': 18, 'essais_benchmark': 18, 'essais_hybrides': 3,
          'archives_integrees': len(runs), 'autonome': True, 'inferences_declenchees': False,
          'snapshot_sha256': digest, 'notebook_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
          'export_html': TARGET.with_suffix('.html').name}
(OUT/'verification_notebook_presentation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
