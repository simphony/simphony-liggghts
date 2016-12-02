import sys
import site
print site.USER_SITE
print sys.path
for p in sys.path()
    print p
    try:
        print os.listdir()
    except:
        print "can't read"
import liggghts

l = liggghts.liggghts(cmdargs=["-log", "none"])
l.command("print \"Python-LIGGGHTS interface is working\"")
