from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse

from .documents import DOCUMENTS


class WikiDocumentTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        override = override_settings(WIKI_DOCUMENTS_ROOT=self.directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.content = b'%PDF-1.7\n' + bytes(range(256)) * 8
        for document in DOCUMENTS:
            (Path(self.directory.name) / document['filename']).write_bytes(self.content)
        self.url = reverse('wiki_documento_arquivo', args=[DOCUMENTS[0]['slug']])

    def body(self, response):
        try:
            return b''.join(response.streaming_content) if response.streaming else response.content
        finally:
            response.close()

    def test_public_library_reader_and_home_navigation(self):
        response = self.client.get(reverse('wiki_documentos'))
        self.assertContains(response, 'Documentos do jogo')
        self.assertContains(response, 'Ler online', count=2)
        self.assertContains(response, 'Baixar PDF', count=2)
        self.assertContains(response, 'aria-current="page"')
        for document in DOCUMENTS:
            response = self.client.get(reverse('wiki_documento_leitor',args=[document['slug']]))
            self.assertContains(response, 'data-pdf-reader')
            self.assertContains(response, reverse('wiki_documento_arquivo',args=[document['slug']]))
            self.assertContains(response, 'data-pdf-fullscreen')
        self.assertContains(self.client.get(reverse('wiki_home')), reverse('wiki_documentos'))

    def test_original_inline_download_and_head_headers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Content-Type'],'application/pdf')
        self.assertEqual(response['Content-Length'],str(len(self.content)))
        self.assertTrue(response['Content-Disposition'].startswith('inline;'))
        self.assertEqual(self.body(response),self.content)
        for document in DOCUMENTS:
            response = self.client.get(reverse('wiki_documento_download',args=[document['slug']]))
            self.addCleanup(response.close)
            self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
            self.assertEqual(self.body(response),self.content)
        response = self.client.head(self.url,HTTP_RANGE='bytes=0-9')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,b'')
        self.assertEqual(response['Content-Length'],str(len(self.content)))

    def test_partial_open_ended_and_suffix_ranges(self):
        for header,expected in (('bytes=0-9',self.content[:10]),('bytes=9-',self.content[9:]),
                                ('bytes=-20',self.content[-20:]),('bytes=0-999999',self.content)):
            with self.subTest(range=header):
                response = self.client.get(self.url,HTTP_RANGE=header)
                self.assertEqual(response.status_code,206)
                self.assertEqual(response['Accept-Ranges'],'bytes')
                self.assertEqual(int(response['Content-Length']),len(expected))
                self.assertEqual(self.body(response),expected)

    def test_unsatisfiable_and_invalid_ranges(self):
        for header in ('bytes=999999-','bytes=10-2','bytes=-0','bytes=-','bytes=a-b','bytes=0-1,4-5'):
            with self.subTest(range=header):
                response = self.client.get(self.url,HTTP_RANGE=header)
                self.assertEqual(response.status_code,416)
                self.assertEqual(response['Content-Range'],f'bytes */{len(self.content)}')

    def test_cache_validators_and_if_range(self):
        head = self.client.head(self.url)
        for header in (head['ETag'],'W/'+head['ETag'],'*'):
            self.assertEqual(self.client.get(self.url,HTTP_IF_NONE_MATCH=header).status_code,304)
        self.assertEqual(self.client.get(self.url,HTTP_IF_MODIFIED_SINCE=head['Last-Modified']).status_code,304)
        response = self.client.get(self.url,HTTP_RANGE='bytes=0-9',HTTP_IF_RANGE=head['ETag'])
        self.assertEqual(response.status_code,206)
        self.body(response)
        response = self.client.get(self.url,HTTP_RANGE='bytes=0-9',HTTP_IF_RANGE='"stale"')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.body(response),self.content)

    def test_unknown_or_missing_documents_return_404(self):
        self.assertEqual(self.client.get(reverse('wiki_documento_arquivo',args=['unknown'])).status_code,404)
        self.assertEqual(self.client.get('/wiki/documentos/%2e%2e/arquivo.pdf').status_code,404)
        (Path(self.directory.name)/DOCUMENTS[0]['filename']).unlink()
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(self.client.get(reverse('wiki_documento_leitor',args=[DOCUMENTS[0]['slug']])).status_code,404)
        self.assertContains(self.client.get(reverse('wiki_documentos')),'Documento temporariamente indisponível.')

    def test_document_endpoints_are_read_only(self):
        for name,args in (('wiki_documentos',[]),('wiki_documento_leitor',[DOCUMENTS[0]['slug']]),
                          ('wiki_documento_arquivo',[DOCUMENTS[0]['slug']]),('wiki_documento_download',[DOCUMENTS[0]['slug']])):
            self.assertEqual(self.client.post(reverse(name,args=args)).status_code,405)
