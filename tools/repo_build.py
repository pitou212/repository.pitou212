"""Regenerate the Kodi repository index from whatever zips are present.

Kodi fetches addons.xml, then addons.xml.md5, and *silently ignores the entire
repository* if the digest does not match the file. So the two are always written
together here, and never by hand.

Layout produced (mirrors jurialmunkey's own repo, which Kodi is known to accept):

    docs/omega/zips/addons.xml
    docs/omega/zips/addons.xml.md5
    docs/omega/zips/<addon-id>/<addon-id>-<version>.zip
    docs/omega/zips/<addon-id>/addon.xml        <- extracted, for the add-on browser
    docs/omega/zips/<addon-id>/icon.png|fanart.jpg

Usage:  python repo_build.py [--root docs/omega/zips] [--keep 2]
"""
import argparse, hashlib, io, os, re, zipfile
import xml.etree.ElementTree as ET

ARTWORK = ('icon.png', 'fanart.jpg')

# ElementTree resolves internal entities, so a hostile upstream addon.xml could
# stall CI with a billion-laughs expansion. defusedxml is not guaranteed to exist
# on a bare runner, so reject the declarations that make the attack possible
# instead of depending on it. A Kodi addon.xml has no legitimate use for either.
_FORBIDDEN = (b'<!DOCTYPE', b'<!ENTITY')


def safe_parse(data, what):
    upper = data.upper()
    for tok in _FORBIDDEN:
        if tok in upper:
            raise SystemExit('%s contains %s - refusing to parse'
                             % (what, tok.decode()))
    return ET.fromstring(data)


def version_key(v):
    """Sort add-on versions the way Kodi compares them: numerically, part by part."""
    return [int(p) if p.isdigit() else p for p in re.split(r'[._-]', v)]


def zips_for(addon_dir, addon_id):
    out = []
    for f in os.listdir(addon_dir):
        m = re.fullmatch(re.escape(addon_id) + r'-(.+)\.zip', f)
        if m:
            out.append((m.group(1), os.path.join(addon_dir, f)))
    return sorted(out, key=lambda t: version_key(t[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.join('docs', 'omega', 'zips'))
    ap.add_argument('--keep', type=int, default=2,
                    help='how many versions of each add-on to retain (AF3 zips are ~54MB)')
    a = ap.parse_args()

    entries = []
    for addon_id in sorted(os.listdir(a.root)):
        addon_dir = os.path.join(a.root, addon_id)
        if not os.path.isdir(addon_dir):
            continue
        versions = zips_for(addon_dir, addon_id)
        if not versions:
            print('  skip %s (no zip)' % addon_id)
            continue

        # Prune oldest first, keeping the newest --keep.
        for ver, path in versions[:-a.keep]:
            os.remove(path)
            print('  pruned %s-%s.zip' % (addon_id, ver))
        versions = versions[-a.keep:]

        newest_ver, newest_zip = versions[-1]
        with zipfile.ZipFile(newest_zip) as z:
            names = z.namelist()
            axml = '%s/addon.xml' % addon_id
            if axml not in names:
                print('  skip %s (zip has no %s)' % (addon_id, axml))
                continue
            data = z.read(axml)
            # Mirror addon.xml and artwork beside the zip so Kodi's add-on browser
            # can show details without downloading the whole package.
            with open(os.path.join(addon_dir, 'addon.xml'), 'wb') as fh:
                fh.write(data)
            for art in ARTWORK:
                src = '%s/%s' % (addon_id, art)
                if src in names:
                    with open(os.path.join(addon_dir, art), 'wb') as fh:
                        fh.write(z.read(src))

        root = safe_parse(data, '%s addon.xml' % addon_id)
        entries.append((addon_id, newest_ver, data))
        print('  indexed %s %s' % (addon_id, root.get('version')))

    # Assemble addons.xml by concatenating each add-on's own manifest verbatim.
    # Re-serialising via ElementTree would drop upstream comments and reorder
    # attributes for no benefit.
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<addons>']
    for addon_id, ver, data in entries:
        text = data.decode('utf-8')
        text = re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', text)
        parts.append('\n'.join('    ' + l for l in text.strip().split('\n')))
    parts.append('</addons>')
    xml = '\n'.join(parts) + '\n'

    index = os.path.join(a.root, 'addons.xml')
    with io.open(index, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(xml)

    digest = hashlib.md5(xml.encode('utf-8')).hexdigest()
    with io.open(index + '.md5', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(digest)

    safe_parse(xml.encode('utf-8'), 'generated addons.xml')  # never publish a broken index
    print('  wrote addons.xml (%d add-ons) md5=%s' % (len(entries), digest))


if __name__ == '__main__':
    main()
