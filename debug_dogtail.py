#!/usr/bin/python2 -i

import sys
import os

def list_dirs(path):
    return [
        os.path.join(path, x)
        for x in os.listdir(path)
        if os.path.isdir(os.path.join(path, x))
    ]

os.environ["DISPLAY"] = ":1"

# Add dogtail import path
for d in list_dirs('dogtail'):
    sys.path.append(d)
# Add teres import path
sys.path.append('teres')

try:
    app_name = sys.argv[1]
except IndexError:
    app_name = "anaconda"

import dogtail
import dogtail.utils
dogtail.utils.enableA11y()
import dogtail.config
dogtail.config.config.childrenLimit = 10000
from dogtail.predicate import GenericPredicate
import dogtail.tree

app_node = dogtail.tree.root.child(roleName="application", name=app_name)

from anabot.runtime.functions import waiton, waiton_all, getnode, getnodes, getparent, getparents, getsibling, hold_key, release_key, dump
from anabot.runtime.translate import set_languages, tr
set_languages(['cs_CZ', 'cs'])