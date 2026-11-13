#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
import gettext
import importlib.util
import io
import json
from pathlib import Path
import struct
import unittest

folder = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('paragraph_patch', folder / 'patch-translations.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
config = json.loads((folder / 'paragraph-translations.json').read_text(encoding='utf-8'))


class ParagraphCatalogTests(unittest.TestCase):
    def base(self):
        return patch.write_mo({
            b'': b'Content-Type: text/plain; charset=UTF-8\nPlural-Forms: nplurals=2; plural=(n != 1);\n',
            b'other-context\x04First:': 'Traducción de otro contexto'.encode(),
            b'item\x00items': 'artículo\x00artículos'.encode(),
            b'Original': 'Tradución café'.encode(),
        })

    def test_all_locales_contexts_and_original_plural_entries(self):
        self.assertEqual(set(config['languages']), {'es', 'ca', 'gl', 'de', 'fr', 'it', 'pt', 'pt_BR'})
        for language in config['languages']:
            with self.subTest(language=language):
                additions = patch.additions_for(config, language)
                self.assertEqual(len(additions), 6)
                before = self.base()
                after = patch.patch_catalog(before, additions)
                translations = gettext.GNUTranslations(io.BytesIO(after))
                for key, value in additions.items():
                    context, source = key.split('\x04', 1)
                    self.assertEqual(translations.pgettext(context, source), value)
                    self.assertNotEqual(source, value)
                self.assertEqual(translations.pgettext('other-context', 'First:'), 'Traducción de otro contexto')
                self.assertEqual(translations.gettext('Original'), 'Tradución café')
                self.assertEqual(translations.ngettext('item', 'items', 1), 'artículo')
                self.assertEqual(translations.ngettext('item', 'items', 2), 'artículos')
                self.assertEqual(patch.patch_catalog(after, additions), after)

    def test_conflicting_upstream_translation_requires_review(self):
        additions = patch.additions_for(config, 'es')
        original = patch.read_mo(self.base())
        key = next(iter(additions))
        original[key.encode()] = b'Existing translation'
        with self.assertRaises(ValueError):
            patch.patch_catalog(patch.write_mo(original), additions)

    def test_invalid_catalog_and_language_are_rejected(self):
        with self.assertRaises(ValueError):
            patch.patch_catalog(b'not a catalog', {})
        broken = bytearray(self.base())
        struct.pack_into('<I', broken, 12, len(broken) + 100)
        with self.assertRaises((ValueError, struct.error)):
            patch.read_mo(bytes(broken))
        with self.assertRaises(ValueError):
            patch.additions_for(config, '../es')


if __name__ == '__main__':
    unittest.main()
