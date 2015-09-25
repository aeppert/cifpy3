"""
CIF.Worker.Plugins
Plugins take in an observable and may or may not generate additional observables based on data from the original
observable.
The additional observables should reference the original observable's ID using the 'related' field.
"""

__package__ = "cif.worker.plugins"
__author__ = 'James DeVincentis <james.d@hexhost.net>'

import os

plugins = {}

plugindir = os.path.dirname(__file__)
pluginfiles = os.listdir(plugindir)
for plugin in pluginfiles:
    if plugin.endswith('.py') and plugin != "__init__.py":
        module = __import__("cif.worker.plugins.{0}".format(os.path.splitext(plugin)[0]), fromlist=["process"])
        plugins[os.path.splitext(plugin)[0]] = module.process
