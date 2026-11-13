#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# Copyright Software GestiónPYME, 2026
"""Conservar el inventario y fuentes Ubuntu exactas de una imagen distribuida."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import urllib.parse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--release', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', args.image_id):
        parser.error('ID de imagen no válido')
    if not re.fullmatch(r'gp-[0-9.]+-[0-9]+', args.release):
        parser.error('Release no válida')
    output = Path(args.output).resolve()
    if not output.is_relative_to(Path('/root/collabora-maintenance')):
        parser.error('El destino debe estar bajo /root/collabora-maintenance')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder = output / 'ubuntu-source'
    folder.mkdir(mode=0o700, exist_ok=True)
    os_release = subprocess.check_output(['docker', 'run', '--rm', '--network=none', '--entrypoint',
                                         '/usr/bin/cat', args.image_id, '/etc/os-release'], text=True)
    operating_system = dict(line.split('=', 1) for line in os_release.splitlines() if '=' in line)
    assert operating_system['ID'].strip('"') == 'ubuntu'
    codename = operating_system['VERSION_CODENAME'].strip('"')
    assert re.fullmatch(r'[a-z][a-z0-9]*', codename)
    (folder / 'os-release.txt').write_text(os_release)
    inventory = subprocess.check_output([
        'docker', 'run', '--rm', '--network=none', '--entrypoint', '/usr/bin/dpkg-query',
        args.image_id, '-W', '-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\t${db:Status-Status}\n'],
        text=True)
    (folder / 'packages.tsv').write_text(inventory)
    rows = [line.split('\t') for line in inventory.splitlines() if line]
    sources = sorted({(row[2], row[3]) for row in rows if row[4] == 'installed'})
    for package, version in sources:
        if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*', package) or not re.fullmatch(r'[a-zA-Z0-9.+:~_-]+', version):
            raise RuntimeError('Paquete fuente inesperado')
    selections = [package + '=' + version for package, version in sources]
    # Only an ephemeral container is changed. Production and the image are untouched.
    script = '''set -eu
sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
apt-get update
cd /sources
: > missing-sources.txt
for selection do
  if ! apt-get source --download-only "$selection"; then
    printf '%s\\n' "$selection" >> missing-sources.txt
  fi
done
'''
    run('docker', 'run', '--rm', '--user', '0', '--entrypoint', '/bin/sh',
        '-v', str(folder) + ':/sources:Z',
        args.image_id, '-c', script, 'source-download', *selections)
    provenance = []
    for selection in (folder / 'missing-sources.txt').read_text().splitlines():
        package, version = selection.split('=', 1)
        assert (package, version) in sources
        query = urllib.parse.urlencode({'ws.op': 'getPublishedSources', 'source_name': package,
                    'version': version, 'exact_match': 'true',
                    'distro_series': 'https://api.launchpad.net/1.0/ubuntu/' + codename})
        with urllib.request.urlopen('https://api.launchpad.net/1.0/ubuntu/+archive/primary?' + query, timeout=30) as response:
            publications = json.load(response)['entries']
        publications = [p for p in publications if p['source_package_name'] == package and
                        p['source_package_version'] == version and p['status'] in ('Published', 'Superseded')]
        if not publications:
            raise RuntimeError('No official source publication found for ' + selection)
        publication = max(publications, key=lambda p: p['date_published'])
        parse_time = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        start = parse_time(publication['date_published'])
        end = parse_time(publication['date_superseded']) if publication.get('date_superseded') else datetime.datetime.now(datetime.timezone.utc)
        if end <= start:
            raise RuntimeError('Invalid source publication dates for ' + selection)
        snapshot = (start + min((end - start) / 2, datetime.timedelta(days=1))).strftime('%Y%m%dT%H%M%SZ')
        suite = codename + {'Release': '', 'Updates': '-updates', 'Security': '-security',
                            'Backports': '-backports'}[publication['pocket']]
        stanza = ('Types: deb-src\nURIs: https://snapshot.ubuntu.com/ubuntu/' + snapshot +
                  '/\nSuites: ' + suite + '\nComponents: main restricted universe multiverse\n'
                  'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\nCheck-Valid-Until: no\n')
        snapshot_script = '''set -eu
printf '%s\\n' "$1" > /etc/apt/sources.list.d/ubuntu.sources
shift
apt-get update
cd /sources
apt-get source --download-only "$1"
'''
        print(json.dumps({'source': selection, 'officialSnapshot': snapshot, 'suite': suite}), flush=True)
        run('docker', 'run', '--rm', '--user', '0', '--entrypoint', '/bin/sh',
            '-v', str(folder) + ':/sources:Z', args.image_id, '-c', snapshot_script,
            'snapshot-download', stanza, selection)
        provenance.append({'package': package, 'version': version, 'publication': publication['self_link'],
                           'snapshot': snapshot, 'suite': suite})
    (folder / 'missing-sources.txt').unlink()
    (folder / 'source-provenance.json').write_text(json.dumps(provenance, indent=2))
    (folder / 'README.txt').write_text(
        'Ubuntu package source archives corresponding to the unmodified OS packages in\n'
        'GestiónPYME Office ' + args.release + '.\nImage ID: ' + args.image_id + '\n'
        'packages.tsv columns: binary package, binary version, source package, source\n'
        'version, installed status. Source archives and Debian packaging retain their original\n'
        'licenses and notices. Extract the matching .dsc with dpkg-source -x to obtain\n'
        'the preferred source and original packaging/build instructions. The editor\n'
        'and its bundled engine sources are published in the separate -source archive.\n')
    hashes = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.name != 'SHA256SUMS':
            digest = sha256(path)
            hashes.append(digest + '  ' + path.name)
    (folder / 'SHA256SUMS').write_text('\n'.join(hashes) + '\n')
    destination = output / ('gestionpyme-office-' + args.release + '-ubuntu-source.tar')
    with tarfile.open(destination, 'w') as archive:
        archive.add(folder, arcname='ubuntu-source')
    if destination.stat().st_size >= 1_800_000_000:
        raise RuntimeError('Dividir el archivo antes de publicarlo: supera el límite por asset')
    digest = sha256(destination)
    (output / 'UBUNTU-SHA256SUMS').write_text(digest + '  ' + destination.name + '\n')
    print(json.dumps({'release': args.release, 'imageId': args.image_id,
                      'sourcePackages': len(sources), 'archive': str(destination),
                      'bytes': destination.stat().st_size, 'sha256': digest}), flush=True)


if __name__ == '__main__':
    main()
