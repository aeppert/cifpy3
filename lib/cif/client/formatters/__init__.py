import os

formatters = {}

plugindir = os.path.dirname(__file__)
pluginfiles = os.listdir(plugindir)
for plugin in pluginfiles:
    if plugin.endswith('.py') and plugin != "__init__.py":
        module = __import__("cif.client.formatters.{0}".format(os.path.splitext(plugin)[0]), fromlist=["process"])
        formatters[os.path.splitext(plugin)[0]] = module.process

list = formatters.keys()