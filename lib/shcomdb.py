"""
Shimmie / Comic database functions
"""

import re
import shutil
from cview import *
from sqlobject import *

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
    posted = DateCol(default=func.now())

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
                

def connect():
    username = "rule34"
    password = "rule3434"
    hostname = "marigold.shishnet.org"
    database = "rule34"
    conn = connectionForURI("postgres://%s:%s@%s/%s" % (
        username, password, hostname, database))
    # check that the connection is live. Yes, the connect() call will return
    # success when the server doesn't even exist, and this is the official
    # way to deal with that...
    conn.query("SELECT 1")
    sqlhub.processConnection = conn
    return conn

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

