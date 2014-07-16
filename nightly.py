#!/usr/bin/env python

import glob
import os
import subprocess
import sys
import urllib

import conf


def fetch_all_extensions():
    print 'Fetching list of all extensions...'
    req = urllib.urlopen(conf.EXT_LIST)
    text = req.read()
    req.close()
    return text


def get_all_extensions(update=False):
    fname = os.path.join(conf.SRC_PATH, 'extension-list')
    if update or not os.path.exists(fname):
        with open(fname, 'w') as f:
            exts = fetch_all_extensions()
            f.write(exts)
    else:
        with open(fname, 'r') as f:
            exts = f.read()

    return exts.strip().splitlines()


def shell_exec(args, **kwargs):
    return subprocess.check_output(args, **kwargs)


def update_extension(ext):
    full_path = os.path.join(conf.SRC_PATH, ext)
    print 'Starting update for %s' % ext
    if not os.path.exists(full_path):
        os.chdir(conf.SRC_PATH)
        print 'Cloning %s' % ext
        shell_exec(['git', 'clone', conf.GIT_URL % ext, ext])
        pass
    for branch in conf.SUPPORTED_VERSIONS:
        os.chdir(full_path)
        print 'Creating %s for %s' %(branch, ext)
        shell_exec(['git', 'fetch'])
        shell_exec(['git', 'reset', '--hard', 'origin/master'])
        try:
            shell_exec(['git', 'checkout', 'origin/%s' % branch])
        except subprocess.CalledProcessError:
            print 'Error: could not checkout origin/%s' % branch
            continue
        shell_exec(['git', 'submodule', 'sync'])
        shell_exec(['git', 'submodule', 'update', '--init'])
        rev = shell_exec(['git', 'rev-parse', '--short', 'HEAD']).strip()
        tarball_fname = '%s-%s-%s.tar.gz' % (ext, branch, rev)
        if os.path.exists(os.path.join(conf.DIST_PATH, tarball_fname)):
            print 'No updates to branch, tarball already exists.'
            continue
        with open('version', 'w') as f:
            f.write('%s: %s\n' %(ext, branch))
            f.write(shell_exec(['date', '+%Y-%m-%dT%H:%M:%S']) + '\n')  # TODO: Do this in python
            f.write(rev + '\n')
        old_tarballs = glob.glob(os.path.join(conf.DIST_PATH, '%s-%s-*.tar.gz' %(ext, branch)))
        print 'Deleting old tarballs...'
        for old in old_tarballs:
            # FIXME: Race condition, we should probably do this later on...
            os.unlink(old)
            pass
        os.chdir(conf.SRC_PATH)
        shell_exec(['tar', 'czPf', tarball_fname, ext])
        pass
    print 'Moving new tarballs into dist/'
    tarballs = glob.glob(os.path.join(conf.SRC_PATH, '*.tar.gz'))
    for tar in tarballs:
        fname = tar.split('/')[-1]
        os.rename(tar, os.path.join(conf.DIST_PATH, fname))
    print 'Finished update for %s' % ext


def main():
    extensions = get_all_extensions(update=True)
    print 'Starting update of all extensions...'
    for ext in extensions:
        update_extension(ext)
    print 'Finished update of all extensions!'
    pass


if __name__ == '__main__':
    if '--all' in sys.argv:
        main()
    else:
        update_extension('VisualEditor')

