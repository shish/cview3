#!/usr/bin/python2.4

session_dir = "./sessions"
upload_tmp = "./upload_tmp"

import sys
sys.path.append("./lib/")

import cgi
import web
import re
import os
import tempfile
import md5
import logging

from shcomdb import *
from cview import *

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
)
render = web.template.render("templates/")
app = web.application(urls, locals())
if not os.path.exists(session_dir):
    os.mkdir(session_dir)
session = web.session.Session(
    app, web.session.DiskStore(session_dir),
    initializer={'username': "Anonymous", 'is_user': False, 'is_admin': False})


# utility functions
def if_user_is_admin(func):
    def splitter(*args):
        if session.is_admin:
            return func(*args)
        else:
            return render.login()
    return splitter

def if_user_is_user(func):
    def splitter(*args):
        if session.is_user:
            return func(*args)
        else:
            return render.login()
    return splitter

def log_info(text):
    logging.info("%s (%s): %s" % (session.username, web.ctx.ip, text))

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

            if not os.path.exists(upload_tmp):
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

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        filename="cview.log")
    conn = connect()
    app.run()
    conn.close()
