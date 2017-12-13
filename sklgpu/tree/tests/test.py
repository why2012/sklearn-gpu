import numpy as np
import math
import sys
sys.path.append('../../../')
import sklgpu.tree._tree_gpu as _tree_gpu

print(_tree_gpu.add_a_b(1, 2))
print(_tree_gpu.cos(math.pi))
print(_tree_gpu.square(2))
print(_tree_gpu.npsum(np.array([1,2,3], dtype=np.float64)))
_tree_gpu.gpu_check()