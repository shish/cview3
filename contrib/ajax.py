#!/usr/bin/python

from glob import glob
import os.path
import cgi
import cgitb; cgitb.enable()


def main():
    form = cgi.FieldStorage()

    func = "page"
    if "func" in form:
        func = form["func"].value

    if func == "get_books":
        print "Context-type: text/plain"
        print
        for n in glob(os.path.join("books", "*")):
            if os.path.isdir(n):
                print os.path.basename(n)

    if func == "get_chaps":
        print "Context-type: text/plain"
        print
        for n in glob(os.path.join("books", form["book"].value, "*")):
            if os.path.isdir(n):
                print os.path.basename(n)

    if func == "get_pages":
        print "Context-type: text/plain"
        print
        for n in glob(os.path.join("books", form["book"].value, form["chap"].value, "*")):
            if os.path.isfile(n) and (n.endswith(".jpg") or n.endswith(".png")):
                print os.path.basename(n)

if __name__ == "__main__":
    main()

