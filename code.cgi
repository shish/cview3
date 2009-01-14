#!/usr/bin/python2.4

import sys
sys.path.append("./lib/")

import ConfigParser
import cgi
import web
import re
import os
import tempfile
import md5
import logging
import shutil
import zipfile

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
            '/comic/list', 'browse',
            '/comic/upload', 'upload',
            '/comic/rename', 'rename',
            '/comic/set_tags', 'set_tags',
            '/comic/delete', 'delete',
            # deprecated
            '/browse', 'browse',
            '/browse.cgi', 'browse',
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
        #logging.info("Running...")
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
    description = StringCol(notNone=True, default="")
    pages = IntCol(notNone=True, default=0)
    rating = DecimalCol(size=5, precision=2, notNone=True, default=0)
    posted = DateCol(notNone=True, default=func.now())

    def get_language(self):
        if self.tags.lower().find("english") >= 0:
            return "english"
        if self.tags.lower().find("japanese") >= 0:
            return "japanese"
        else:
            return "unknown"

    def remove_files(self):
        shutil.rmtree("books/"+self.get_disk_title())

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

def get_comics(search=None, orderBy="default", way="asc"):
    """
    Find comics, optionally filtered with a tag
    """
    tag = "%"
    if search:
        tag = "%"+search+"%"
    if orderBy == "default":
        orderBy = "posted"
        way = "desc"
    if orderBy not in [
                "title", "posted",
                "rating", "pages",
                "id"]:
        orderBy = "title"
    comics = Comic.select("tags LIKE %s" % Comic.sqlrepr(tag), orderBy=orderBy)
    if way == "desc":
        comics = comics.reversed()
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
            web.seeother("/")
        else:
            return "Login failed"

class logout:
    def GET(self):
        log_info("Logged out")
        session.kill()
        web.seeother("/")

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

# comic
class browse:
    def GET(self):
        x = web.input(sort="default", way="asc")
        return render.browse(get_comics(orderBy=x["sort"], way=x["way"]), session)

class rename:
    @if_user_is_admin
    def POST(self):
        try:
            x = web.input(comic_id=None, title=None)
            if x["comic_id"] and x["title"]:
                comic = Comic.get(int(x["comic_id"]))
                log_info("Renamed %s (%d) to %s" % (comic.title, comic.id, x["title"]))
                comic.rename(x["title"])
                return "Renamed OK"
            else:
                return "Missing comic_id or title"
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
                return "Tags set OK"
            else:
                return "Missing comic_id or tags"
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
                return "Deleted OK"
            else:
                return "Missing comic_id"
        except Exception, e:
            return "Error: "+str(e)

class view:
    def GET(self):
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
            add_to_db(x['title'], x['tags'], pages, session["username"], web.ctx.ip)
            extract_archive(archive_name, x['title'])
            log_info("Uploaded %s (%s)" % (x['title'], x['tags']))
            return "Comic uploaded without error"
        except BadComicException, e:
            return str(e)

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
        return url


if __name__ == "__main__":
    main()

