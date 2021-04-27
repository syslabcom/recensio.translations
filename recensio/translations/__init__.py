# -*- extra stuff goes here -*-
from zc.testbrowser.browser import Browser
from zope.i18nmessageid import MessageFactory

import pkg_resources
import sys


RecensioMessageFactory = MessageFactory("recensio")


def initialize(context):
    """Initializer called when used as a Zope 2 product."""


def podiff(vcsurl):
    """Shows differences between the po files in the working copy of this
    package and their counterparts in the repository. Only cares
    about msgid and msgstr, not about position in the file, comments, etc.
    """
    import os, subprocess, tempfile, urllib, polib, re
    from mr.developer.common import which

    vcstype = vcsurl.split(" ")[0]
    vcsextra = ""
    if len(vcsurl.split(" ")) > 2:
        vcsextra = " ".join(vcsurl.split(" ")[2:])
    vcsurl = vcsurl.split(" ")[1]
    pofiles = []

    def visit(pofiles, dirname, names):
        pofiles.extend(
            map(
                lambda n: os.path.join(dirname, n),
                filter(lambda n: n.endswith(".po") or n.endswith(".pot"), names),
            )
        )

    os.path.walk(__path__[0], visit, pofiles)
    basepath = __path__[0][: __path__[0].rfind(__name__) + len(__name__)]

    for pofile in pofiles:
        # out = subprocess.Popen(("/usr/bin/svn info %s" % pofile).split(" "), stdout=subprocess.PIPE).stdout.read()
        # out = out[out.find('URL: ')+5:]
        # pofileurl = out[:out.find('\n')]
        proto, string = urllib.splittype(vcsurl)
        host, path = urllib.splithost(string)
        relpath = os.path.relpath(pofile, basepath)
        pofileurl = os.path.join(vcsurl, relpath)

        tmp, tmppath = tempfile.mkstemp(text=True)
        if vcstype == "svn":
            urllib.urlretrieve(pofileurl, tmppath)
        elif vcstype == "git":
            cmd = which("git")
            branchmatch = re.search("branch=(\S*)", vcsextra)
            if branchmatch:
                branch = branchmatch.group(1)
            else:
                branch = "master"
            cmdline = "%s show %s:%s" % (cmd, branch, relpath)
            err, errtmppath = tempfile.mkstemp(text=True)
            out = subprocess.Popen(
                cmdline.split(" "), stdout=subprocess.PIPE, stderr=err, cwd=basepath
            ).stdout.read()
            err = open(errtmppath).read()
            if err:
                print (err)
                return
            outfile = open(tmppath, "w")
            outfile.write(out)
            outfile.close()
        else:
            print ("Sorry, %s is not supported yet.")
            return

        polocal = polib.pofile(pofile)
        povcs = polib.pofile(tmppath)

        diff = []

        for entryvcs in povcs:
            if entryvcs.obsolete:
                if entryvcs not in polocal.obsolete_entries():
                    diff += ['-#msgid "%s"' % entryvcs.msgid]
                    diff += ['-#msgstr "%s"' % entryvcs.msgstr]
                    diff += [""]
                else:
                    continue
            entrylocal = polocal.find(entryvcs.msgid)
            if not entrylocal:
                if entryvcs in polocal.obsolete_entries():
                    diff += ['+#msgid "%s"' % entryvcs.msgid]
                    diff += ['+#msgstr "%s"' % entryvcs.msgstr]
                    diff += [""]
                else:
                    diff += ['-msgid "%s"' % entryvcs.msgid]
                    diff += ['-msgstr "%s"' % entryvcs.msgstr]
                    diff += [""]
            else:
                if not entryvcs.msgstr == entrylocal.msgstr:
                    diff += [' msgid "%s"' % entryvcs.msgid]
                    diff += ['-msgstr "%s"' % entryvcs.msgstr]
                    diff += ['+msgstr "%s"' % entrylocal.msgstr]
                    diff += [""]
        for entrylocal in filter(lambda e: e not in povcs, polocal):
            if entrylocal in povcs.obsolete_entries():
                # XXX WTF? Iterating over a POFile yields obsolete entries, but
                # checking for an obsolete entry with 'in' returns False. This
                # means we have already iterated over the obsolete entries but
                # the above filter returns them again. We need to explicity skip
                # them.
                #
                # (Pdb) entry.obsolete
                # 1
                # (Pdb) [e for e in povcs if e == entry]
                # [<polib.POEntry object at 0x2f7d850>]
                # (Pdb) entry in povcs
                # False
                continue
            if entrylocal.obsolete:
                diff += ['+#msgid "%s"' % entrylocal.msgid]
                diff += ['+#msgstr "%s"' % entrylocal.msgstr]
                diff += [""]
            else:
                diff += ['+msgid "%s"' % entrylocal.msgid]
                diff += ['+msgstr "%s"' % entrylocal.msgstr]
                diff += [""]

        if diff:
            out = [""]
            out += ["Index: %s" % pofile]
            out += [
                "==================================================================="
            ]
            out += ["--- repository"]
            out += ["+++ working copy"]
            out += diff
            out += [""]
            print ("\n".join(out))

        os.remove(tmppath)


def updateTranslations(ignore):
    br = Browser("http://transifex.syslab.com")
    try:
        br.getControl(name="username").value = sys.argv[1]
        if len(sys.argv) < 3:
            import getpass

            br.getControl(name="password").value = getpass.getpass()
        else:
            br.getControl(name="password").value = sys.argv[2]
    except IndexError:
        print "Usage: %s [Your Transifex username] [Your Transifex password]"
        return 1
    br.getControl("Sign in").click()
    for domain, url_tmpl in (
        (
            "recensio",
            "http://transifex.syslab.com/projects/p/recensio/resource/recensiopot/l/%s/download/",
        ),
        (
            "plone",
            "http://transifex.syslab.com/projects/p/recensio/resource/plonepot/l/%s/download/",
        ),
    ):
        for lang in ("de", "en", "fr"):
            print "Getting %s for %s" % (domain, lang)
            br.open(url_tmpl % lang)
            file(
                pkg_resources.resource_filename(
                    __name__, "locales/%s/LC_MESSAGES/%s.po" % (lang, domain)
                ),
                "w",
            ).write(br.contents)
