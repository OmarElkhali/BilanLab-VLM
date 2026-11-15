"""Vérifie les fichiers livrés et les notes, sans générer ou modifier d'image."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

from PIL import Image
from pptx import Presentation

deck=Path(__file__).resolve().parent
jobs=json.loads((deck/'slide_jobs.json').read_text(encoding='utf-8'))
expected=[f'slide_{i:02d}' for i in range(1,22)]
assert [s['slide_id'] for s in jobs['slides']]==expected
assert all(s['status'] in ('recorded','accepted') for s in jobs['slides'])
assert Counter(s['status'] for s in jobs['slides'])=={'recorded':20,'accepted':1}
images=sorted((deck/'origin_image').glob('slide_*.png'))
assert [p.stem for p in images]==expected
manifest={}
for image in images:
    with Image.open(image) as im:
        assert abs(im.width/im.height-16/9)<.015,(image.name,im.size)
        im.verify()
    manifest[image.name]={'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'octets':image.stat().st_size}

speech=(deck/'speech.md').read_text(encoding='utf-8')
parts=re.split(r'^## Slide (\d+):[^\n]*\n',speech,flags=re.M)
notes={int(parts[i]):parts[i+1].strip() for i in range(1,len(parts),2)}
assert set(notes)==set(range(1,22))
path=deck/(deck.name+'.pptx')
with zipfile.ZipFile(path) as archive:
    assert archive.testzip() is None
prs=Presentation(path)
assert len(prs.slides)==21
assert abs(prs.slide_width/prs.slide_height-16/9)<.0001
for number,slide in enumerate(prs.slides,1):
    assert len(slide.shapes)==1 and slide.shapes[0].shape_type==13
    assert slide.has_notes_slide
    assert slide.notes_slide.notes_text_frame.text.strip()==notes[number]
    picture=slide.shapes[0]
    assert picture.left==picture.top==0
    assert picture.width==prs.slide_width and picture.height==prs.slide_height
result={'statut':'OK','diapositives':21,'images_enregistrees':20,'temoin_accepte':1,
        'notes_orales_integrees':21,'format':'16:9','backend':'built-in image tool',
        'qa_visuelle':'Chaque image finale inspectee par le parent, apres controle par son sous-agent.',
 'reprises':['slide_01 : titre repete et bandeau retires','slide_03 : en-tete du temoin remplace',
            'slides_17_19_21 : nouvelles mesures locales et recommandations synchronisees'],
        'limites':['Les diapositives sont des images, les elements de texte et de graphe ne sont pas editables separement.',
                   'Les petits caracteres des pages de bilan sont visibles comme document source, non comme tableau de lecture detaillee.',
                   'Validation structurelle du PPTX ; aucune ouverture native dans PowerPoint revendiquee.'],
        'pptx':str(path),'images':manifest}
(deck/'verification_presentation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='images'},ensure_ascii=True))
