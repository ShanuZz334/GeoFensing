#!/usr/bin/env python

"""
pyton_setup.py file for SWIG ultimateFaceSDK
You must run this file from 'binaries/os/arch' (e.g. 'binaries/windows/x86_64') folder.
"""

from distutils.core import setup, Extension
from distutils import sysconfig
from Cython.Distutils import build_ext
from sys import platform
import os

# Shared library name
print("Your platform: %s" % platform)
LIBNAME = 'ultimateFaceSDK'

# Do not add suffix (e.g. 'cp36-win_amd64')
class NoSuffixBuilder(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        suffix = sysconfig.get_config_var('EXT_SUFFIX')
        ext = os.path.splitext(filename)[1]
        return filename.replace(suffix, "") + ext

ultimateFaceSDK_module = Extension('_ultimateFaceSDK',
                           sources=[os.path.abspath('../../../python/ULTFACE-SDK-API-PUBLIC-SWIG_python.cxx')],
                           include_dirs=['../../../cpp'],
                           language='c++11',
                           library_dirs=['.'],
                           libraries=[LIBNAME]
                           )

setup (name = 'ultimateFaceSDK',
       version = '0.0.1',
       author      = "Doubango AI",
       description = """ultimateFaceSDK for python""",
       ext_modules = [ultimateFaceSDK_module],
       py_modules = ["ultimateFaceSDK"],
       cmdclass={"build_ext": NoSuffixBuilder},
       )