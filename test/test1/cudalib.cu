#include "cudalib.h"
#include <stdio.h>

float a_triple(float a) {
	return a * a * a;
}

float a_triple_plus_10(float a) {
	return a * a * a + 10;
}

__global__ void helloworld_gpu() {
	printf("Hello World from GPU!\n");
}

void helloworld() {
	printf("Hello World from CPU!\n");
	helloworld_gpu<<<1,10>>>();
	cudaDeviceReset();
}