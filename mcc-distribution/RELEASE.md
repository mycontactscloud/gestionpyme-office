Independent WOPI document editor maintained by Software GestiónPYME.

Built from Collabora Online cp-26.04.6-1 (febe91b27107ff458ddb8dcdf8c0c6d521483033).
The complete corresponding source, including the engine and distribution changes,
is available in this release's source archives and tagged repository tree.

The engine, browser and server are compiled from source. No code-brand package,
proprietary theme or Collabora logo is added. Original attribution and component
licenses are retained; distribution changes to MPL files remain MPL-2.0.

The workflow checks capabilities, WOPI discovery and Writer-to-PDF rendering before
publishing the image. Deployment-specific WOPI authorization is configured separately.
This independent distribution is not endorsed or supported by Collabora.

This packaging revision reuses the engine, browser and server compiled from
source in gp-26.04.6.1-4 (9dafcdea7332fc0999fee071a36031ac5c0d20e2).
The packaging workflow verifies that their source files are unchanged, adds
servable .txt filenames for the original license notices, and updates the
source/branding metadata. Its manifest records both source revisions and the
verified base image ID. Complete source archives include the same pinned
language modules and external source tarballs.

Revision gp-26.04.6.1-6 adds a source-published standalone-window extension to
the branding JavaScript. After the editor completes its normal UI_Close action,
it closes the script-opened window. Embedded frames and native editor shells
retain their host-controlled behavior. Manually opened tabs that cannot be
closed by script display instructions instead of a blank document area.
The compiled engine/browser/server files are unchanged; this extension is
distributed in its readable preferred source form and bundled by prepare-branding.py.

Exact Ubuntu sources for the unchanged base packages are available in
gp-26.04.6.1-5: https://github.com/mycontactscloud/gestionpyme-office/releases/tag/gp-26.04.6.1-5
Use its Ubuntu source archive, inventory, manifest and UBUNTU-SHA256SUMS.

Revision gp-26.04.6.1-9 supplies the six contextual paragraph labels
(Above, Before, Below, After, Line Spacing and First) to the svx gettext catalogs
for es, ca, gl, de, fr, it, pt and pt_BR. The already translated German and
French catalogs remain byte-identical; six other catalogs receive 36 new entries.
Labels include their original colon
and context identifiers; unrelated strings and plural forms are preserved.
paragraph-translations.json is the preferred source of the additions, and
patch-translations.py reproduces the updated catalogs from the pinned base.
Only translation resources and source metadata change; no engine, browser
bundle or server binary is recompiled. translation-manifest.json records each
original and resulting catalog hash. The standalone-window extension is retained.

Revision 8 was withdrawn from production after native localized document loading
failed: its hashless MO catalogs passed Python gettext checks but triggered an
unavailable encoding-conversion path in the engine's Boost.Locale reader.
Revision 9 includes the GNU gettext hash table required for native UTF-8 lookup.
Regression checks cover contextual and plural hash lookups. Before publication,
the real engine loads and renders a synthetic ODT with each of en-US, es, ca, gl,
de, fr, it, pt and pt-BR explicitly requested through the conversion endpoint.
No account language is changed. The engine, browser and server remain unchanged.

Revision gp-26.04.6.1-10 changes the Spanish introductory tour title from
"Le damos la bienvenida a Collabora Office" to "Está en GestiónPYME Office".
welcome-translations.json and patch-welcome.py supply the exact browser catalog
entry; all other translations, the tour behavior and original copyright and
license notices are retained. The packaged resource is fetched and checked by
the smoke test, and welcome-manifest.json records its original and final hashes.
No engine, browser bundle or server binary is recompiled.

Revision gp-26.04.6.1-11 translates all 12 onboarding tour steps, buttons and
the accessible step counter for the languages used by MCC: English, Spanish,
Catalan, Galician, German, French, Italian and both Portuguese variants.
The existing Basque editor catalog is covered too. Regional language fallback
is retained, including British English. A small English catalog gives every
English variant the independent product title. Only the English entry in
localizations.json changes; all other locale routes are preserved.

The 30 preferred strings per catalog live in welcome-translations.json.
welcome-originals.json records the reviewed original values, so unexpected
existing translations cause the patch to stop. Existing translated controls
and unrelated catalog entries are preserved. The real upstream l10n.js and
OnboardingSteps.ts are exercised with 23 regional locales before publication.
The packaged server resources and localized native document rendering are
checked independently. The engine, browser bundle and server stay unchanged.
