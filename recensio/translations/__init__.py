  # -*- extra stuff goes here -*-
from zope.i18nmessageid import MessageFactory
from zc.testbrowser.browser import Browser
import pkg_resources
import sys

RecensioMessageFactory = MessageFactory('recensio')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""

def podiff(svnurl):
    """ Shows differences between the po files in the working copy of this
        package and their counterparts in the svn repository. Only cares
        about msgid and msgstr, not about position in the file, comments, etc.
    """
    import os, subprocess, sys, tempfile, urllib, polib

    svnurl = svnurl.split(' ')[-1]
    pofiles = []
    def visit(pofiles, dirname, names):
        pofiles.extend(
            map(lambda n: os.path.join(dirname, n),
                filter(
                    lambda n: n.endswith('.po') or n.endswith('.pot'), names)))
    os.path.walk(__path__[0], visit, pofiles)
    basepath = __path__[0][:__path__[0].rfind(__name__)+len(__name__)]

    for pofile in pofiles:
        #out = subprocess.Popen(("/usr/bin/svn info %s" % pofile).split(" "), stdout=subprocess.PIPE).stdout.read()
        #out = out[out.find('URL: ')+5:]
        #pofileurl = out[:out.find('\n')]
        proto, string = urllib.splittype(svnurl)
        host, path = urllib.splithost(string)
        relpath = os.path.relpath(pofile, basepath)
        pofileurl = os.path.join(svnurl, relpath)

        tmp, tmppath = tempfile.mkstemp(text=True)
        urllib.urlretrieve(pofileurl, tmppath)

        polocal = polib.pofile(pofile)
        posvn = polib.pofile(tmppath)

        diff = []

        for entrysvn in posvn:
            entrylocal = polocal.find(entrysvn.msgid)
            if not entrylocal:
                diff += ['-msgid "%s"' % entrysvn.msgid]
                diff += ['-msgstr "%s"' % entrysvn.msgstr]
                diff += ['']
            else:
                if not entrysvn.msgstr == entrylocal.msgstr:
                    diff += [' msgid "%s"' % entrysvn.msgid]
                    diff += ['-msgstr "%s"' % entrysvn.msgstr]
                    diff += ['+msgstr "%s"' % entrylocal.msgstr]
                    diff += ['']
        for entrylocal in filter(lambda e: not posvn.find(e.msgid), polocal):
            diff += ['+msgid "%s"' % entrylocal.msgid]
            diff += ['+msgstr "%s"' % entrylocal.msgstr]
            diff += ['']

        if diff:
            out = ['']
            out += ['Index: %s' % pofile]
            out += ['===================================================================']
            out += ['--- repository']
            out += ['+++ working copy']
            out += diff
            out += ['']
            print("\n".join(out))

        os.remove(tmppath)

def updateTranslations(ignore):
    br = Browser('http://transifex.syslab.com')
    try:
        br.getControl(name='username').value = sys.argv[1]
        if len(sys.argv) < 3:
            import getpass
            br.getControl(name='password').value = getpass.getpass()
        else:
            br.getControl(name='password').value = sys.argv[2]
    except IndexError:
        print "Usage: %s [Your Transifex username] [Your Transifex password]"
        return 1
    br.getControl('Sign in').click()
    for domain, url_tmpl in (('recensio', 'http://transifex.syslab.com/projects/p/recensio/resource/recensiopot/l/%s/download/'), ('plone', 'http://transifex.syslab.com/projects/p/recensio/resource/plonepot/l/%s/download/')):
      for lang in ('de', 'en', 'fr'):
        print "Getting %s for %s" % (domain, lang)
        br.open(url_tmpl % lang)
        file(pkg_resources.resource_filename(__name__, 'locales/%s/LC_MESSAGES/%s.po' % (lang, domain)), 'w').write(br.contents)
