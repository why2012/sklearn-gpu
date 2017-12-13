#include "cudalib.h"
#include <cuda_runtime.h>
#include <stdio.h>
#include <time.h>
#ifdef _WIN32
	#include <windows.h>
#else
	#include <sys/time.h>
#endif
#ifdef WIN32
	int gettimeofday(struct timeval* tp, void* tzp) {
		time_t clock;
		struct tm tm;
		SYSTEMTIME wtm;
		GetLocalTime(&wtm);
		tm.tm_year = wtm.wYear - 1900;
		tm.tm_mon = wtm.wMonth - 1;
		tm.tm_mday = wtm.wDay;
		tm.tm_hour = wtm.wHour;
		tm.tm_min = wtm.wMinute;
		tm.tm_sec = wtm.wSecond;
		tm.tm_isdst = -1;
		clock = mktime(&tm);
		tp->tv_sec = clock;
		tp->tv_usec = wtm.wMilliseconds * 1000;
		return 0;
	}
#endif

#define CHECK(call)															\
{																			\
	const cudaError_t error = call;											\
	if (error != cudaSuccess) {												\
		printf("Error: %s:%d, ", __FILE__, __LINE__);						\
		printf("code:%d, reason: %s\n", error, cudaGetErrorString(error));	\
		exit(EXIT_FAILURE);													\
	}																		\
}

double cpuSeconds() {
	struct timeval tp;
	gettimeofday(&tp, NULL);
	return ((double)tp.tv_sec + (double)tp.tv_usec * 1.e-6);
}

__global__ void _checkIndex() {
	printf("threadIdx:(%d, %d, %d) blockIdx:(%d, %d, %d) blockDim:(%d, %d, %d) gridDim:(%d, %d, %d)\n",
		threadIdx.x, threadIdx.y, threadIdx.z, blockIdx.x, blockIdx.y, blockIdx.z, blockDim.x, blockDim.y, blockDim.z,
		gridDim.x, gridDim.y, gridDim.z);
}

void checkIndex() {
	printf("GPU Side Invocation Check.\n");
	dim3 block(3);
	dim3 grid((6 + block.x - 1) / block.x);
	double iStart = cpuSeconds();
	_checkIndex<<<grid, block>>>();
	cudaDeviceSynchronize();
	double iEnd = cpuSeconds();
	printf("checkIndex<<<grid, block>>> time elapsed %f.", iEnd - iStart);
	cudaDeviceReset();
}

void printDeviceProp() {
	int deviceCount = 0;
	CHECK(cudaGetDeviceCount(&deviceCount));
	if (deviceCount == 0) {
		printf("There are no available devices that support CUDA\n");
	} else {
		printf("Detected %d CUDA Capable device(s)\n", deviceCount);
	}
	int dev = 0, driverVersion = 0, runtimeVersion = 0;
	cudaSetDevice(dev);
	cudaDeviceProp deviceProp;
	cudaGetDeviceProperties(&deviceProp, dev);
	printf("Device: %d, \"%s\"\n", dev, deviceProp.name);
	cudaDriverGetVersion(&driverVersion);
	cudaRuntimeGetVersion(&runtimeVersion);
	printf("	CUDA Driver Version / RuntimeVersion 	%d.%d / %d.%d\n", driverVersion / 1000, (driverVersion % 100) / 10, 
		runtimeVersion / 1000, (runtimeVersion % 100) / 10);
	printf("	Total amount of global memory:	%.2f GB (%llu bytes)\n", (float)deviceProp.totalGlobalMem / (pow(1024.0, 3)),
		(unsigned long long) deviceProp.totalGlobalMem);
	printf("	Multiprocessor Count: %d\n", deviceProp.multiProcessorCount);
	printf("	GPU Clock rate:	%.0f MHz(%.2f GHz)\n", deviceProp.clockRate * 1e-3f, deviceProp.clockRate * 1e-6f);
	printf("	Memory Clock rate:	%.0f MHz\n", deviceProp.memoryClockRate * 1e-3f);
	printf("	Memory Bus Width:	%d-bit\n", deviceProp.memoryBusWidth);
	printf("	Warp size:	%d\n", deviceProp.warpSize);
	printf("	Maximum number of threads per multiprocessor: %d\n", deviceProp.maxThreadsPerMultiProcessor);
	printf("	Maximum number of threads per block: %d\n", deviceProp.maxThreadsPerBlock);
	printf("	Maximum size of each dimension of a block: %d x %d x %d\n", deviceProp.maxThreadsDim[0], 
		deviceProp.maxThreadsDim[1], deviceProp.maxThreadsDim[2]);
	printf("	Maximum size of each dimension of a grid: %d x %d x %d\n", deviceProp.maxGridSize[0], 
		deviceProp.maxGridSize[1], deviceProp.maxGridSize[2]);
}

__global__ void reduceNeighbor(int* g_idata, int* g_odata, unsigned int n) {
	unsigned int tid = threadIdx.x;
	unsigned int idx = threadIdx.x + blockIdx.x * blockDim.x;
	int* idata = g_idata + blockIdx.x * blockDim.x;
	if (idx >= n) return;
	for (int stride = 1; stride < blockDim.x; stride *= 2) {
		if ((tid % (2 * stride)) == 0) {
			idata[tid] += idata[tid + stride];
		}
		__syncthreads();
	}
	if (tid == 0) g_odata[blockIdx.x] = idata[0];
}

__global__ void reduceNeighborPlus(int* g_idata, int* g_odata, unsigned int n) {
	unsigned int tid = threadIdx.x;
	unsigned int idx = threadIdx.x + blockIdx.x * blockDim.x;
	int* idata = g_idata + blockIdx.x * blockDim.x;
	if (idx >= n) return;
	for (int stride = 1; stride < blockDim.x; stride *= 2) {
		int index = 2 * stride * tid;
		if (index < blockDim.x) {
			idata[index] += idata[index + stride];
		}
		__syncthreads();
	}
	if (tid == 0) g_odata[blockIdx.x] = idata[0];
}

void __reduceCheck(int blockSize = 512) {
	int size = 1 << 24;
	dim3 block(blockSize);
	dim3 grid((size + block.x - 1) / block.x);
	int gpu_sum = 0;
	size_t bytes = size * sizeof(int);
	int* h_idata = (int*)malloc(bytes);
	int* h_odata = (int*)malloc(grid.x * sizeof(int));
	for (int i = 0; i < size; i++) {
		h_idata[i] = (int)(rand() & 0xff);
	}
	int* d_idata = NULL;
	int* d_odata = NULL;
	cudaMalloc((void**)&d_idata, bytes);
	cudaMalloc((void**)&d_odata, grid.x * sizeof(int));

	cudaMemcpy(d_idata, h_idata, bytes, cudaMemcpyHostToDevice);
	double iStart = cpuSeconds();
	reduceNeighbor<<<grid, block>>>(d_idata, d_odata, size);
	cudaDeviceSynchronize();
	double iEnd = cpuSeconds();
	cudaMemcpy(h_odata, d_odata, grid.x * sizeof(int), cudaMemcpyDeviceToHost);
	for (int i = 0; i < grid.x; i++) gpu_sum += h_odata[i];
	printf("gpu Neighbored Reduce elapsed %.2f s gpu_sum: %d <<<grid %d block %d>>>\n", iEnd - iStart, gpu_sum, grid.x, block.x);
	
	cudaMemcpy(d_idata, h_idata, bytes, cudaMemcpyHostToDevice);
	iStart = cpuSeconds();
	reduceNeighborPlus<<<grid, block>>>(d_idata, d_odata, size);
	cudaDeviceSynchronize();
	iEnd = cpuSeconds();
	cudaMemcpy(h_odata, d_odata, grid.x * sizeof(int), cudaMemcpyDeviceToHost);
	gpu_sum = 0;
	for (int i = 0; i < grid.x; i++) gpu_sum += h_odata[i];
	printf("gpu Neighbored Reduce Plus elapsed %.2f s gpu_sum: %d <<<grid %d block %d>>>\n", iEnd - iStart, gpu_sum, grid.x, block.x);
	
	free(h_idata);
	free(h_odata);
	cudaFree(d_idata);
	cudaFree(d_odata);
	cudaDeviceReset();
}

int cuCheck() {
	printDeviceProp();
	printf("Reduce Check\n");
	__reduceCheck();
	return 0;
}