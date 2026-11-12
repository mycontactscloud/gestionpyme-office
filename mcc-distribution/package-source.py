#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Archive preferred source forms, pinned language modules and fetched source tarballs."""
import json
from pathlib import Path
import subprocess
import tarfile

config = json.loads(Path('mcc-distribution/distribution.json').read_text())
release = config['release']
prefix = 'gestionpyme-office-' + release + '/'
destination = Path('gestionpyme-office-' + release + '-source.tar.zst')
with destination.open('wb') as stream:
    compressor = subprocess.Popen(['zstd', '-T0', '-6'], stdin=subprocess.PIPE, stdout=stream)
    with tarfile.open(fileobj=compressor.stdin, mode='w|') as output:
        for folder in ['.'] + [module['path'] for module in config['modules']]:
            subprefix = prefix if folder == '.' else prefix + folder + '/'
            archive = subprocess.Popen(['git', '-C', folder, 'archive', '--format=tar',
                                        '--prefix=' + subprefix, 'HEAD'], stdout=subprocess.PIPE)
            with tarfile.open(fileobj=archive.stdout, mode='r|') as source:
                for member in source:
                    output.addfile(member, source.extractfile(member) if member.isfile() else None)
            if archive.wait():
                raise RuntimeError('git archive failed: ' + folder)
        cache = Path('engine/external/tarballs')
        if cache.exists():
            output.add(cache, arcname=prefix + 'engine/external/tarballs', recursive=True)
    compressor.stdin.close()
    if compressor.wait():
        raise RuntimeError('Source compression failed')
print(destination, destination.stat().st_size)
if destination.stat().st_size >= 2_000_000_000:
    raise RuntimeError('Source archive exceeds the release asset limit; split it before publishing')
