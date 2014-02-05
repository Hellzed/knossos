import sys
import os
import logging
import shutil
import subprocess
import six
import progress
from six.moves.urllib.request import urlopen


SEVEN_PATH = '7z'


def get(link):
    try:
        logging.info('Retrieving "%s"...', link)
        result = urlopen(link)
        if six.PY2:
            code = result.getcode()
        else:
            code = result.status

        if code == 200:
            return result
        else:
            return None
    except:
        logging.exception('Failed to load "%s"!', link)

    return None


def download(link, dest):
    try:
        logging.info('Downloading "%s"...', link)
        result = urlopen(link)
        if six.PY2:
            size = float(result.info()['Content-Length'])
            if result.getcode() != 200:
                return False
        else:
            size = float(result.getheader('Content-Length'))
            if result.status != 200:
                return False

        start = dest.tell()
        while True:
            chunk = result.read(50 * 1024)  # Read 50KB chunks
            if not chunk:
                break

            dest.write(chunk)

            progress.update((dest.tell() - start) / size, '%s: %d%%' % (os.path.basename(link), 100 * (dest.tell() - start) / size))
    except:
        logging.exception('Failed to load "%s"!', link)
        return False

    return True


# This function will move the contents of src inside dest so that src/a/r/z.dat ends up as dest/a/r/z.dat.
# It will overwrite everything already present in the destination directory!
def movetree(src, dest, ifix=False):
    if not os.path.isdir(dest):
        os.makedirs(dest)

    if ifix:
        siblings = os.listdir(dest)
        l_siblings = [s.lower() for s in siblings]

    for item in os.listdir(src):
        spath = os.path.join(src, item)
        dpath = os.path.join(dest, item)

        if ifix and not os.path.exists(dpath):
            if item.lower() in l_siblings:
                l_item = siblings[l_siblings.index(item.lower())]
                logging.warning('Changing path "%s" to "%s" to avoid case problems...', dpath, os.path.join(dest, l_item))

                dpath = os.path.join(dest, l_item)
            else:
                siblings.append(item)
                l_siblings.append(item.lower())

        if os.path.isdir(spath):
            movetree(spath, dpath)
        else:
            if os.path.exists(dpath):
                os.unlink(dpath)
            
            shutil.move(spath, dpath)


def normpath(path):
    return os.path.normcase(path.replace('\\', '/'))


# Try to map a case insensitive path to an existing one.
def ipath(path):
    if os.path.exists(path):
        return path

    parent = os.path.dirname(path)
    if not os.path.exists(parent):
        parent = ipath(parent)

        if not os.path.exists(parent):
            # Well, nothing we can do here...
            return path

    siblings = os.listdir(parent)
    l_siblings = [s.lower() for s in siblings]
    
    item = os.path.basename(path)
    if item.lower() in l_siblings:
        item = siblings[l_siblings.index(item.lower())]
        path = os.path.join(parent, item)

    return path


def test_7z():
    try:
        return subprocess.call([SEVEN_PATH, '-h'], stdout=subprocess.DEVNULL) == 0
    except:
        logging.exception('Call to 7z failed!')
        return False


def is_archive(path):
    return subprocess.call([SEVEN_PATH, 'l', path], stdout=subprocess.DEVNULL) == 0


def extract_archive(archive, outpath, overwrite=False, files=None, _rec=False):
    if '.tar.' in archive and not _rec:
        # This is a file like whatever.tar.gz. We have to call 7z two times for this kind of file:
        # First to get whatever.tar and second to extract that tar archive.
        
        if not extract_archive(archive, os.path.dirname(archive), True, None, True):
            return False
        
        unc_archive = archive.split('.')
        # Remove the .gz or .bz2 or whatever ending...
        unc_archive.pop()
        
        # ... and put it together again.
        unc_archive = '.'.join(unc_archive)
        res = extract_archive(unc_archive, outpath, overwrite, files)
        
        # Cleanup
        os.unlink(unc_archive)
        return res
        
    cmd = [SEVEN_PATH, 'x', '-o' + outpath]
    if overwrite:
        cmd.append('-y')

    cmd.append(archive)

    if files is not None:
        cmd.extend(files)

    # Redirect its stdout to sys.stdout so its output is logged.
    # (installer.py redirects sys.stdout.)
    if hasattr(sys.stdout, 'fileno'):
        output = sys.stdout
    else:
        output = None
    return subprocess.call(cmd, stdout=output, stderr=output) == 0
