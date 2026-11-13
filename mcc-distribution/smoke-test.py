#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check capabilities, discovery and a real Writer-to-PDF conversion."""
import io
import gettext
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import zipfile

config = json.loads(Path('mcc-distribution/distribution.json').read_text())
subprocess.run(['docker', 'run', '-d', '--name', 'office-smoke', '--cap-add', 'SYS_ADMIN',
                '--security-opt', 'seccomp=unconfined', '--shm-size=512m',
                '-p', '127.0.0.1:9980:9980', '-e', 'DONT_GEN_SSL_CERT=1',
                '-e', 'extra_params=--o:ssl.enable=false --o:ssl.termination=true',
                'gestionpyme-office:build'], check=True)
try:
    labels = json.loads(Path('mcc-distribution/paragraph-translations.json').read_text(encoding='utf-8'))
    for language, values in labels['languages'].items():
        path = '/opt/collaboraoffice/program/resource/' + language + '/LC_MESSAGES/svx.mo'
        catalog = gettext.GNUTranslations(io.BytesIO(subprocess.check_output(['docker', 'exec', 'office-smoke', 'cat', path])))
        for message, translation in zip(labels['messages'], values):
            assert catalog.pgettext(labels['contextPrefix'] + message['id'], message['source']) == translation, (language, message)
    for attempt in range(60):
        try:
            with urllib.request.urlopen('http://127.0.0.1:9980/hosting/capabilities', timeout=5) as r:
                result = json.load(r)
            assert result['productVersion'] == config['version'], result
            break
        except Exception:
            if attempt == 59:
                raise
            time.sleep(2)
    with urllib.request.urlopen('http://127.0.0.1:9980/hosting/discovery', timeout=10) as r:
        assert b'<wopi-discovery>' in r.read()
    browser = 'http://127.0.0.1:9980/browser/' + result['productVersionHash'] + '/'
    with urllib.request.urlopen(browser + 'branding.js', timeout=10) as r:
        assert config['release'].encode() in r.read()
    with urllib.request.urlopen(browser + 'licenses.html', timeout=10) as r:
        assert config['release'].encode() in r.read()
    for filename in ['LICENSE-MPL-2.0.txt', 'THIRDPARTYLICENSES.txt', 'BROWSER-LICENSE.txt', 'ENGINE-LICENSE.txt']:
        with urllib.request.urlopen(browser + 'licenses/' + filename, timeout=10) as r:
            assert len(r.read()) > 100, filename
    sample = io.BytesIO()
    with zipfile.ZipFile(sample, 'w') as archive:
        archive.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
        archive.writestr('META-INF/manifest.xml', '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/></manifest:manifest>')
        archive.writestr('content.xml', '<?xml version="1.0"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2"><office:body><office:text><text:p>GestionPYME Office rendering validation</text:p></office:text></office:body></office:document-content>')
    Path('/tmp/office-validation.odt').write_bytes(sample.getvalue())
    rendered_languages = []
    for language in ['en-US', 'es', 'ca', 'gl', 'de', 'fr', 'it', 'pt', 'pt-BR']:
        subprocess.run(['curl', '--fail', '--max-time', '60', '-F', 'data=@/tmp/office-validation.odt',
                        '-F', 'lang=' + language,
                        'http://127.0.0.1:9980/cool/convert-to/pdf', '-o', '/tmp/office-validation.pdf'], check=True)
        text = subprocess.check_output(['pdftotext', '/tmp/office-validation.pdf', '-'], text=True)
        assert 'GestionPYME Office rendering validation' in text, (language, text)
        rendered_languages.append(language)
    package = subprocess.run(['docker', 'exec', 'office-smoke', 'dpkg-query', '-W',
                              '-f=${db:Status-Status}', 'code-brand'], capture_output=True, text=True)
    assert package.returncode == 1 and not package.stdout.strip()
    for attempt in range(30):
        state = json.loads(subprocess.check_output(['docker', 'inspect', 'office-smoke']))[0]['State']
        if state.get('Health', {}).get('Status') == 'healthy':
            break
        if attempt == 29:
            raise RuntimeError('Docker healthcheck did not become healthy')
        time.sleep(3)
    print(json.dumps({'capabilities': result, 'discovery': 'ok', 'writerToPdf': 'ok', 'renderedLanguages': rendered_languages}))
finally:
    subprocess.run(['docker', 'logs', '--tail', '50', 'office-smoke'])
    subprocess.run(['docker', 'stop', 'office-smoke'])
