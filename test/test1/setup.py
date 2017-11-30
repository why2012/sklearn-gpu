from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
#from Cython.Build import cythonize

ext_modules = [Extension("cmodule01", ["cmodule01.pyx"]), Extension("cmodule02", ["cmodule02.pyx"])]
setup(
    name='cmodules',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
    #ext_modules = cythonize('cmodule01.pyx')
)