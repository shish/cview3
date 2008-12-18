#!/usr/bin/python2.4

import cgi
import web
import os
import sqlite
import zipfile
import tempfile
import os
import re

urls = (
    '/?', 'browse',
    '/browse', 'browse',
    '/browse.cgi', 'browse',
    '/view', 'view',
    '/upload', 'upload',
    '/tag_set', 'tag_set',
    '/comment', 'comment',
)
render = web.template.render("templates/")
app = web.application(urls, locals())

# common upload
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
    return name.replace(" ", "_").replace("!", "").replace("'", "").replace("/", "")

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

# database
def get_database():
    """
    Get a connection to the database, creating it if necessary
    """
    if not os.path.exists('comics.db'):
        conn = sqlite.connect('comics.db')
        cursor = conn.cursor()
        cursor.execute("""
			CREATE TABLE comics (
				title varchar(64) not null unique,
				tags varchar(255) not null,
                description text not null default "",
				pages integer not null,
				rating decimal not null default 0.0
			)
        """)
        conn.commit()
    else:
        conn = sqlite.connect('comics.db')
    return conn

def get_comics(search=None):
    """
    Find comics, optionally filtered with a tag
    """
    tag = "%"
    if search:
        tag = "%"+search+"%"
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comics WHERE tags LIKE %s ORDER BY title", tag)
    comics = cursor.fetchall()
    conn.close()
    return comics

def add_to_db(title, tags, pages):
    """
    Add some meta-info to the database
    """
    if len(title) == 0:
        raise BadComicException("No title specified")
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comics WHERE title=%s", title)
    if len(cursor.fetchall()) > 0:
        raise BadComicException("There's already a comic with that title")
    cursor.execute("INSERT INTO comics(title, tags, pages) VALUES (%s, %s, %d)", title, tags, pages)
    conn.commit()
    conn.close()

# page
class browse:
    def GET(self):
        return render.browse(get_comics())

class view:
    def GET(self):
        return render.view()

class upload:
    def POST(self):
        try:
            x = web.input(title=None, tags="tagme", archive={})

            outinfo = tempfile.mkstemp(".zip")
            outfile = open(outinfo[1], "wb")
            outfile.write(x['archive'].value)
            outfile.close()
            archive_name = outinfo[1]

            pages = count_pages(archive_name)
            add_to_db(x['title'], x['tags'], pages)
            extract_archive(archive_name, x['title'])
            return "Comic uploaded without error"
        except BadComicException, e:
            return str(e)

class tag_set:
    def GET(self, url):
        return url

class comment:
    def POST(self):
        x = web.input(target=None, comment=None)
        target = x["target"];
        comment = x["comment"];
        return self.add(target, comment)

    def GET(self):
        x = web.input(target=None, comment=None)
        target = x["target"];
        comment = x["comment"];
        return self.add(target, comment)

    def add(self, target, comment):
        if os.path.exists("books/"+target):
            txt_target = re.sub("(jpg|png|gif)$", "txt", target)
            if txt_target.endswith("txt"):
                fp = open("books/"+txt_target, "a")
                fp.write("comment:"+web.ctx.ip+":Anonymous:"+cgi.escape(comment).replace("\n", "<br>")+"\n");
                fp.close();
                return "ok"
            else:
                return "invalid image"
        else:
            return "image not found"

if __name__ == "__main__":
    app.run()
