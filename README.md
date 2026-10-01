# Pitou Kodi repository

Personal Kodi repository serving locally patched builds of third-party add-ons.

Each build is **upstream's own release with a small patch layer merged on top**.
The version carries a trailing `.1` so Kodi ranks it above the unpatched upstream
release of the same base version.

| add-on | upstream source | patch layer |
|---|---|---|
| `skin.arctic.fuse.3` | [signde/skin.arctic.fuse.3](https://github.com/signde/skin.arctic.fuse.3) (`omega`) | Fen Light OMDb fallback rating chips; Otaku MAL/AniList rating chip |
| `script.module.magneto` | [kodiyashimaru/repo](https://github.com/kodiyashimaru/repo) | anime cour matching, AnimeTosho + SeaDex providers, Kitsu query paths |

## Install

Add this as a repository in Kodi, then install add-ons from it normally:

```
https://pitou212.github.io/repository.pitou212/omega/zips/repository.pitou212/repository.pitou212-1.0.3.zip
```

## Mirrored dependencies

Kodi installs a missing dependency only from the add-on's own repository or the
official one, so Arctic Fuse 3's dependencies that live in signde's repository are
also served here, as unmodified copies: signde Media Flags, TinyPPI, Skin Variables,
TextureMaker, TMDb Helper, script.module.jurialmunkey, script.module.infotagger and
the Roboto CJK SC font. `tools/mirror_deps.py` keeps them level with signde's
repository every six hours (`.github/workflows/mirror-deps.yml`).

## Licensing

Add-ons here are redistributed under their own licences, with upstream attribution
and credits left intact. Arctic Fuse 3 is CC BY-NC-SA 4.0 — this repository is
non-commercial and shares alike. Nothing here is sold or advertised.

## How the index is built

`tools/make_zip.py` packages an add-on from a git ref and stamps the version
suffix; `tools/repo_build.py` regenerates `addons.xml` and `addons.xml.md5`
together and prunes old versions. The digest must always match the file — Kodi
silently ignores an entire repository whose md5 disagrees.
