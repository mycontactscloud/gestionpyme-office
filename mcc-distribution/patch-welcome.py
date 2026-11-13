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
    parser.add_argument('--template-input', required=True, type=Path)
    parser.add_argument('--template-output', required=True, type=Path)
    args = parser.parse_args()
    changes = json.loads(Path(__file__).with_name('welcome-translations.json').read_text(encoding='utf-8'))
    expected = json.loads(Path(__file__).with_name('welcome-originals.json').read_text(encoding='utf-8'))
    release = json.loads(Path(__file__).with_name('distribution.json').read_text(encoding='utf-8'))['release']
    if not re.fullmatch(r'gp-[A-Za-z0-9.-]+', release):
        raise ValueError('Invalid resource version')
    suffix = '?v=' + release
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
    if index.get('en') is not False and str(index.get('en')).split('?')[0] != route:
        raise ValueError('Unexpected English locale route')
    patched = {**index, 'en': route}
    resources = {entry['resource'] for entry in changes['languages'].values()}
    for locale, value in patched.items():
        if isinstance(value, str) and value.split('?')[0].rsplit('/', 1)[-1] in resources:
            patched[locale] = value.split('?')[0] + suffix
    # Only cache versions may change for existing non-English locale routes.
    assert {k: str(v).split('?')[0] for k, v in index.items() if k != 'en'} == {
        k: str(v).split('?')[0] for k, v in patched.items() if k != 'en'}
    result = (json.dumps(patched, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    (args.output_root / name).write_bytes(result)
    report.append({'file': name, 'before': hashlib.sha256(original).hexdigest(),
                   'after': hashlib.sha256(result).hexdigest(), 'localePathsPreserved': True,
                   'resourceVersion': release})
    # The compiled browser hash stays unchanged in resource-only releases.
    # Version the index reference too, so an already cached index/catalog cannot
    # hide the new translations when a new editor window opens.
    original = args.template_input.read_bytes()
    pattern = rb'(/l10n/localizations\.json)(?:\?v=gp-[A-Za-z0-9.-]+)?(?=["\x27])'
    template, count = re.subn(pattern, lambda m: m[1] + suffix.encode('ascii'), original)
    if count != 1:
        raise ValueError('Expected exactly one UI localization reference in cool.html')
    args.template_output.parent.mkdir(parents=True, exist_ok=True)
    args.template_output.write_bytes(template)
    report.append({'file': 'cool.html', 'before': hashlib.sha256(original).hexdigest(),
                   'after': hashlib.sha256(template).hexdigest(), 'onlyUiCatalogReferenceChanged': True,
                   'resourceVersion': release})
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
