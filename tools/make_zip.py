"""Build a Kodi add-on zip from a git ref, stamping our version suffix onto it.

The zip Kodi expects has exactly one top-level directory named for the add-on id,
so that is what --prefix produces. Files git does not track are never included,
which is what keeps __pycache__, .pyc and local scratch out of a release.

Usage:
    python make_zip.py --src <git-worktree> --ref main --id script.module.magneto \
                       --suffix .1 --out <dir>

Prints the built version to stdout so a workflow can capture it.
"""
import argparse, io, os, re, subprocess, sys, tarfile, zipfile

# Paths that must never reach a published add-on zip. Upstream ships its own CI
# and issue templates; they are dead weight inside an installed add-on. Anything
# whose basename starts with .git is repo metadata (.gitignore, .gitattributes)
# and likewise has no business in a package Kodi unpacks over the add-on dir.
SKIP_PREFIXES = ('.github',)


def is_skipped(name):
    if any(name == p or name.startswith(p + '/') for p in SKIP_PREFIXES):
        return True
    return os.path.basename(name).startswith('.git')


def git_archive(src, ref):
    """Return {path: (bytes, mode)} for every tracked file at ref."""
    # -c core.autocrlf=false is load-bearing: git archive otherwise applies the
    # repo's CRLF conversion, so a Windows checkout would package CRLF files that
    # upstream shipped as LF. That drift reaches addons.xml and breaks its md5.
    out = subprocess.run(['git', '-C', src, '-c', 'core.autocrlf=false',
                          '-c', 'core.eol=lf', 'archive', '--format=tar', ref],
                         capture_output=True, check=True).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(out)) as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            if is_skipped(m.name):
                continue
            files[m.name] = (tf.extractfile(m).read(), m.mode)
    return files


def stamp_version(addon_xml, suffix):
    """Append the suffix to the add-on version, leaving everything else alone.

    Deliberately a narrow regex on the first version= attribute rather than an XML
    round-trip: re-serialising would reorder attributes and rewrite entities, which
    turns every release into a noisy diff and risks non-ASCII creeping in.
    """
    text = addon_xml.decode('utf-8')
    m = re.search(r'(<addon\b[^>]*?\bversion=")([^"]+)(")', text)
    if not m:
        raise SystemExit('could not find addon version attribute')
    base = m.group(2)
    if base.endswith(suffix):
        new = base
    else:
        new = base + suffix
    text = text[:m.start(2)] + new + text[m.end(2):]
    data = text.encode('utf-8')
    try:
        data.decode('ascii')
    except UnicodeDecodeError:
        # Fen Light's own service rewrites addon.xml with the cp1252 codec and
        # truncates the file to zero bytes on any non-cp1252 character. Keeping
        # every addon.xml ASCII-only across the board avoids that class of bug.
        print('  WARNING: addon.xml contains non-ASCII characters', file=sys.stderr)
    return data, base, new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--ref', default='main')
    ap.add_argument('--id', required=True)
    ap.add_argument('--suffix', default='.1')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    files = git_archive(a.src, a.ref)
    if 'addon.xml' not in files:
        raise SystemExit('no addon.xml at the root of %s@%s' % (a.src, a.ref))

    stamped, base, new = stamp_version(files['addon.xml'][0], a.suffix)
    files['addon.xml'] = (stamped, files['addon.xml'][1])

    os.makedirs(a.out, exist_ok=True)
    zip_path = os.path.join(a.out, '%s-%s.zip' % (a.id, new))
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            data, mode = files[name]
            zi = zipfile.ZipInfo('%s/%s' % (a.id, name))
            zi.external_attr = (mode & 0xFFFF) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            # Fixed timestamp so an unchanged source produces an identical zip.
            zi.date_time = (1980, 1, 1, 0, 0, 0)
            z.writestr(zi, data)

    print('  %s  %s -> %s  (%d files, %.1f MB)' % (
        a.id, base, new, len(files), os.path.getsize(zip_path) / 1e6))
    print(new)


if __name__ == '__main__':
    main()
