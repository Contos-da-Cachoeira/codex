"""Renderiza a capa de compartilhamento a partir do símbolo e das cores do site."""
import base64
from pathlib import Path
import re

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'codex/core/static/core/img'


def main():
    symbol = base64.b64encode((ASSETS / 'tesseract.svg').read_bytes()).decode()
    white_svg = (ASSETS / 'tesseract.svg').read_text(encoding='utf-8').replace('fill="#000000"', 'fill="#FFFFFF"')
    white_svg = re.sub(r'<!DOCTYPE[^>]*>\s*', '', white_svg)
    assert 'fill="#FFFFFF"' in white_svg
    (ASSETS / 'favicon-white.svg').write_text(white_svg, encoding='utf-8')
    white_symbol = base64.b64encode(white_svg.encode()).decode()
    html = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><style>
      * { box-sizing: border-box; }
      body { margin: 0; width: 1200px; height: 630px; background: #090b10; color: #ededed; font-family: Arial, sans-serif; }
      main { position: relative; width: 100%; height: 100%; overflow: hidden; padding: 80px; }
      main::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 10px; background: #3a83f7; }
      .orbit { position: absolute; width: 700px; height: 700px; right: -120px; top: -35px; border: 1px solid #24304a; border-radius: 50%; }
      .orbit.inner { width: 520px; height: 520px; right: -30px; top: 55px; }
      .brand { position: relative; z-index: 1; padding-top: 56px; }
      .eyebrow { color: #76aaff; font-size: 20px; font-weight: 700; letter-spacing: 5px; margin: 0 0 20px; }
      h1 { font-size: 108px; letter-spacing: -6px; line-height: 1; margin: 0; }
      .subtitle { margin: 20px 0 0; font-size: 28px; font-weight: 700; letter-spacing: 2px; }
      .lead { margin: 45px 0 0; font-size: 25px; color: #aeb6c5; line-height: 1.5; }
      .symbol { position: absolute; right: 78px; top: 141px; width: 340px; height: 340px; filter: invert(1); }
      .footer { position: absolute; bottom: 57px; font-size: 16px; font-weight: 700; letter-spacing: 3px; color: #76aaff; }
      </style><main><div class="orbit"></div><div class="orbit inner"></div>
      <div class="brand"><p class="eyebrow">VIVA A SUA HISTÓRIA</p><h1>Codex</h1>
      <p class="subtitle">CONTOS DA CACHOEIRA</p><p class="lead">Crie seu personagem.<br>Prepare sua próxima aventura.</p></div>
      <img class="symbol" alt="" src="data:image/svg+xml;base64,SYMBOL">
      <p class="footer">LARP &nbsp;·&nbsp; PERSONAGENS &nbsp;·&nbsp; GUILDAS &nbsp;·&nbsp; WIKI</p></main></html>'''.replace('SYMBOL', symbol)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
        page.set_content(html, wait_until='load')
        page.screenshot(path=str(ASSETS / 'share-card.png'))
        for size, filename in ((32, 'favicon-white-32.png'), (180, 'apple-touch-icon.png')):
            page.set_viewport_size({'width': size, 'height': size})
            page.set_content('''<!doctype html><style>body { margin: 0; background: BACKGROUND; }
                img { display: block; width: 100vw; height: 100vh; padding: 12%; box-sizing: border-box; filter: invert(1); }
                </style><img alt="" src="data:image/svg+xml;base64,SYMBOL">'''
                .replace('BACKGROUND', 'transparent' if size == 32 else '#3a83f7')
                .replace('filter: invert(1);', '' if size == 32 else 'filter: invert(1);')
                .replace('SYMBOL', white_symbol if size == 32 else symbol), wait_until='load')
            page.screenshot(path=str(ASSETS / filename), omit_background=size == 32)
        browser.close()
    print(ASSETS / 'share-card.png')


if __name__ == '__main__':
    main()
