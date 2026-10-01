"""Copy the dependencies our add-ons need into this repository.

Since Kodi 20 a missing dependency is looked up only in the repository the add-on
came from, then in the official Kodi repository -- never in any other repository
the user has installed. Our Arctic Fuse 3 needs eight add-ons that exist only in
signde's (and jurialmunkey's) repositories, so installing or updating it from here
failed with "failed to find dependency resource.images.mediaflags.signde" on
2026-10-01 even with repository.signde installed. signde's repository hosts all of
them for its own AF3; this mirrors exactly those packages, unmodified.

Run before tools/repo_build.py, which indexes whatever zips are present:

    python tools/mirror_deps.py [--root docs/omega/zips]

A mirrored add-on installed from here updates from here only, so this must keep
running (see .github/workflows/mirror-deps.yml). Only ever adds the source's newest
version; repo_build.py prunes the old ones.
"""
import argparse, io, os, re, sys, urllib.request, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_build import safe_parse, version_key

# The URLs repository.signde's own addon.xml declares for Kodi 21 (omega).
SOURCES = {
    'signde': {
        'index': 'https://signde.github.io/repository.signde/addons/omega/addons.xml',
        'datadir': 'https://signde.github.io/repository.signde/addons/zips/',
    },
}

# Every add-on skin.arctic.fuse.3 needs, directly or through another dependency,
# that neither this repository nor the official one can supply at the version
# required. script.module.pil also has no repository source but ships with Kodi.
# Re-derive this list whenever AF3's <requires> changes.
MIRROR = {
    'resource.images.mediaflags.signde': 'signde',
    'script.signde.tinyppi': 'signde',
    'script.skinvariables': 'signde',
    'script.texturemaker': 'signde',
    'plugin.video.themoviedb.helper': 'signde',
    'script.module.jurialmunkey': 'signde',
    'script.module.infotagger': 'signde',
    'resource.font.robotocjksc': 'signde',
}

UA = {'User-Agent': 'Kodi/21 (repository.pitou212 mirror)'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def newest_entries(index_xml):
    """{addon_id: (version, relative zip path)} -- the highest version of each."""
    out = {}
    for a in safe_parse(index_xml, 'source addons.xml').findall('addon'):
        aid, ver = a.get('id'), a.get('version')
        if not aid or not ver:
            continue
        path = None
        for ext in a.findall('extension'):
            p = ext.findtext('path')
            if p:
                path = p.strip()
        path = path or '%s/%s-%s.zip' % (aid, aid, ver)
        if aid not in out or version_key(ver) > version_key(out[aid][0]):
            out[aid] = (ver, path)
    return out


def check_zip(data, aid, ver):
    """The download must be a zip of exactly this add-on and version."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None:
            raise SystemExit('%s %s: corrupt zip' % (aid, ver))
        bad = [n for n in z.namelist() if not n.startswith(aid + '/')]
        if bad:
            raise SystemExit('%s %s: zip holds files outside %s/ (%s)' % (aid, ver, aid, bad[0]))
        root = safe_parse(z.read(aid + '/addon.xml'), '%s addon.xml' % aid)
    if root.get('id') != aid or root.get('version') != ver:
        raise SystemExit('%s %s: zip is %s %s' % (aid, ver, root.get('id'), root.get('version')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.join('docs', 'omega', 'zips'))
    a = ap.parse_args()

    indexes = {name: newest_entries(fetch(src['index'])) for name, src in SOURCES.items()}
    changed = 0
    for aid, source in sorted(MIRROR.items()):
        entry = indexes[source].get(aid)
        if entry is None:
            # Keep what we have rather than failing the whole run: a source that drops
            # an add-on leaves ours serving the last copy, which still installs.
            print('  WARNING %s: no longer in %s; keeping our copy' % (aid, source))
            continue
        ver, rel = entry
        addon_dir = os.path.join(a.root, aid)
        dest = os.path.join(addon_dir, '%s-%s.zip' % (aid, ver))
        if os.path.exists(dest):
            print('  ok %s %s' % (aid, ver))
            continue
        have = [re.fullmatch(re.escape(aid) + r'-(.+)\.zip', f) for f in
                (os.listdir(addon_dir) if os.path.isdir(addon_dir) else [])]
        have = [m.group(1) for m in have if m]
        if any(version_key(h) > version_key(ver) for h in have):
            print('  keep %s: we serve %s, %s has only %s' % (aid, max(have, key=version_key), source, ver))
            continue
        data = fetch(SOURCES[source]['datadir'] + rel)
        check_zip(data, aid, ver)
        os.makedirs(addon_dir, exist_ok=True)
        tmp = dest + '.part'
        with open(tmp, 'wb') as fh:
            fh.write(data)
        os.replace(tmp, dest)
        changed += 1
        print('  mirrored %s %s (%d bytes) from %s' % (aid, ver, len(data), source))
    print('  %d new package(s)' % changed)


if __name__ == '__main__':
    main()
