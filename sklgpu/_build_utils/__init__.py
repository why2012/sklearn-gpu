from __future__ import division, print_function, absolute_import

import os

from .cuda_support import get_cuda_support

CUDA, cuda_build_ext = get_cuda_support()