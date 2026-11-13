#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# Copyright Software GestiónPYME, 2026.
"""Add six contextual paragraph labels to existing gettext catalogs; no code compilation."""
import argparse
import gettext
import hashlib
import io
import json
from pathlib import Path
import re
import struct


def read_mo(data):
    if len(data) < 28:
        raise ValueError('Truncated gettext catalog')
    magic = struct.unpack('<I', data[:4])[0]
    if magic not in (0x950412de, 0xde120495):
        raise ValueError('Invalid gettext catalog')
    endian = '<' if magic == 0x950412de else '>'
    _, revision, count, originals, translations, _, _ = struct.unpack(endian + '7I', data[:28])
    if revision != 0:
        raise ValueError('Review unsupported gettext revision')
    messages = {}
    for index in range(count):
        pairs = []
        for table in (originals, translations):
            length, offset = struct.unpack_from(endian + '2I', data, table + index * 8)
            if offset + length >= len(data) or data[offset + length] != 0:
                raise ValueError('Invalid gettext string bounds')
            pairs.append(data[offset:offset + length])
        if pairs[0] in messages:
            raise ValueError('Duplicate gettext key')
        messages[pairs[0]] = pairs[1]
    return messages


def write_mo(messages):
    keys = sorted(messages)
    count = len(keys)
    offset = 28 + 16 * count
    originals, translations = [], []
    originals_data, translations_data = bytearray(), bytearray()
    for key in keys:
        originals.append((len(key), offset + len(originals_data)))
        originals_data.extend(key + b'\0')
    offset += len(originals_data)
    for key in keys:
        value = messages[key]
        translations.append((len(value), offset + len(translations_data)))
        translations_data.extend(value + b'\0')
    # GNU gettext supports a sorted catalog with no hash table.
    header = struct.pack('<7I', 0x950412de, 0, count, 28, 28 + count * 8, 0, 0)
    tables = b''.join(struct.pack('<2I', *item) for item in originals + translations)
    return header + tables + originals_data + translations_data


def patch_catalog(data, additions):
    old = read_mo(data)
    new = dict(old)
    for key, value in additions.items():
        encoded_key, encoded_value = key.encode('utf-8'), value.encode('utf-8')
        if encoded_key in old and old[encoded_key] != encoded_value:
            raise ValueError('Existing translation differs; review before replacing: ' + key)
        new[encoded_key] = encoded_value
    result = data if new == old else write_mo(new)
    parsed = read_mo(result)
    if any(parsed.get(key) != value for key, value in old.items()):
        raise ValueError('An original translation changed')
    # Validate independently using the standard gettext reader, including plurals.
    before = gettext.GNUTranslations(io.BytesIO(data))
    after = gettext.GNUTranslations(io.BytesIO(result))
    if any(after._catalog.get(key) != value for key, value in before._catalog.items()):
        raise ValueError('An original gettext entry changed')
    for key, value in additions.items():
        context, source = key.split('\x04', 1)
        if after.pgettext(context, source) != value:
            raise ValueError('Contextual translation failed: ' + key)
    return result


def additions_for(config, language):
    if not re.fullmatch(r'[a-z]{2}(?:_[A-Z]{2})?', language):
        raise ValueError('Invalid catalog language')
    labels = config['languages'][language]
    if len(labels) != len(config['messages']) or len(labels) != 6:
        raise ValueError('Expected the six paragraph labels')
    result = {}
    for message, translation in zip(config['messages'], labels):
        if not re.fullmatch(r'[a-z]+', message['id']) or not translation or '\x00' in translation:
            raise ValueError('Invalid contextual translation')
        key = config['contextPrefix'] + message['id'] + '\x04' + message['source']
        if key in result:
            raise ValueError('Duplicate paragraph context')
        result[key] = translation
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(Path(__file__).with_name('paragraph-translations.json').read_text(encoding='utf-8'))
    report = []
    for language in config['languages']:
        relative = Path(language) / 'LC_MESSAGES' / 'svx.mo'
        original = (args.input_root / relative).read_bytes()
        result = patch_catalog(original, additions_for(config, language))
        target = args.output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        report.append({'language': language, 'path': relative.as_posix(), 'labels': 6,
                       'addedEntries': len(read_mo(result)) - len(read_mo(original)),
                       'beforeSha256': hashlib.sha256(original).hexdigest(),
                       'afterSha256': hashlib.sha256(result).hexdigest(),
                       'originalEntriesPreserved': True})
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'catalogs': len(report), 'labels': 6 * len(report), 'originalEntriesPreserved': True}))


if __name__ == '__main__':
    main()
