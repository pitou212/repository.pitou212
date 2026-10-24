# Pitou Kodi repository

Personal Kodi repository (Omega) serving DeadLight, a locally patched Arctic Fuse 3,
and the dependencies the skin needs.

| add-on | source | notes |
|---|---|---|
| `plugin.video.deadlight` | [pitou212/DeadLight](https://github.com/pitou212/DeadLight) | Own add-on (started from Fen Light). Version is set by hand in `addon.xml`; every push to `main` publishes. |
| `skin.arctic.fuse.3` | [pitou212/ArcticFuse3](https://github.com/pitou212/ArcticFuse3), tracking [signde/skin.arctic.fuse.3](https://github.com/signde/skin.arctic.fuse.3) (`omega`) | Upstream's release with a patch layer merged on top: DeadLight info layout and show status, rating rows (incl. an Anime section). The version gets a trailing build number (`72.3.4.8.28`) so Kodi ranks it above upstream's. |
| `repository.pitou212` | this repository (`repository.pitou212/`) | The repository add-on itself. |

## Install

Add this as a file source in Kodi and install the zip from it:

```
https://pitou212.github.io/repository.pitou212/
```

or install the repository zip directly:

```
https://pitou212.github.io/repository.pitou212/omega/zips/repository.pitou212/repository.pitou212-1.0.3.zip
```

## Mirrored dependencies

Kodi installs a missing dependency only from the add-on's own repository or the
official one, so Arctic Fuse 3's dependencies that live elsewhere are also served
here, as unmodified copies: from signde's repository Media Flags, TinyPPI, Skin
Variables, TextureMaker, TMDb Helper, script.module.jurialmunkey,
script.module.infotagger and the Roboto CJK SC font; from jurialmunkey's the Arctic
splash and weather image packs. `tools/mirror_deps.py` keeps them level every six
hours (`.github/workflows/mirror-deps.yml`).

## Licensing

Add-ons here are redistributed under their own licences, with upstream attribution
and credits left intact. Arctic Fuse 3 is CC BY-NC-SA 4.0 — this repository is
non-commercial and shares alike. Nothing here is sold or advertised.

## How the index is built

`tools/make_zip.py` packages an add-on from a git ref and stamps the version
suffix; `tools/repo_build.py` regenerates `addons.xml` and `addons.xml.md5`
together and prunes all but the two newest versions of each add-on. The digest
must always match the file — Kodi silently ignores an entire repository whose md5
disagrees.

The DeadLight and ArcticFuse3 workflows publish by cloning this repository at
depth 1, copying in their zip and running `repo_build.py`; history here is not
needed and was squashed on 2026-10-24.
