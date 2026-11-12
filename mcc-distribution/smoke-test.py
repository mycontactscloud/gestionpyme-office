#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Check capabilities, discovery and a real Writer-to-PDF conversion."""
import io
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
    sample = io.BytesIO()
    with zipfile.ZipFile(sample, 'w') as archive:
        archive.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
        archive.writestr('META-INF/manifest.xml', '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/></manifest:manifest>')
        archive.writestr('content.xml', '<?xml version="1.0"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2"><office:body><office:text><text:p>GestionPYME Office rendering validation</text:p></office:text></office:body></office:document-content>')
    Path('/tmp/office-validation.odt').write_bytes(sample.getvalue())
    subprocess.run(['curl', '--fail', '--max-time', '90', '-F', 'data=@/tmp/office-validation.odt',
                    'http://127.0.0.1:9980/cool/convert-to/pdf', '-o', '/tmp/office-validation.pdf'], check=True)
    text = subprocess.check_output(['pdftotext', '/tmp/office-validation.pdf', '-'], text=True)
    assert 'GestionPYME Office rendering validation' in text, text
    print(json.dumps({'capabilities': result, 'discovery': 'ok', 'writerToPdf': 'ok'}))
finally:
    subprocess.run(['docker', 'logs', '--tail', '50', 'office-smoke'])
    subprocess.run(['docker', 'stop', 'office-smoke'])
