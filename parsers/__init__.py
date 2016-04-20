# coding=utf-8

import os, sys
import importlib
import inspect
import re
from ..data import Parser

def pyfiles():
    ret = []
    for name in os.listdir(os.path.dirname(__file__)):
        if name and name[0] != "_" and name.lower().endswith(".py"):
            ret.append(name)
    return ret

def see():
    ret = []
    a = sys.modules.keys()
    for name in a:
        if "parsers" in name:
            ret.append(name)
    return ret
####################################

# load all parsers in 'parser' folder
parserDir = os.path.dirname(__file__)
appendFlag = parserDir not in sys.path              # add 'parser' folder to sys.path
if appendFlag: sys.path.append(parserDir)
moda = []
for name in pyfiles():
    # load modules
    modname = re.sub("\.py$", "", name)
    try:
        mod = importlib.import_module(modname)
        moda.append((modname, mod))
    except Exception, data:
        print >> sys.stderr, "import file '%s' failed: %s" % (name, data.message)
        raise
if appendFlag: sys.path.remove(parserDir)           # remove 'parser' folder from sys.path

# find parsers
for modname, mod in moda:
    for value in mod.__dict__.values():
        try:
            if callable(value) and inspect.isclass(value) and issubclass(value, Parser):
                p = value()
                name = p.name()
                if name is None: name = modname
                Parser.add(name, p)
        except:
            print >> sys.stderr, "Warn: load parser failed with value '%s'" % value