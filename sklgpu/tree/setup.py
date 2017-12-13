import os

import numpy
from numpy.distutils.misc_util import Configuration
from _build_utils import CUDA

def configuration(parent_package="", top_path=None):
    config = Configuration("tree", parent_package, top_path)

    config.add_extension("_tree_gpu", ["tests/cmodule01.pyx", "tests/funclib.cpp", "tests/cudalib.cu"], 
        library_dirs = [CUDA['lib64']], 
        libraries = ['cudart', 'cuda'], 
        # runtime_library_dirs = [CUDA['lib64']],
        extra_compile_args = {'cc': [], 'nvcc': ['-arch=sm_30', '-c', '-Xcompiler', '/MD', '-O3']},
        include_dirs = [CUDA['include'], numpy.get_include()],
        language = "c++"
    )

    config.add_subpackage("tests")

    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration().todict())