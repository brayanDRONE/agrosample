#!/usr/bin/env python3
"""Parse all XML files in the repository and extract code->label rows.
Saves a CSV at data/codigos.csv with columns:
  source, file, code_key, code, label_key, label, full_row_json
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import csv
import json
import sys


def find_row_elements(root):
    rows = root.findall('.//row')
    if rows:
        return rows
    # fallback: any child element that has children
    return [e for e in root if list(e)]


def main():
    base = Path(__file__).resolve().parents[1]
    out_dir = base / 'data'
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / 'codigos.csv'

    xml_files = sorted(p for p in out_dir.glob('*.xml') if p.is_file())
    if not xml_files:
        print('No XML files found.')
        return

    rows_written = 0
    with out_file.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'file', 'code_key', 'code', 'label_key', 'label', 'full_row_json'])
        for p in sorted(xml_files):
            try:
                tree = ET.parse(p)
                root = tree.getroot()
            except Exception as e:
                print(f'skip {p}: parse error {e}', file=sys.stderr)
                continue

            row_elems = find_row_elements(root)
            count = 0
            for r in row_elems:
                d = {}
                for child in r:
                    tag = getattr(child, 'tag', '')
                    if tag is None:
                        continue
                    tag = tag.strip()
                    text = (child.text or '').strip()
                    d[tag] = text

                if not d:
                    continue

                code_keys = [k for k in d.keys() if 'CODIGO' in k.upper() or k.upper().endswith('ID') or k.upper().endswith('KEY')]
                code_key = code_keys[0] if code_keys else next(iter(d.keys()))
                code = d.get(code_key, '')

                label_key = ''
                label = ''
                for k in d.keys():
                    if k == code_key:
                        continue
                    if any(s in k.upper() for s in ('NOMBRE', 'NOM', 'DESCRIP', 'DESCR', 'CONCENTRACION', 'DURACION', 'TEMPERATURA', 'PRODUCTO', 'PAIS', 'RAZON', 'RUBRO')):
                        label_key = k
                        label = d[k]
                        break

                if not label_key:
                    other_keys = [k for k in d.keys() if k != code_key]
                    if other_keys:
                        label_key = other_keys[0]
                        label = d[label_key]

                writer.writerow([p.parent.name, str(p), code_key, code, label_key, label, json.dumps(d, ensure_ascii=False)])
                rows_written += 1
                count += 1

            print(f'parsed {p}: {count} rows')

    print(f'wrote {out_file} rows={rows_written}')


if __name__ == '__main__':
    main()
