#!/usr/bin/python2.4

import cgi
import cgitb; cgitb.enable()
import os, sys
import sqlite
import tempfile
import zipfile

# http upload
def handle_upload():
    form = cgi.FieldStorage()
    if form.has_key("archive") and form["archive"].file:
        archive = upload_to_file(form["archive"].file)
        title = form["title"].value
        tags = form["tags"].value

        try:
            info = get_archive_info(archive)
            if len(title) == 0:
                raise BadComicException("No title specified")
            if len(tags) == 0:
                raise BadComicException("No tags specified")

            add_to_db(title, info['short_title'], tags, info['pages'])
            extract_archive(archive)
            print "Location: browse.cgi"
            print
        except BadComicException, e:
            print "Content-type: text/html"
            print
            print "Upload failed: "+str(e)

        #os.remove(archive)
        return True
    return False
def upload_to_file(infile):
    outinfo = tempfile.mkstemp(".zip")
    outfile = open(outinfo[1], "wb")
    while True:
        chunk = infile.read(1024*64)
        if chunk:
            outfile.write(chunk)
        else:
            outfile.close()
            break
    return outinfo[1]

# cli upload
def handle_add():
    if len(sys.argv) == 4:
        archive = sys.argv[1]
        title = sys.argv[2]
        tags = sys.argv[3]
        info = get_archive_info(archive)
        add_to_db(title, info['short_title'], tags, info['pages'])
        extract_archive(archive)
        return True
    return False

# common upload
class BadComicException(Exception):
    pass
def get_archive_info(archive):
    if not zipfile.is_zipfile(archive):
        raise BadComicException("Archive is not a zip file")

    short_title = None
    pages = 0

    zf = zipfile.ZipFile(archive)
    for zipname in zf.namelist():
        if valid_comicfile(zipname):
            short_title = zipname_to_outname(zipname).split("/")[1]
            pages = pages + 1
    zf.close()

    if pages == 0:
        raise BadComicException("No pages found")
    
    return {
        "short_title": short_title,
        "pages": pages
    }
def valid_comicfile(name):
    return (
        (name[-3:].lower() in ["png", "jpg", "peg", "gif", "txt"]) and
        (len(name.split("/")) == 3)
    )
def zipname_to_outname(zipname):
    return "books/"+zipname.replace(" ", "_")
def extract_archive(archive):
    zf = zipfile.ZipFile(archive)
    for zipname in zf.namelist():
        outname = zipname_to_outname(zipname)
        if zipname[-1:] == "/":
            if not os.path.exists(outname):
                os.makedirs(outname)
        if valid_comicfile(zipname):
            data = zf.read(zipname)
            outfile = open(outname, "wb")
            outfile.write(data)
            outfile.close()
    zf.close()

# database
def get_database():
    if not os.path.exists('comics.db'):
        conn = sqlite.connect('comics.db')
        cursor = conn.cursor()
        cursor.execute("""
			CREATE TABLE comics (
				title varchar(64) not null,
                short_title varchar(16) not null,
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
def get_comics():
    form = cgi.FieldStorage()
    tag = "%"
    if form.has_key("tag"):
        tag = "%"+form['tag'].value+"%"
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comics WHERE tags LIKE %s ORDER BY title", tag)
    comics = cursor.fetchall()
    conn.close()
    return comics
def add_to_db(title, sort_title, tags, pages):
    conn = get_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comics VALUES (%s, %s, %s, %d, 0.0)",
                   title, sort_title, tags, pages)
    conn.commit()
    conn.close()

# html
def list_comics(results):
    print "<h3>Comic List</h3>"
    print "<table border='1'>"
    print "<thead><tr><th>Name</th><th>Pages</th><th>Tags</th></tr></thead>"
    for (title, short_title, tags, pages, rating) in results:
        link = "cview.html#%s--0--0" % cgi.escape(short_title)
        tags_h = " ".join([
            "<a href='browse.cgi?tag=%s'>%s</a> " %
            (n, n) for n in cgi.escape(tags).split(" ")
            ])

        print "<tr><td><a href='%s'>%s</a></td><td>%s</td>"\
              "<td>%s</td></tr>\n" % (link, cgi.escape(title), pages, tags_h);
    print "</table>"
def get_uploader():
	return """
<h3>Upload</h3>
Uploads should be in .zip format, with folders inside, in the structure
comic_short_title/chapter/page.ext, eg bobs_day_at_school/01/page01.jpg;
allowed filetypes are .jpg, .png, .gif and .txt; any files outside this
structure will be ignored (readme files and such should go in chapter zero)

<P><form enctype="multipart/form-data" method="POST" action="browse.cgi">
	<table>
		<tr><td>Archive</td><td><input type="file" name="archive"></td></tr>
		<tr><td>Full Title</td><td><input type="text" name="title"></td></tr>
		<tr><td>Tags</td><td><input type="text" name="tags"></td></tr>
		<tr><td colspan="2"><input type="submit" style="width: 100%"></td></tr>
	</table>
</form>
    """
def get_header():
    return """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
	<head>
		<title>CView Browser</title>
		<link rel='stylesheet' href='cview.css' type='text/css'>
	</head>
	<body>
<div class="padded">
<h1>CView Browser</h1>
<h3>Info</h3>
To-do: tag editing, block dupe short titles, try and detect duplicate comics,
admin controls, rating, comments, make things look nice
    """
def get_footer():
    return """</div></body></html>"""

if __name__ == "__main__":
    if handle_add():
        pass
    elif handle_upload():
        pass
    else:
        print "Content-type: text/html"
        print
        print get_header()
        list_comics(get_comics())
        print get_uploader()
        print get_footer()

