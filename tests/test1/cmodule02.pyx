# coding: utf-8
import numpy as np
cimport numpy as np

cdef class Function:
	cdef float const1
	cdef public float const2
	const3 = 3.0

	cpdef float sub_a_b(self, float a, float b) except *:
		return a - b

	def mul_a_b(self, a, b):
		return a * b


cpdef float npsum(np.ndarray[np.float64_t, ndim=1] arr) except *:
	return np.sum(arr)