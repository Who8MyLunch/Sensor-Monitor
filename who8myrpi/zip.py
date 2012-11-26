
from __future__ import division, print_function, unicode_literals

import os
import zipfile

def folder_zip(path_folder, verbosity=False):
    """
    Zip the contents of a folder.
    Create a zip new file from existing folder.
    """

    path_folder = os.path.abspath(os.path.normpath(path_folder))

    path_base = os.path.dirname(path_folder)
    name_folder = os.path.basename(path_folder)

    fname_zip = name_folder + '.zip'

    f = os.path.join(path_base, fname_zip)
    compression = zipfile.ZIP_DEFLATED    # zipfile.ZIP_STORED

    if os.path.isfile(f):
        # Add to existing archive.
        mode = 'a'
    else:
        # Write to a new archive.
        mode = 'w'

    with zipfile.ZipFile(f, mode, compression=compression) as zipper:
        for path_root, folders, files in os.walk(path_folder):
            for f in files:
                if verbosity:
                    print(os.path.basename(f))

                f_true = os.path.join(path_root, f)
                f_arc = f_true.split(path_folder)[1]
                zipper.write(f_true, f_arc)

    # Done.
    return os.path.join(path_base, fname_zip)



def folder_unzip(fname_zip):
    """
    Extract zip file to new folder.
    """

    fname_zip = os.path.abspath(os.path.normpath(fname_zip))

    path_base = os.path.dirname(fname_zip)

    b, e = os.path.splitext(os.path.basename(fname_zip))
    name_folder = b

    path_out = os.path.join(path_base, name_folder)
    if not os.path.isdir(path_out):
        os.mkdir(path_out)

    with zipfile.ZipFile(fname_zip, 'r') as zipper:
        zipper.extractall(path_out)

    # Done.
