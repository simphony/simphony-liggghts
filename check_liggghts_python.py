import sys
import site
print site.USER_SITE
print sys.path

import liggghts
l = liggghts.liggghts(cmdargs=["-log", "none"])
l.command("print \"Python-LIGGGHTS interface is working\"")
