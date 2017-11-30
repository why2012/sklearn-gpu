# coding: utf-8

cdef class Function:
	cdef float const1
	cdef public float const2
	const3 = 3.0

	cpdef float sub_a_b(self, float a, float b) except *:
		return a - b

	def mul_a_b(self, a, b):
		return a * b