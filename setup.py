#!/usr/bin/env python

import os
from setuptools import setup, Extension
import setuptools.command.install

__base__ = {
    "name": "python3_midi",
    "version": "v0.2.5",
    "python_requires": ">=3.5",
    "description": "Python MIDI API",
    "author": "giles hall",
    "author_email": "ghall@csh.rit.edu",
    "package_dir": {"python3_midi": "src"},
    "py_modules": [
        "python3_midi.containers",
        "python3_midi.__init__",
        "python3_midi.events",
        "python3_midi.util",
        "python3_midi.fileio",
        "python3_midi.constants",
    ],
    "ext_modules": [],
    "ext_package": "",
    "scripts": ["scripts/mididump.py", "scripts/mididumphw.py", "scripts/midiplay.py"],
}

# this kludge ensures we run the build_ext first before anything else
# otherwise, we will be missing generated files during the copy
class Install_Command_build_ext_first(setuptools.command.install.install):
    def run(self):
        self.run_command("build_ext")
        return setuptools.command.install.install.run(self)


def setup_alsa(ns):
    # scan for alsa include directory
    dirs = ["/usr/include", "/usr/local/include"]
    testfile = "alsa/asoundlib.h"
    alsadir = None
    for _dir in dirs:
        tfn = os.path.join(_dir, testfile)
        if os.path.exists(tfn):
            alsadir = _dir
            break
    if not alsadir:
        print(
            "Warning: could not find asoundlib.h, not including ALSA sequencer support!"
        )
        return
    srclist = ["src/sequencer_alsa/sequencer_alsa.i"]
    include_arg = "-I%s" % alsadir
    extns = {
        "libraries": ["asound"],
        "swig_opts": [include_arg],
        #'extra_compile_args':['-DSWIGRUNTIME_DEBUG']
    }
    ext = Extension("_sequencer_alsa", srclist, **extns)
    ns["ext_modules"].append(ext)

    ns["package_dir"]["python3_midi.sequencer"] = "src/sequencer_alsa"
    ns["py_modules"].append("python3_midi.sequencer.__init__")
    ns["py_modules"].append("python3_midi.sequencer.sequencer")
    ns["py_modules"].append("python3_midi.sequencer.sequencer_alsa")
    ns["ext_package"] = "python3_midi.sequencer"
    ns["cmdclass"] = {"install": Install_Command_build_ext_first}


def configure_platform():
    from sys import platform

    ns = __base__.copy()
    # currently, only the ALSA sequencer is supported
    if platform.startswith("linux"):
        # setup_alsa(ns)
        pass
    else:
        print("No sequencer available for '%s' platform." % platform)
    return ns


if __name__ == "__main__":
    setup(**configure_platform())
