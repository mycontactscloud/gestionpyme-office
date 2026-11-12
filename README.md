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

Original project documentation: [upstream README](mcc-distribution/UPSTREAM-README.md).
