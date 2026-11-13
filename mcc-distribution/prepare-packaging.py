#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Reuse our compiled image only when all compiled source files are unchanged."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    root = Path.cwd()
    config = json.loads((root / 'mcc-distribution/distribution.json').read_text())
    base = json.loads((root / 'mcc-distribution/packaging-base.json').read_text())
    assert config['upstreamCommit'] == base['upstreamCommit']
    run('git', 'fetch', '--depth=1', 'origin', base['sourceCommit'])
    changed = subprocess.check_output(['git', 'diff', '--name-only', base['sourceCommit'], 'HEAD'], text=True).splitlines()
    assert all(p == 'README.md' or p.startswith(('mcc-distribution/', '.github/workflows/')) for p in changed), changed
    folder = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'gestionpyme-office-packaging-base'
    folder.mkdir(parents=True, exist_ok=True)
    url = config['repository'] + '/releases/download/' + base['release'] + '/'

    def download(name):
        assert Path(name).name == name
        destination = folder / name
        with urllib.request.urlopen(url + name, timeout=60) as response, destination.open('wb') as stream:
            shutil.copyfileobj(response, stream, 1 << 20)
        return destination

    manifest = json.loads(download('build-manifest.json').read_text())
    assert manifest['sourceCommit'] == base['sourceCommit'] and manifest['imageId'] == base['imageId']
    assert manifest['version'] == config['version'] and manifest['product'] == config['product']
    checks = {}
    for line in download('SHA256SUMS').read_text().splitlines():
        value, name = line.split(None, 1)
        name = name.lstrip('*')
        assert Path(name).name == name and name.startswith('gestionpyme-office-' + base['release'])
        checks[name] = value
    files = []
    for name, value in checks.items():
        path = download(name)
        assert sha256(path) == value, name
        files.append(path)
    image = next(p for p in files if p.name == 'gestionpyme-office-' + base['release'] + '.tar.zst')
    run('docker', 'image', 'load', '--input', str(image))
    base_image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', base['imageId']]))[0]
    assert base_image['Config']['Labels']['org.opencontainers.image.revision'] == base['sourceCommit']
    source_parts = sorted(p for p in files if '-source.tar.zst' in p.name)
    assert source_parts
    pipe = subprocess.Popen(['cat', *map(str, source_parts)], stdout=subprocess.PIPE)
    try:
        run('tar', '--zstd', '-xf', '-', '--strip-components=1',
            'gestionpyme-office-' + base['release'] + '/engine/external/tarballs', stdin=pipe.stdout)
    finally:
        pipe.stdout.close()
    assert pipe.wait() == 0
    for path in files:
        path.unlink()
    run('git', 'submodule', 'update', '--init', '--depth=1')
    run(sys.executable, 'mcc-distribution/prepare-branding.py')
    target = root / 'mcc-distribution/license-overlay'
    target.mkdir(exist_ok=True)
    for original, name in [('COPYING', 'COPYING.txt'), ('THIRDPARTYLICENSES', 'THIRDPARTYLICENSES.txt'),
                           ('browser/LICENSE', 'BROWSER-LICENSE.txt'),
                           ('mcc-distribution/LICENSE-MPL-2.0.txt', 'LICENSE-MPL-2.0.txt')]:
        shutil.copyfile(root / original, target / name)
    cid = subprocess.check_output(['docker', 'create', base['imageId']], text=True).strip()
    try:
        run('docker', 'cp', cid + ':/opt/collaboraoffice/LICENSE', str(target / 'ENGINE-LICENSE.txt'))
        catalogs = folder / 'engine-catalogs'
        labels = json.loads((root / 'mcc-distribution/paragraph-translations.json').read_text(encoding='utf-8'))
        for language in labels['languages']:
            destination = catalogs / language / 'LC_MESSAGES'
            destination.mkdir(parents=True, exist_ok=True)
            run('docker', 'cp', cid + ':/opt/collaboraoffice/program/resource/' + language + '/LC_MESSAGES/svx.mo', str(destination / 'svx.mo'))
        browser_catalogs = folder / 'browser-catalogs'
        browser_catalogs.mkdir(exist_ok=True)
        welcome = json.loads((root / 'mcc-distribution/welcome-translations.json').read_text(encoding='utf-8'))
        for name in welcome:
            assert Path(name).name == name
            run('docker', 'cp', cid + ':/usr/share/coolwsd/browser/dist/l10n/' + name, str(browser_catalogs / name))
    finally:
        run('docker', 'rm', cid)
    run(sys.executable, 'mcc-distribution/patch-translations.py', '--input-root', str(catalogs),
        '--output-root', str(root / 'mcc-distribution/translation-overlay'),
        '--manifest', str(root / 'translation-manifest.json'))
    run(sys.executable, 'mcc-distribution/patch-welcome.py', '--input-root', str(browser_catalogs),
        '--output-root', str(root / 'mcc-distribution/browser-translation-overlay'),
        '--manifest', str(root / 'welcome-manifest.json'))
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    run('docker', 'build', '--pull=false', '--build-arg', 'BASE_IMAGE=mycontactscloud/gestionpyme-office:' + base['release'],
        '--label', 'org.opencontainers.image.revision=' + revision,
        '--label', 'org.opencontainers.image.version=' + config['release'],
        '--label', 'io.gestionpyme.compiled-source=' + base['sourceCommit'],
        '-t', 'gestionpyme-office:build', '-f', 'mcc-distribution/Dockerfile.packaging', 'mcc-distribution')
    print(json.dumps({'packagingRevision': revision, 'compiledSourceCommit': base['sourceCommit'],
                      'baseImageId': base['imageId'], 'compiledSourceFilesChanged': False}), flush=True)


if __name__ == '__main__':
    main()
