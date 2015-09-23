__author__ = 'James DeVincentis <james.d@hexhost.net>'

import os

meta = {}

plugindir = os.path.dirname(__file__)
pluginfiles = os.listdir(plugindir)
for plugin in pluginfiles:
    if plugin.endswith('.py') and plugin != "__init__.py":
        module = __import__("cif.worker.meta.{0}".format(os.path.splitext(plugin)[0]), fromlist=["process"])
        meta[os.path.splitext(plugin)[0]] = module.process
del plugindir, pluginfiles