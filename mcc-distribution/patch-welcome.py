#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Change the welcome title through the existing browser translation resource."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root', required=True, type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    changes = json.loads(Path(__file__).with_name('welcome-translations.json').read_text(encoding='utf-8'))
    report = []
    for name, change in changes.items():
        if Path(name).name != name or not name.startswith('ui-') or not name.endswith('.json'):
            raise ValueError('Invalid browser resource: ' + name)
        original = (args.input_root / name).read_bytes()
        catalog = json.loads(original)
        if catalog.get(change['message']) not in (change['original'], change['translation']):
            raise ValueError('Unexpected welcome translation: ' + name)
        patched = {**catalog, change['message']: change['translation']}
        assert {k: v for k, v in patched.items() if k != change['message']} == {
            k: v for k, v in catalog.items() if k != change['message']}
        result = (json.dumps(patched, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / name).write_bytes(result)
        report.append({'file': name, 'message': change['message'], 'translation': change['translation'],
                       'before': hashlib.sha256(original).hexdigest(), 'after': hashlib.sha256(result).hexdigest(),
                       'otherTranslationsUnchanged': True})
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
