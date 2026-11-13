#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Generate only our own assets; never download or use code-brand."""
import html
import json
from pathlib import Path

folder = Path(__file__).resolve().parent
config = json.loads((folder / 'distribution.json').read_text())
brand = folder / 'branding' / 'browser'
brand.mkdir(parents=True, exist_ok=True)
source = config['repository'] + '/tree/' + config['release']
(brand / 'branding.js').write_text(
    '// SPDX-License-Identifier: MPL-2.0\n'
    'var brandProductName = ' + json.dumps(config['product']) + ';\n'
    'var brandProductURL = ' + json.dumps(source) + ';\n'
    'var brandProductFAQURL = ' + json.dumps(source) + ';\n', encoding='utf-8')
(brand / 'branding.css').write_text(
    '/* SPDX-License-Identifier: MPL-2.0 */\n'
    '#document-logo { background-image: none; background-color: #123e55; border-radius: 6px; }\n'
    '#document-logo::after { content: "GP"; color: #fff; font: bold 15px sans-serif; padding: 6px; }\n', encoding='utf-8')
name = html.escape(config['product'])
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">'
       '<!-- SPDX-License-Identifier: MPL-2.0; Software GestiónPYME, 2026 -->'
       '<rect width="800" height="400" rx="24" fill="#123e55"/>'
       '<path d="M90 80h100l50 50v190H90z M190 80v50h50" fill="none" stroke="#fff" stroke-width="10"/>'
       '<path d="M120 180h90m-90 40h90m-90 40h65" stroke="#67d6b9" stroke-width="10"/>'
       '<text x="290" y="195" fill="#fff" font-family="Liberation Sans,sans-serif" font-size="40">'
       + name + '</text><text x="290" y="245" fill="#b9ddd8" font-family="Liberation Sans,sans-serif" '
       'font-size="23">WOPI document editor</text></svg>')
(folder / 'branding' / 'office.svg').write_text(svg, encoding='utf-8')
# browser/Makefile.am requires this directory and this exact toolbar filename.
# Supply our own images before starting the expensive engine compilation.
(brand / 'images').mkdir(parents=True, exist_ok=True)
(brand / 'images' / 'toolbar-bg-logo.svg').write_text(svg, encoding='utf-8')
(brand / 'images' / 'collabora-office-white.svg').write_text(svg, encoding='utf-8')
(folder / 'licenses.html').write_text('''<!DOCTYPE html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Source code and licenses</title><main><h1>''' + name + ''' — source code and licenses</h1>
<p>Independent distribution maintained by Software GestiónPYME, based on Collabora Online.
Copyright the Collabora Online contributors and other upstream authors. This distribution is not endorsed by Collabora.</p>
<p>Open-source components retain their respective licenses. Changes to MPL-covered files are available under MPL 2.0.
No proprietary code-brand package is included.</p>
<ul><li><a href="''' + html.escape(source) + '''">Complete source code and distribution changes</a></li>
<li><a href="licenses/LICENSE-MPL-2.0.txt">Mozilla Public License 2.0</a></li>
<li><a href="licenses/THIRDPARTYLICENSES.txt">Third-party notices</a></li>
<li><a href="licenses/BROWSER-LICENSE.txt">Browser components license</a></li>
<li><a href="licenses/ENGINE-LICENSE.txt">Engine and bundled components notices</a></li></ul>
<p lang="es">Distribución independiente mantenida por Software GestiónPYME, basada en Collabora Online.
El código fuente completo, los cambios y las licencias están disponibles en los enlaces anteriores.</p></main></html>
''', encoding='utf-8')
