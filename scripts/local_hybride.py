"""Extraction CPU depuis les pixels : RapidOCR, géométrie et relecture Qwen ciblée.

Le catalogue apporte uniquement les libellés. Aucun accès à la référence chiffrée.
Adapté au modèle normal marocain du TP ; une autre mise en page doit être validée.
"""
import base64
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import io
import json
from pathlib import Path
import re
import time
import unicodedata

from PIL import Image
import requests


def normalize(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    text = text.split('(')[0] if text.strip().startswith('total') else re.sub(r'\([12]\)', '', text)
    return re.sub(r'[^a-z0-9]', '', text).replace('total1', 'totali')


def amount(text):
    text = re.sub(r'\s+', '', text).replace('−', '-').replace(',', '.')
    if not re.fullmatch(r'-?\d+\.\d{2}', text):
        raise ValueError('OCR numérique ambigu : ' + text)
    return text


def assemble_page(rows, size, nature, catalogue):
    width, height = size
    candidates = []
    for item in rows:
        item = dict(item)
        item['x'] = sum(p[0] for p in item['box']) / 4 / width
        item['y'] = sum(p[1] for p in item['box']) / 4 / height
        candidates.append(item)
    label_limit = .45 if nature == 'actif' else .65
    labels = [r for r in candidates if r['x'] < label_limit and .13 < r['y'] < .95]
    canonical = [r for r in catalogue if r['rubrique'] == nature]
    pairs = []
    for row in canonical:
        name = row['poste']
        suffix = row['id'].split('_')[1]
        if suffix in ('I', 'II', 'III'):
            name = 'TOTAL ' + suffix
        elif suffix == 'E':
            name = 'ECART DE CONVERSION ' + nature
        elif row['id'] in ('A_J', 'P_H'):
            name = 'ECARTS DE CONVERSION ' + nature
        for index, label in enumerate(labels):
            score = SequenceMatcher(None, normalize(name), normalize(label['text'])).ratio()
            pairs.append((score, row['id'], index))
    assigned, used = {}, set()
    for score, identifier, index in sorted(pairs, reverse=True):
        if score >= .72 and identifier not in assigned and index not in used:
            assigned[identifier] = labels[index]
            used.add(index)
    missing = {r['id'] for r in canonical} - assigned.keys()
    if missing:
        raise ValueError('Libellés non alignés : ' + ', '.join(sorted(missing)))
    boundaries = [.451, .579, .707, .833, .972] if nature == 'actif' else [.674, .826, .972]
    values = {r['id']: [None] * 4 if nature == 'actif' else ['NA', 'NA', None, None] for r in canonical}
    evidence = []
    for item in candidates:
        if not boundaries[0] < item['x'] < boundaries[-1] or not .13 < item['y'] < .95:
            continue
        identifier, label = min(assigned.items(), key=lambda pair: abs(pair[1]['y'] - item['y']))
        if abs(label['y'] - item['y']) > .007:
            continue  # En-têtes, marqueurs et doublon imprimé de trésorerie.
        column = next((i for i in range(len(boundaries)-1) if boundaries[i] < item['x'] < boundaries[i+1]), None)
        if column is None:
            continue
        column += 0 if nature == 'actif' else 2
        try:
            value = amount(item['text'])
        except ValueError:
            value = '?'
        if values[identifier][column] is not None:
            raise ValueError('Plusieurs détections dans une cellule : ' + identifier)
        values[identifier][column] = value
        evidence.append({**item, 'id': identifier, 'column': column, 'value': value})
    years = [int(m.group(1)) for r in candidates if 'CLOS' in r['text'].upper()
             for m in re.finditer(r'\d{2}/\d{2}/(\d{4})', r['text'])]
    page = {'nature': nature, 'exercice_N': years[0] if len(set(years)) == 1 else None,
            'unite': 'inconnue', 'preuve_unite': '', 'avertissements': [],
            'lignes': [{'id': r['id'], 'valeurs': values[r['id']]} for r in canonical]}
    return page, evidence


def review_qwen(images, evidence, *, count=4, url='http://127.0.0.1:11434', model='qwen3-vl:4b-instruct'):
    if url != 'http://127.0.0.1:11434':
        raise ValueError('La relecture reste sur la boucle locale.')
    selected = sorted(evidence, key=lambda x: x['score'])[:count]
    crops = []
    for item in selected:
        with Image.open(images[item['page']-1]) as image:
            box = item['box']
            rect = (max(0, int(min(p[0] for p in box))-5), max(0, int(min(p[1] for p in box))-4),
                    min(image.width, int(max(p[0] for p in box))+5), min(image.height, int(max(p[1] for p in box))+4))
            crops.append(image.crop(rect).convert('RGB'))
    sheet = Image.new('RGB', (max(im.width for im in crops)+20, sum(im.height+24 for im in crops)), 'white')
    y = 12
    for crop in crops:
        sheet.paste(crop, (10, y)); y += crop.height + 24
    buffer = io.BytesIO(); sheet.save(buffer, format='PNG')
    schema = {'type': 'object', 'properties': {'valeurs': {'type': 'array',
              'items': {'type': 'string', 'maxLength': 24}, 'minItems': len(crops), 'maxItems': len(crops)}},
              'required': ['valeurs'], 'additionalProperties': False}
    payload = {'model': model, 'stream': False, 'think': False, 'keep_alive': '30m', 'format': schema,
               'messages': [{'role': 'user', 'content': f'Lis les {len(crops)} nombres de cette image, du haut vers le bas. Un nombre par bande. Recopie exactement les chiffres et les signes. Supprime les espaces de milliers, remplace la virgule par un point, garde deux decimales. Reponds avec valeurs, une liste de chaines. Aucun calcul. Voici les propositions OCR a verifier sur les pixels : '+json.dumps([r['value'] for r in selected]),
                             'images': [base64.b64encode(buffer.getvalue()).decode('ascii')]}],
               'options': {'temperature': 0, 'num_ctx': 4096, 'num_predict': 220, 'num_thread': 6}}
    start = time.perf_counter()
    response = requests.post(url + '/api/chat', json=payload, timeout=300)
    response.raise_for_status(); raw = response.json()
    archive = Path(__file__).resolve().parent.parent/'outputs_vlm/optimisation_locale'
    archive.mkdir(exist_ok=True)
    (archive/f'qwen_relecture_{time.time_ns()}.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    if raw.get('done_reason') != 'stop':
        raise ValueError('Relecture Qwen tronquée.')
    parsed = json.loads(raw['message']['content'])
    import jsonschema
    jsonschema.validate(parsed, schema)
    reviews = [{**item, 'qwen': amount(parsed['valeurs'][i]), 'accord': amount(parsed['valeurs'][i]) == item['value']} for i, item in enumerate(selected)]
    return {'seconds': time.perf_counter()-start, 'raw': raw, 'reviews': reviews,
            'image_base64': base64.b64encode(buffer.getvalue()).decode('ascii')}


def extract(images, catalogue, *, qwen=True):
    from rapidocr import RapidOCR
    start = time.perf_counter()
    engine = RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads': 6,
                             'EngineConfig.onnxruntime.inter_op_num_threads': 1})
    pages, detections, evidence = [], [], []
    for number, image_path in enumerate(images, 1):
        result = engine(str(image_path))
        rows = [{'box': b.tolist(), 'text': text, 'score': float(score)}
                for b, text, score in zip(result.boxes, result.txts, result.scores)]
        with Image.open(image_path) as image:
            page, cells = assemble_page(rows, image.size, 'actif' if number == 1 else 'passif', catalogue)
        pages.append({'page': number, **page}); detections.append(rows)
        evidence.extend({**r, 'page': number} for r in cells)
    ocr_seconds = time.perf_counter() - start
    review = review_qwen(images, evidence) if qwen else None
    # Un désaccord reste illisible ; aucune réponse n'est choisie à partir du gold.
    if review:
        for item in review['reviews']:
            if not item['accord']:
                page = pages[item['page']-1]
                next(r for r in page['lignes'] if r['id'] == item['id'])['valeurs'][item['column']] = '?'
    return {'pages': pages, 'ocr_seconds': ocr_seconds, 'wall_seconds': time.perf_counter()-start,
            'detections': detections, 'evidence': evidence, 'review': review,
            'method': 'RapidOCR CPU + Qwen3-VL relecture de 4 cellules OCR' if qwen else 'RapidOCR CPU seul',
            'utc': datetime.now(timezone.utc).isoformat(),
            'images_sha256': [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in images],
            'catalogue_sha256': hashlib.sha256(json.dumps(catalogue, sort_keys=True).encode()).hexdigest()}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--ocr-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error('repeats doit être compris entre 1 et 10')
    root = Path(__file__).resolve().parent.parent
    catalogue = json.loads((root/'outputs_vlm/catalogue_sans_montants.json').read_text(encoding='utf-8'))
    images = [root/f'outputs_vlm/images_group9/page_{i:02d}.png' for i in (1, 2)]
    for index in range(args.repeats):
        result = extract(images, catalogue, qwen=not args.ocr_only)
        archive = root/'outputs_vlm/optimisation_locale'
        archive.mkdir(exist_ok=True)
        (archive/f"{'ocr' if args.ocr_only else 'hybride'}_{time.time_ns()}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        (archive/('ocr_brut.json' if args.ocr_only else 'hybride_brut.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'seconds': result['wall_seconds'], 'ocr_seconds': result['ocr_seconds'],
                         'reviews': [{k: r[k] for k in ('id', 'column', 'value', 'qwen', 'accord')} for r in result['review']['reviews']] if result['review'] else []}, ensure_ascii=False), flush=True)
