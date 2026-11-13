# GestiónPYME Office

Independent WOPI document editor maintained by Software GestiónPYME, based on
Collabora Online **26.04.6.1**. This is a source distribution and build project;
it does not contain the My Contacts Cloud application or its data.

The complete upstream source, including the rendering engine under `engine/`,
is retained in this repository. The base is upstream tag `cp-26.04.6-1`, commit
`febe91b27107ff458ddb8dcdf8c0c6d521483033`.

## Distribution changes

- Compile the engine, server and browser from source; do not install `code-brand`
  or download Collabora's proprietary branding repository.
- Use our own product name, vendor, logo and browser theme.
- Add the corresponding-source link to the browser's About dialog while
  retaining the upstream copyright and license notices.
- Build and test a Docker image using the manual GitHub Actions workflow.
- Publish a tagged source tree, image archive, checksum and build manifest after
  capabilities, discovery and document-rendering checks pass.

See [build configuration](mcc-distribution/distribution.json),
[build script](mcc-distribution/build.sh),
[runtime Dockerfile](mcc-distribution/Dockerfile) and
[workflow](.github/workflows/gestionpyme-office.yml).

Use `git clone --recurse-submodules` to obtain the pinned translations and
dictionaries too. The release's custom `-source.tar.zst` asset includes these
modules and the source tarballs fetched during the build; GitHub's automatic
source archives omit submodule contents. Large source archives are published as
numbered `.part001`, `.part002` assets. Download all parts and `SHA256SUMS`, run
`sha256sum -c SHA256SUMS`, then concatenate the parts in order before extracting:

```sh
cat gestionpyme-office-*-source.tar.zst.part* > source.tar.zst
tar --zstd -xf source.tar.zst
```

## License and attribution

Copyright the Collabora Online contributors and other upstream authors.
Distribution additions and modifications by Software GestiónPYME, 2026, are
available under **MPL-2.0**. Existing files and dependencies retain their licenses,
including the notices in [COPYING](COPYING), [THIRDPARTYLICENSES](THIRDPARTYLICENSES),
[browser/LICENSE](browser/LICENSE) and the engine's license files.

The `code-brand` binary package and its proprietary themes are not used in this
build. Original open-source notices are preserved. The GestiónPYME name and
marks identify this independent distribution; source availability does not grant
trademark rights. Collabora's trademarks remain their owners' property.
This distribution is not endorsed or supported by Collabora.

## Packaging-only revisions

Revision gp-26.04.6.1-5 repairs two license-resource filenames over our previously
source-compiled gp-26.04.6.1-4 image. It retains the compiled code from
9dafcdea7332fc0999fee071a36031ac5c0d20e2 and publishes the packaging changes and
complete source again. The manifest records the compiled source, packaging
source and base image separately. The compiled About dialog retains its exact
compiled-source link; the branding and license page link to the packaging source.

The separate packaging workflow rejects any change to compiled source files or
the upstream source pin. Use the full build workflow for engine, browser or
server code changes. Both workflows verify all public license resources before
publishing an immutable image and source release.

Original project documentation: [upstream README](mcc-distribution/UPSTREAM-README.md).

Revision gp-26.04.6.1-6 additionally bundles the readable, MPL-2.0
`mcc-distribution/standalone-window.js` extension through the branding generator.
It listens to the editor's internal UI_Close event in standalone browser windows
and closes them after normal document teardown. It does not close embedded
frames or native editor shells. Its focused regression checks run in the
packaging workflow; the compiled engine/browser/server remain unchanged.

Revision gp-26.04.6.1-8 supplies missing paragraph labels through the engine's
existing gettext catalogs, without recompiling the engine or browser. The
preferred additions are in mcc-distribution/paragraph-translations.json;
patch-translations.py applies them contextually and preserves all original
entries and plural forms. The packaged catalogs and every locale are checked
independently with Python's gettext reader. No DOM text replacement is used.
Existing German and French translations and their catalog bytes are preserved.
The preliminary revision 7 stopped before image publication when its guard
detected those existing translations; its source tag remains immutable.

Revision gp-26.04.6.1-10 customizes the Spanish introductory tour title through
the existing ui-es.json catalog: "Está en GestiónPYME Office". The preferred
translation is in mcc-distribution/welcome-translations.json and is applied by
patch-welcome.py in both build workflows. Other translations and the tour's
behavior are preserved. This packaging revision does not recompile the engine,
browser bundle or server, and retains the revision 9 paragraph catalog fix.

Revision gp-26.04.6.1-11 extends the resource-based localization to the complete
tour in every MCC language, both Portuguese variants, British English and the
existing Basque catalog. All 12 steps and the controls are checked against the
real upstream localization loader with regional fallbacks. Original component
attribution and unrelated translations remain intact. No compiled code changes.

Revision gp-26.04.6.1-12 includes the Show Tour menu entry and versions the
translation-resource URLs in the installed HTML template and localization index.
This allows previously cached editor sessions to see the updated translations
when a new editor window opens, while retaining the compiled browser hash.
