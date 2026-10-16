"""Biblioteca pública e entrega dos dois PDFs autorizados da Wiki."""
from pathlib import Path
import re

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import content_disposition_header, http_date, parse_etags, parse_http_date_safe
from django.views.decorators.http import require_safe


DOCUMENTS = (
    {'slug': 'manual-larp-3-3', 'title': 'Manual LARP', 'edition': 'Versão 3.3',
     'category': 'Manual de regras', 'filename': 'Manual LARP - 3.3.pdf', 'pages': 25,
     'description': 'Tenha o manual completo à mão para preparar seu personagem e consultar as regras do jogo.'},
    {'slug': 'cenario-contos-da-cachoeira', 'title': 'Cenário · Contos da Cachoeira', 'edition': 'Caderno de cenário',
     'category': 'O mundo da Cachoeira', 'filename': 'Cenário_ Contos da Cachoeira.pdf', 'pages': 23,
     'description': 'Conheça o cenário que dá vida às histórias e às aventuras dos Contos da Cachoeira.'},
)


def document_path(document):
    root = Path(getattr(settings, 'WIKI_DOCUMENTS_ROOT', settings.BASE_DIR.parent / 'docs')).resolve()
    path = (root / document['filename']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise Http404('Documento não encontrado.')
    return path


def document_info(document):
    try:
        size = document_path(document).stat().st_size
    except (Http404, OSError):
        size = None
    return {**document, 'available': size is not None,
            'size_label': f'{size / 1024 / 1024:.1f}'.replace('.', ',') + ' MB' if size is not None else '',
            'cover': f"wiki/img/documents/{document['slug']}.png",
            'reader_url': reverse('wiki_documento_leitor', args=[document['slug']]),
            'file_url': reverse('wiki_documento_arquivo', args=[document['slug']]),
            'download_url': reverse('wiki_documento_download', args=[document['slug']])}


def get_document(slug):
    document = next((document for document in DOCUMENTS if document['slug'] == slug), None)
    if document is None:
        raise Http404('Documento não encontrado.')
    return document


@require_safe
def document_list(request):
    return render(request, 'wiki/documentos.html', {'documents': [document_info(item) for item in DOCUMENTS]})


@require_safe
def document_reader(request, slug):
    document = get_document(slug)
    document_path(document)
    return render(request, 'wiki/documento_leitor.html', {
        'document': document_info(document), 'documents': [document_info(item) for item in DOCUMENTS]})


def _chunks(path, start, length):
    with path.open('rb') as stream:
        stream.seek(start)
        while length:
            chunk = stream.read(min(length, 64 * 1024))
            if not chunk:
                break
            yield chunk
            length -= len(chunk)


def _byte_range(value, size):
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value.strip())
    if not match or not size:
        raise ValueError
    first, last = match.groups()
    if not first:
        if not last or int(last) <= 0:
            raise ValueError
        return max(0, size - int(last)), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError
    return start, end


@require_safe
def document_file(request, slug, download=False):
    document = get_document(slug)
    path = document_path(document)
    try:
        stat = path.stat()
    except OSError:
        raise Http404('Documento não encontrado.')
    size, modified = stat.st_size, int(stat.st_mtime)
    etag = f'"{stat.st_mtime_ns:x}-{size:x}"'
    headers = {'Accept-Ranges': 'bytes', 'ETag': etag, 'Last-Modified': http_date(modified),
               'Cache-Control': 'public, max-age=3600, no-transform', 'X-Content-Type-Options': 'nosniff',
               'Content-Disposition': content_disposition_header(download, document['filename'])}
    validators = request.headers.get('If-None-Match')
    date = parse_http_date_safe(request.headers.get('If-Modified-Since', ''))
    if (validators and (validators.strip() == '*' or etag in [item.removeprefix('W/') for item in parse_etags(validators)])) or (not validators and date is not None and date >= modified):
        return HttpResponse(status=304, headers=headers)
    requested_range = request.headers.get('Range') if request.method == 'GET' else None
    if_range = request.headers.get('If-Range')
    if requested_range and if_range:
        range_date = parse_http_date_safe(if_range)
        if if_range != etag and (range_date is None or range_date < modified):
            requested_range = None
    if requested_range:
        try:
            start, end = _byte_range(requested_range, size)
        except (ValueError, OverflowError):
            return HttpResponse(status=416, headers={**headers, 'Content-Range': f'bytes */{size}'})
        headers.update({'Content-Range': f'bytes {start}-{end}/{size}', 'Content-Length': str(end - start + 1)})
        return StreamingHttpResponse(_chunks(path, start, end - start + 1), status=206, content_type='application/pdf', headers=headers)
    headers['Content-Length'] = str(size)
    if request.method == 'HEAD':
        return HttpResponse(content_type='application/pdf', headers=headers)
    try:
        stream = path.open('rb')
    except OSError:
        raise Http404('Documento não encontrado.')
    return FileResponse(stream, as_attachment=download, filename=document['filename'], content_type='application/pdf', headers=headers)
