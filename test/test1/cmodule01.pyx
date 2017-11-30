# coding: utf-8
cdef extern from "math.h":
	float cosf(float)
	float sinf(float)
	float acosf(float theta)
	double sin(double)

cdef extern from "funclib.h":
	float a_square(float)

cdef extern from "cudalib.h":
	float a_triple(float)
	float a_triple_plus_10(float)
	void helloworld()

cpdef float add_a_b(float a, float b) except *:
	return a + b

cpdef float cos(float theta) except *:
	return cosf(theta)

cpdef float square(float a) except *:
	return a_square(a)

cpdef float triple(float a) except *:
	return a_triple(a)

cpdef float triple_plus_10(float a) except *:
	return a_triple_plus_10(a)

cpdef void hello_world() except *:
	helloworld()