"""
CView manager bits
"""

import os
import re
import zipfile

class BadComicException(Exception):
    pass

def count_pages(archive):
    """
    Count the pages in a comic zip, raise an exception
    of anything is dodgy
    """
    if not zipfile.is_zipfile(archive):
        raise BadComicException("Archive is not a zip file")

    pages = 0

    zf = zipfile.ZipFile(archive)
    for zipname in zf.namelist():
        if valid_comicfile(zipname):
            pages = pages + 1
    zf.close()

    if pages == 0:
        raise BadComicException("No pages found")
    
    return pages

def valid_comicfile(name):
    """
    check for allowed filetype
    """
    return (name[-3:].lower() in ["png", "jpg", "peg", "gif", "txt"])

def sanitise(name):
    """
    Given a human name, return a filesystem-safe name
    """
    return re.sub("[^a-zA-Z0-9\-_\. ]", "", name).replace(" ", "_")

def comicname(zipname):
    """
    Given the name of a file within a comic zip, return a canonical
    name in the form chapter_name/page_name.ext
    """
    parts = zipname.split("/")
    if len(parts) == 1:
        return "01/"+sanitise(zipname)
    if len(parts) >= 2:
        return sanitise(parts[-2])+"/"+sanitise(parts[-1])

def extract_archive(archive, title):
    zf = zipfile.ZipFile(archive)
    for zipname in zf.namelist():
        outname = "books/"+sanitise(title)+"/"+comicname(zipname)
        if valid_comicfile(zipname):
            if not os.path.exists(os.path.dirname(outname)):
                os.makedirs(os.path.dirname(outname))
            data = zf.read(zipname)
            outfile = open(outname, "wb")
            outfile.write(data)
            outfile.close()
    zf.close()

