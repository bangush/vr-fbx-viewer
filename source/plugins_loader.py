import importlib
import importlib.util
import os
import sys

PluginFolder = "./plugins"
MainModule = "__init__"


def get_plugins():
    plugins = {}
    possibleplugins = os.listdir(PluginFolder)
    for i in possibleplugins:
        location = os.path.join(PluginFolder, i)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            continue

        sys.path.append(location)
        spec = importlib.util.spec_from_file_location(MainModule, os.path.join(location, MainModule + ".py"))
        info = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(info)
        plugins[i] = info
    return plugins


# example
# for i in pluginloader.getPlugins():
#     print("Loading plugin " + i["name"])
#     plugin = pluginloader.loadPlugin(i)
#     plugin.run()