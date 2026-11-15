"""Execute et sauvegarde le notebook ; mode archives sans API par defaut."""
import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

parser = argparse.ArgumentParser()
parser.add_argument('--kernel', default='python3', help='Noyau Jupyter, par exemple vlm-tp pour l environnement isole.')
parser.add_argument('--through', type=int, default=None, help='Dernier indice de cellule a executer (facultatif).')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
path = root / 'TP_Extraction_Bilans_VLM_Groupe9.ipynb'
notebook = nbformat.read(path, as_version=4)
client = NotebookClient(notebook, timeout=7200, kernel_name=args.kernel, resources={'metadata': {'path': str(root)}})
with client.setup_kernel():
    for index, cell in enumerate(notebook.cells):
        if args.through is not None and index > args.through:
            break
        if cell.cell_type != 'code':
            continue
        print(f'Cellule {index}', flush=True)
        try:
            client.execute_cell(cell, index)
        finally:
            nbformat.write(notebook, path)
print('Notebook execute et sauvegarde.', flush=True)
