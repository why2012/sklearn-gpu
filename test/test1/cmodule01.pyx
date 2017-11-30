# coding: utf-8
cdef extern from "math.h":
	float cosf(float theta)
	float sinf(float theta)
	float acosf(float theta)

def add_a_b(a, b):
	return a + b

def cos(theta):
	return cosf(theta)