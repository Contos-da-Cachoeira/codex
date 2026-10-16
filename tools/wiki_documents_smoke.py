"""Leitura e download dos PDFs reais em navegador com banco SQLite isolado."""
import hashlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'codex'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
import django
django.setup()
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from playwright.sync_api import sync_playwright, expect
from wiki.documents import DOCUMENTS


class WikiDocumentsSmoke(StaticLiveServerTestCase):
    def test_documents_reader_and_download(self):
        output = Path(os.environ['USERPROFILE'])/'Downloads'
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome',headless=True)
            context = browser.new_context(viewport={'width':1500,'height':1100},accept_downloads=True)
            page = context.new_page()
            errors, documents = [], []
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:documents.append(request.url) if request.resource_type=='document' else None)
            page.goto(self.live_server_url+'/wiki/documentos/',wait_until='networkidle')
            expect(page.locator('.wd-document')).to_have_count(2)
            page.screenshot(path=str(output/'codex-wiki-documents-desktop.png'),full_page=True,animations='disabled')
            for index,item in enumerate(DOCUMENTS):
                card = page.locator('.wd-document').nth(index)
                with page.expect_download() as downloaded:
                    card.get_by_role('link',name='Baixar PDF',exact=True).click()
                artifact = downloaded.value
                self.assertEqual(artifact.suggested_filename,item['filename'])
                self.assertEqual(hashlib.sha256(Path(artifact.path()).read_bytes()).digest(),hashlib.sha256((ROOT/'docs'/item['filename']).read_bytes()).digest())
            page.locator('.wd-document').first.get_by_role('link',name='Ler online',exact=True).click()
            reader = page.locator('[data-pdf-reader]')
            expect(reader).to_have_attribute('data-pdf-ready','true',timeout=60000)
            expect(page.locator('[data-pdf-total]')).to_have_text('25')
            expect(reader.locator('.page[data-page-number="1"] canvas')).to_be_visible()
            page.screenshot(path=str(output/'codex-wiki-manual-reader-desktop.png'),full_page=True,animations='disabled')
            documents.clear()
            page.get_by_role('button',name='Próxima página',exact=True).click()
            expect(page.locator('[data-pdf-page]')).to_have_value('2')
            page.locator('[data-pdf-page]').fill('10')
            page.locator('[data-pdf-page]').press('Tab')
            expect(page.locator('[data-pdf-page]')).to_have_value('10')
            page.locator('[data-pdf-zoom]').select_option('1')
            width_at_100 = page.locator('.page[data-page-number="10"]').evaluate('page=>page.getBoundingClientRect().width')
            page.locator('[data-pdf-zoom]').select_option('1.5')
            page.wait_for_function("width=>Math.abs(document.querySelector('.page[data-page-number=\"10\"]').getBoundingClientRect().width-width*1.5)<3",arg=width_at_100)
            page.locator('[data-pdf-zoom]').select_option('page-width')
            page.locator('[data-pdf-search]').fill('talentos')
            expect(page.locator('[data-pdf-find-count]')).to_contain_text('resultados',timeout=30000)
            self.assertEqual(documents,[])
            page.get_by_role('button',name='Tela cheia',exact=True).click()
            page.wait_for_function("document.fullscreenElement?.hasAttribute('data-pdf-reader')")
            page.get_by_role('button',name='Sair da tela cheia',exact=True).click()
            page.wait_for_function('!document.fullscreenElement')
            page.get_by_role('navigation',name='Escolher documento').get_by_role('link',name=DOCUMENTS[1]['title'],exact=True).click()
            expect(reader).to_have_attribute('data-pdf-ready','true',timeout=60000)
            expect(page.locator('[data-pdf-total]')).to_have_text('23')
            page.screenshot(path=str(output/'codex-wiki-scenario-reader-desktop.png'),full_page=True,animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            expect(reader.locator('.page[data-page-number="1"] canvas')).to_be_visible()
            page.screenshot(path=str(output/'codex-wiki-scenario-reader-mobile.png'),full_page=True,animations='disabled')
            page.locator('[data-pdf-page]').fill('23')
            page.locator('[data-pdf-page]').press('Enter')
            expect(page.locator('[data-pdf-page]')).to_have_value('23')
            expect(reader.locator('.page[data-page-number="23"] canvas')).to_be_visible(timeout=30000)
            page.get_by_role('link',name='← Voltar aos documentos',exact=True).click()
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-wiki-documents-mobile.png'),full_page=True,animations='disabled')
            # A worker/module/network failure must offer working original/download links.
            page.route('**/build/pdf.worker.min.js',lambda route:route.abort())
            page.locator('.wd-document').first.get_by_role('link',name='Ler online',exact=True).click()
            expect(reader).to_have_attribute('data-pdf-error','true',timeout=30000)
            expect(page.get_by_role('link',name='Baixar PDF',exact=True)).to_be_visible()
            expect(page.get_by_role('link',name='Abrir PDF em outra aba ↗',exact=True)).to_be_visible()
            self.assertFalse(errors,errors)
            browser.close()
        print('PASS: real original downloads; both PDFs rendered; page navigation/zoom/search/fullscreen without reload; mobile; loading failure fallback.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1,interactive=False).run_tests(['__main__.WikiDocumentsSmoke'])))
