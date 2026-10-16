"""Gera capas dos PDFs originais e prepara uma cópia local e fixa do PDF.js."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = '6.4.299'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-tools', type=Path)
    parser.add_argument('--pdfjs-archive', type=Path, required=True)
    parser.add_argument('--pdfjs-metadata', type=Path, required=True)
    args = parser.parse_args()
    if args.pdf_tools:
        sys.path.insert(0, str(args.pdf_tools))
    import pymupdf

    metadata = json.loads(args.pdfjs_metadata.read_text(encoding='utf-8'))
    assert metadata['name'] == 'pdfjs-dist' and metadata['version'] == VERSION
    integrity = 'sha512-' + base64.b64encode(hashlib.sha512(args.pdfjs_archive.read_bytes()).digest()).decode()
    assert integrity == metadata['dist']['integrity'], 'A integridade do pacote PDF.js não confere.'
    vendor = ROOT / 'codex/wiki/static/wiki/vendor/pdfjs' / VERSION
    exact = {'build/pdf.min.mjs', 'build/pdf.worker.min.mjs', 'web/pdf_viewer.mjs', 'web/pdf_viewer.css', 'LICENSE'}
    prefixes = ('cmaps/', 'standard_fonts/', 'wasm/', 'web/images/')
    files = {}
    with tarfile.open(args.pdfjs_archive, 'r:gz') as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix('package/')
            if not member.isfile() or not (name in exact or name.startswith(prefixes)):
                continue
            # .js is recognized as JavaScript by both Django and existing Nginx MIME tables.
            target_name = name.removesuffix('.mjs') + '.js' if name.endswith('.mjs') else name
            target = vendor / target_name
            assert target.resolve().is_relative_to(vendor.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            content = archive.extractfile(member).read()
            target.write_bytes(content)
            files[target_name] = hashlib.sha256(content).hexdigest()
    assert {name.removesuffix('.mjs') + '.js' if name.endswith('.mjs') else name for name in exact} <= files.keys()
    (vendor / 'UPSTREAM.json').write_text(json.dumps({'project':'https://github.com/mozilla/pdf.js',
        'version':VERSION, 'package':metadata['dist']['tarball'], 'integrity':integrity,
        'license':'Apache-2.0', 'files':files}, indent=2), encoding='utf-8')

    output = ROOT / 'codex/wiki/static/wiki/img/documents'
    output.mkdir(parents=True, exist_ok=True)
    documents = []
    for slug, filename in (('manual-larp-3-3', 'Manual LARP - 3.3.pdf'),
                           ('cenario-contos-da-cachoeira', 'Cenário_ Contos da Cachoeira.pdf')):
        source = ROOT / 'docs' / filename
        with pymupdf.open(source) as pdf:
            page = pdf[0]
            page.get_pixmap(matrix=pymupdf.Matrix(640/page.rect.width,640/page.rect.width),alpha=False).save(output / f'{slug}.png')
            documents.append({'slug':slug,'pages':len(pdf),'bytes':source.stat().st_size,
                              'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    print(json.dumps({'pdfjs_version':VERSION,'vendor_files':len(files),'documents':documents},ensure_ascii=False))


if __name__ == '__main__':
    main()
