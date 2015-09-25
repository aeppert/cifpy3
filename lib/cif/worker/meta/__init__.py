__author__ = 'James DeVincentis <james.d@hexhost.net>'

import os

meta = {}

pluginfiles = os.listdir(os.path.dirname(__file__))
for plugin in pluginfiles:
    if plugin.endswith('.py') and plugin != "__init__.py":
        module = __import__("cif.worker.meta.{0}".format(os.path.splitext(plugin)[0]), fromlist=["process"])
        meta[os.path.splitext(plugin)[0]] = module.process
del pluginfiles
