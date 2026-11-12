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
if destination.stat().st_size >= 1_800_000_000:
    # GitHub limits individual release assets. Preserve the exact compressed
    # stream in numbered parts; concatenation restores the original archive.
    parts = []
    with destination.open('rb') as source:
        index = 1
        while block := source.read(16 << 20):
            part = destination.with_name(destination.name + '.part' + str(index).zfill(3))
            with part.open('wb') as target:
                size = 0
                while block:
                    target.write(block)
                    size += len(block)
                    if size >= 1_792_000_000:
                        break
                    block = source.read(16 << 20)
            parts.append(part)
            index += 1
    if sum(p.stat().st_size for p in parts) != destination.stat().st_size:
        raise RuntimeError('Incomplete source archive parts')
    destination.unlink()
    for part in parts:
        print(part, part.stat().st_size)
