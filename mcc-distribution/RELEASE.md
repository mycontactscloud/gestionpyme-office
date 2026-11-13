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
