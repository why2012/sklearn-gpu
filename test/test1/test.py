# coding: utf-8
import cmodule01
import cmodule02
import numpy as np
import math

print(cmodule01.add_a_b(1, 2))
print(cmodule01.cos(math.pi))
print(cmodule02.Function().sub_a_b(8, 2))
print(cmodule02.Function().mul_a_b(8, 2))
print(cmodule02.Function().const2)
print(cmodule01.square(2))
print(cmodule01.npsum(np.array([1,2,3], dtype=np.float64)))
cmodule01.gpu_check()