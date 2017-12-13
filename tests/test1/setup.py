from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from cuda_support import get_cuda_support
import numpy

CUDA, cuda_build_ext = get_cuda_support()

ext_modules = [
	Extension("cmodule01", ["cmodule01.pyx", "funclib.cpp", "cudalib.cu"], 
		library_dirs = [CUDA['lib64']], 
		libraries = ['cudart', 'cuda'], 
		# runtime_library_dirs = [CUDA['lib64']],
		extra_compile_args = {'cc': [], 'nvcc': ['-arch=sm_30', '-c', '-Xcompiler', '/MD', '-O3']},
		include_dirs = [CUDA['include'], numpy.get_include()],
		language = "c++"
		), 
	Extension("cmodule02", ["cmodule02.pyx"],
		include_dirs = [numpy.get_include()])
]
setup(
    name='cmodules',
    version = "0.01",  
    description = '',
    cmdclass = {'build_ext': cuda_build_ext},
    ext_modules = ext_modules,
    #ext_modules = cythonize('cmodule01.pyx'),
    #zip_safe = False
)