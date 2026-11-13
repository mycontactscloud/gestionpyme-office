#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Translate the complete tour using browser catalogs, without changing compiled code."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root', required=True, type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    changes = json.loads(Path(__file__).with_name('welcome-translations.json').read_text(encoding='utf-8'))
    expected = json.loads(Path(__file__).with_name('welcome-originals.json').read_text(encoding='utf-8'))
    messages = changes['messages']
    if len(messages) != len(set(messages)):
        raise ValueError('Duplicate tour messages')
    report = []
    args.output_root.mkdir(parents=True, exist_ok=True)
    for locale, entry in changes['languages'].items():
        name = entry['resource']
        if Path(name).name != name or not name.startswith('ui-') or not name.endswith('.json'):
            raise ValueError('Invalid browser resource: ' + name)
        translations = changes['languages'][entry['sameAs']]['translations'] if 'sameAs' in entry else entry['translations']
        if len(messages) != len(translations):
            raise ValueError('Incomplete tour: ' + locale)
        source = args.input_root / name
        original = source.read_bytes() if source.exists() else b'{}'
        if not source.exists() and not entry.get('create'):
            raise ValueError('Missing original catalog: ' + name)
        catalog = json.loads(original)
        patched = dict(catalog)
        for message, translation in zip(messages, translations):
            allowed = expected.get(name, {}).get(message)
            allowed = allowed if isinstance(allowed, list) else [allowed]
            if catalog.get(message) not in [*allowed, translation]:
                raise ValueError('Unexpected translation in ' + name + ': ' + message)
            if not isinstance(translation, str) or not translation.strip():
                raise ValueError('Empty translation in ' + name + ': ' + message)
            if Counter(re.findall(r'%\d+', message)) != Counter(re.findall(r'%\d+', translation)):
                raise ValueError('Placeholder mismatch in ' + name + ': ' + message)
            patched[message] = translation
        assert {k: v for k, v in patched.items() if k not in messages} == {
            k: v for k, v in catalog.items() if k not in messages}
        result = (json.dumps(patched, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        (args.output_root / name).write_bytes(result)
        report.append({'file': name, 'locale': locale, 'messages': len(messages), 'title': translations[0],
                       'before': hashlib.sha256(original).hexdigest(), 'after': hashlib.sha256(result).hexdigest(),
                       'otherTranslationsUnchanged': True})
    # l10n.js normally uses source strings for English. A small English catalog
    # also brands the title for en-US and every regional English fallback.
    name = 'localizations.json'
    original = (args.input_root / name).read_bytes()
    index = json.loads(original)
    route = '%SERVICE_ROOT%/browser/%VERSION%/l10n/' + changes['languages']['en']['resource']
    if index.get('en') not in (False, route):
        raise ValueError('Unexpected English locale route')
    patched = {**index, 'en': route}
    assert {k: v for k, v in index.items() if k != 'en'} == {k: v for k, v in patched.items() if k != 'en'}
    result = (json.dumps(patched, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    (args.output_root / name).write_bytes(result)
    report.append({'file': name, 'before': hashlib.sha256(original).hexdigest(),
                   'after': hashlib.sha256(result).hexdigest(), 'onlyEnglishRouteChanged': True})
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
