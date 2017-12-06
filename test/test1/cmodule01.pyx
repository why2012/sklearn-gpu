# coding: utf-8
# import numpy as np
# cimport numpy as np

cdef extern from "math.h":
	float cosf(float)
	float sinf(float)
	float acosf(float theta)
	double sin(double)

cdef extern from "funclib.h":
	float a_square(float)

cdef extern from "cudalib.h":
	int cuCheck()

cpdef float add_a_b(float a, float b) except *:
	return a + b

cpdef float cos(float theta) except *:
	return cosf(theta)

cpdef float square(float a) except *:
	return a_square(a)

# cpdef float npsum(np.ndarray[np.float64_t, ndim=1] arr) except *:
# 	return np.sum(arr)

cpdef void gpu_check() except *:
	cuCheck()