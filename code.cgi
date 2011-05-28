#!/usr/bin/env python

import os

# hack for people to install non-standard
# libraries locally
#if os.path.exists("./lib/"):
#    import sys
#    sys.path.append("./lib/")

import ConfigParser
import cgi
import web
import re
import tempfile
import md5
import logging
import shutil
import zipfile
import json

from sqlobject import *

render = None
session = None
config = None


# startup 
def main():
    config_file = "cview.cfg"

    # config
    try:
        global config
        config = ConfigParser.SafeConfigParser()
        config.read(config_file)
    except Exception, e:
        print "Failed to read config file %s: %s" % (config_file, e)
        return 1

    try:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)-8s %(message)s',
            filename=config.get("files", "log"))
    except Exception, e:
        print "Failed to start logging: "+str(e)
        return 2

    try:
        urls = (
            '/?', 'browse',
            '/view', 'view',
            '/comment/add', 'comment_add',
            '/comment/get', 'comment_get',
            '/user/login', 'login',
            '/user/logout', 'logout',
            '/comic/list/(\d+)', 'browse',
            '/comic/list', 'browse',
            '/comic/upload', 'upload',
            '/comic/download/(\d+).*', 'download',
            '/comic/rename', 'rename',
            '/comic/set_tags', 'set_tags',
            '/comic/set_language', 'set_language',
            '/comic/delete', 'delete',
            '/comic/rate', 'rate',
            '/api/(.*)', 'api',
            '(.*)', 'go404',
        )
        app = web.application(urls, globals())
    except:
        logging.exception("Error loading web app")
        return 3

    try:
        global render
        render = web.template.render(config.get("files", "templates"))
    except:
        logging.exception("Error loading renderer")
        return 3

    try:
        global session
        session_dir = config.get("files", "session_dir")
        if not os.path.exists(session_dir):
            os.mkdir(session_dir)
        session = web.session.Session(
            app, web.session.DiskStore(session_dir),
            initializer={'username': "Anonymous", 'is_user': False, 'is_admin': False})
    except:
        logging.exception("Error loading session manager")
        return 3

    try:
        #logging.debug("Connecting to database")
        hostname = config.get("database", "hostname")
        username = config.get("database", "username")
        password = config.get("database", "password")
        database = config.get("database", "database")
        conn = connectionForURI("postgres://%s:%s@%s/%s" % (
            username, password, hostname, database))
        # check that the connection is live. Yes, the connect() call will return
        # success when the server doesn't even exist, and this is the official
        # way to deal with that...
        conn.query("SELECT 1")
        sqlhub.processConnection = conn
    except:
        logging.exception("Error connecting to database")
        return 3

    try:
        logging.info("Running...")
        app.run()
        #logging.info("App is over, disconnecting from database")
        conn.close()
    except SystemExit:
        pass
        #logging.info("Got SystemExit")
    except Exception, e:
        logging.exception("App exception:")


# SQL objects
class User(SQLObject):
    class sqlmeta:
        table = "users"
    name = StringCol(alternateID=True, length=32, notNone=True)
    password = StringCol(dbName="pass", length=32)
    joindate = DateTimeCol()
    admin = BoolCol()
    comic_admin = BoolCol()
    email = StringCol(length=249)
    image_count = IntCol()
    comment_count = IntCol()

class Comic(SQLObject):
    class sqlmeta:
        table = "comics"
    owner = ForeignKey("User")
    owner_ip = Col(sqlType="INET", notNone=True)
    title = StringCol(length=64, alternateID=True, notNone=True)
    tags = StringCol(length=255, notNone=True)
    creator = StringCol(length=64, notNone=True)
    language = StringCol(length=64, notNone=True, default="unknown")
    description = StringCol(notNone=True, default="")
    pages = IntCol(notNone=True, default=0)
    rating = DecimalCol(size=5, precision=2, notNone=True, default=0)
    posted = DateCol(notNone=True, default=func.now())

    def get_language(self):
        known = ["english", "japanese", "spanish", "dutch", "finnish", "french", "german"]
        if self.language in known:
            return self.language
        for lang in known:
            if self.tags.lower().find(lang) >= 0:
                return lang
        return "unknown"

    def remove_files(self):
        if os.path.exists("books/"+self.get_disk_title()):
            shutil.rmtree("books/"+self.get_disk_title())

    def write_meta(self):
        cp = ConfigParser.SafeConfigParser()
        cp.addsection("meta")
        cp.set("meta", "title", self.title)
        cp.set("meta", "creator", self.creator)
        cp.set("meta", "language", self.language)
        cp.set("meta", "pages", self.pages)
        cp.set("meta", "tags", self.tags)
        cp.set("meta", "description", self.description)
        cp.write(file("books/"+self.get_disk_title()+"/meta.txt", "w"))

    def get_disk_title(self):
        return sanitise(self.title)

    def rename(self, new_title):
        old_disk_title = sanitise(self.title)
        new_disk_title = sanitise(new_title)
        shutil.move("books/"+old_disk_title, "books/"+new_disk_title)
        self.title = new_title

class ComicComment(SQLObject):
    class sqlmeta:
        table = "comic_comments"
    page = StringCol(length=64, notNone=True)
    owner = ForeignKey("User")
    owner_ip = Col(sqlType="INET", notNone=True)
    posted = DateCol(notNone=True, default=func.now())
    comment = StringCol(notNone=True)


# comic utility functions
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


# web utility functions
def if_user_is_admin(func):
    """
    decorate a function to only run if the user is an admin,
    else show a login prompt
    """
    def splitter(*args):
        if session.is_admin:
            return func(*args)
        else:
            return render.login()
    return splitter

def if_user_is_user(func):
    """
    decorate a function to only run if the user is non-anonymous,
    else show a login prompt
    """
    def splitter(*args):
        if session.is_user:
            return func(*args)
        else:
            return render.login()
    return splitter

def log_info(text):
    """
    A simple wrapper for logging.info(), prepends username and IP
    """
    logging.info("%s (%s): %s" % (session.username, web.ctx.ip, text))

def get_comics(search=None, orderBy="default", way="asc", page=1):
    """
    Find comics, optionally filtered with a tag
    """
    tag = "%"
    if search:
        tag = str("%"+search+"%")
    if orderBy == "default":
        orderBy = "posted"
        way = "desc"
    if orderBy not in [
                "title", "posted",
                "rating", "pages",
                "id"]:
        orderBy = "title"
    comics = Comic.select("tags ILIKE %s" % Comic.sqlrepr(tag), orderBy=orderBy)
    if way == "desc":
        comics = comics.reversed()
    comics = comics[(page-1)*100:page*100]
    return comics

def add_to_db(title, tags, pages, owner="Anonymous", owner_ip="0.0.0.0"):
    """
    Add some meta-info to the database
    """
    if len(title) == 0:
        raise BadComicException("No title specified")
    existing = Comic.selectBy(title=str(title))
    if len(list(existing)) > 0:
        raise BadComicException("There's already a comic with that title")
    Comic(owner=User.byName(owner), owner_ip=str(owner_ip), title=str(title), tags=str(tags), pages=int(pages))


# user
class login:
    def GET(self):
        return render.login()

    def POST(self):
        x = web.input(username=None, password=None)
        log_info("Logging in: "+str(x["username"]))
        try:
            passhash = md5.md5(x["username"].lower() + x["password"]).hexdigest()
            user = User.select("name LIKE %s AND pass=%s" % (
                User.sqlrepr(str(x["username"])), User.sqlrepr(str(passhash))
            ))[0]
        except Exception, e:
            user = None
        if user:
            session["username"] = user.name
            session["admin"] = user.comic_admin
            session["is_admin"] = user.comic_admin
            session["is_user"] = True
            log_info("Logged in")
            web.seeother("http://rule34c.paheal.net/")
        else:
            return "Login failed"

class logout:
    def GET(self):
        log_info("Logged out")
        session.kill()
        web.seeother("http://rule34c.paheal.net/")

# admin
class hack:
    def GET(self):
        return "o"
        import time
        conn = connect()
        comics = Comic.select()
        for comic in comics:
            if os.path.exists("books/"+comic.get_disk_title()):
                time_secs = os.stat("books/"+comic.get_disk_title())[8]
                comic.posted = time.strftime("%Y-%m-%d", time.localtime(time_secs))
        conn.close()
        return "ok"

class api:
    def GET(self, call):
        if call == "all_comics":
            return json.write([{
                "id": int(c.id),
                "title": str(c.title),
                "disk_title": str(c.get_disk_title()),
                "pages": int(c.pages),
                "tags": str(c.tags),
                "posted": str(c.posted),
                "language": str(c.get_language())
            } for c in Comic.select()])
        elif call == "all_tags":
            tags = set()
            for c in Comic.select():
                for tag in c.tags.lower().split():
                    tags.add(tag)
            return json.write(list(tags))

# comic
class browse:
    def GET(self, pagen=1):
        x = web.input(search=None, sort="default", way="asc")
        return render.browse(int(pagen), get_comics(x["search"], orderBy=x["sort"], way=x["way"], page=int(pagen)), session)

class rename:
    @if_user_is_admin
    def POST(self):
        try:
            x = web.input(comic_id=None, title=None)
            if x["comic_id"] and x["title"]:
                comic = Comic.get(int(x["comic_id"]))
                log_info("Renamed %s (%d) to %s" % (comic.title, comic.id, x["title"]))
                comic.rename(x["title"])
                return "Renamed comic #%d to %s" % (comic.id, cgi.escape(comic.title))
            else:
                return "Missing comic_id or title"
        except Exception, e:
            return "Error: "+str(e)

class rate:
    @if_user_is_user
    def POST(self):
        try:
            x = web.input(comic_id=None, rating=None)
            if x["comic_id"] and x["rating"]:
                comic_id = int(x["comic_id"])
                comic = Comic.get(int(x["comic_id"]))
                rating = int(x["rating"])
                if rating < 1 or rating > 5:
                    return "Ratings can only be 1-5"
                owner_id = User.byName(session["username"]).id
                sqlhub.processConnection.query("""
                    DELETE FROM comic_ratings WHERE comic_id=%d AND owner_id=%d
                    """ % (comic_id, owner_id))
                sqlhub.processConnection.query("""
                    INSERT INTO comic_ratings(comic_id, owner_id, rating) VALUES(%d, %d, %d)
                    """ % (comic_id, owner_id, rating))
                sqlhub.processConnection.query("""
                    UPDATE comics
                    SET rating=
                        (SELECT SUM(rating) FROM comic_ratings WHERE comic_id=%d)/
                        (SELECT COUNT(*) FROM comic_ratings WHERE comic_id=%d)
                    WHERE id=%d
                    """ % (comic_id, comic_id, comic_id))
                log_info("Voted #%d to %d" % (comic_id, rating))
                return "Rated %s as %d-star" % (cgi.escape(comic.title), rating)
            else:
                return "Missing comic_id or rating"
        except Exception, e:
            return "Error: "+str(e)

class set_tags:
    @if_user_is_user
    def POST(self):
        try:
            x = web.input(comic_id=None, tags=None)
            if x["comic_id"] and x["tags"]:
                comic = Comic.get(int(x["comic_id"]))
                comic.tags = x["tags"]
                log_info("Set tags for %s (%d) to %s" % (comic.title, comic.id, comic.tags))
                return "Tags for %s set to: %s" % (cgi.escape(comic.title), cgi.escape(comic.tags))
            else:
                return "Missing comic_id or tags"
        except Exception, e:
            return "Error: "+str(e)

class set_language:
    @if_user_is_user
    def POST(self):
        try:
            x = web.input(comic_id=None, language=None)
            if x["comic_id"] and x["language"]:
                comic = Comic.get(int(x["comic_id"]))
                comic.language = x["language"]
                log_info("Set language for %s (%d) to %s" % (comic.title, comic.id, comic.language))
                return "Language for %s set to: %s" % (cgi.escape(comic.title), cgi.escape(comic.language))
            else:
                return "Missing comic_id or language"
        except Exception, e:
            return "Error: "+str(e)

class delete:
    @if_user_is_admin
    def POST(self):
        try:
            x = web.input(comic_id=None)
            if x["comic_id"]:
                comic = Comic.get(int(x["comic_id"]))
                comic.remove_files()
                comic.destroySelf()
                log_info("Deleted %s (%d)" % (comic.title, comic.id))
                return "Deleted \"%s\"" % (cgi.escape(comic.title), )
            else:
                return "Missing comic_id"
        except Exception, e:
            return "Error: "+str(e)

class view:
    def GET(self):
        web.http.expires(86400)
        return render.view()

class upload:
    def POST(self):
        try:
            x = web.input(title=None, tags="tagme", archive={})

            upload_tmp = config.get("files", "upload_tmp")
            if upload_tmp and not os.path.exists(upload_tmp):
                os.mkdir(upload_tmp)
            if len(x['archive'].value) == 0:
                raise BadComicException("Uploaded file is empty")
            outinfo = tempfile.mkstemp(".zip", dir=upload_tmp)
            outfile = open(outinfo[1], "wb")
            outfile.write(x['archive'].value)
            outfile.close()
            archive_name = outinfo[1]

            pages = count_pages(archive_name)
            title = x['title'].strip()
            add_to_db(title, x['tags'], pages, session["username"], web.ctx.ip)
            extract_archive(archive_name, title)
            os.remove(outinfo[1])
            log_info("Uploaded %s (%s)" % (title, x['tags']))
            return "Comic uploaded without error, you may need to hit refresh to see it in the list"
        except BadComicException, e:
            return str(e)

class download:
    def GET(self, cid):
        from zipstream import ZipStream
        web.http.expires(86400 * 30)
        comic = Comic.get(int(cid))
        path = "books/"+comic.get_disk_title()
        zip_filename = comic.get_disk_title()+'.cbz'
        web.header('Content-type' , 'application/octet-stream')
        web.header('Content-Disposition', 'attachment; filename="%s"' % (zip_filename,))
        for data in ZipStream(path):
            yield data


# comment
class comment_add:
    def POST(self):
        x = web.input(target=None, comment=None)
        target = x["target"];
        comment = x["comment"];

        ComicComment(
            page=str(target),
            owner=User.byName(str(session["username"])),
            owner_ip=str(web.ctx.ip),
            comment=str(comment)
        )

        return "ok"

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

class comment_get:
    def GET(self):
        x = web.input(page=None)
        page = x["page"]
        comments = ComicComment.selectBy(page=str(page))
        buf = ""
        for comment in comments:
            buf = buf + "comment:"+comment.owner.name+":"+cgi.escape(comment.comment).replace("\n", "<br>")+"\n"
        return buf

# misc
class go404:
    def GET(self, url):
        return "404: 'GET "+str(url)+"' not found"

    def POST(self, url):
        return "404: 'POST "+str(url)+"' not found"+str(web.ctx.env)


if __name__ == "__main__":
    main()

