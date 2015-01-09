#include <stdio.h>
#include <stdlib.h>
#include <time.h>


extern "C" {
void *  alloc_gpu_mem( size_t N)
{
	void*d;
	int size = N *sizeof(float);
	int err;

	err = cudaMalloc(&d, size);
	if (err != 0) printf("cuda malloc error: %d\n", err);

	return d;
}}


// see kernels.cu for launch_kernel functions

extern "C" {
void host2gpu(float * a, void * da, size_t N)
{
	int size = N * sizeof(float); 
	int err;

	err = cudaMemcpy(da, a, size, cudaMemcpyHostToDevice);
	if (err != 0) printf("load mem: %d\n", err);

}}
extern "C"{
void gpu2host(float *c, void *d_c, size_t N)
{
	cudaError_t  err;
	int size = N*sizeof(float);
	// copy result back
	err = cudaMemcpy(c, d_c, size, cudaMemcpyDeviceToHost);
	if (err != 0) {printf("cpy mem back %d\n", err);
		//cudaError_t cudaGetLastError(void);
		printf("%s\n", cudaGetErrorString(cudaGetLastError()));
	}
}}
extern "C"{
void free_gpu_mem(void *d)
{
	cudaFree(d);
}}	

extern "C"{
void free_mem(void *d)
{
	free(d);
}}	


extern "C"{
void get_cuda_info()
{
	int count, i;
	const int kb = 1024;
	const int mb = kb*kb;

	cudaGetDeviceCount(&count);
	for(i=0; i<count;i++)
	{
		cudaDeviceProp props;
		cudaGetDeviceProperties(&props, i);
		printf("\nDevice Details:\n");
		printf("%d : %s : %d : %d\n", i, props.name, props.major, props.minor);
		printf("Number of Processors: %d\n", props.multiProcessorCount);
		printf("Global Memory: %f mb\n", (float) props.totalGlobalMem /mb);
		printf("Shared Memory: %f kb \n", (float) props.sharedMemPerBlock / kb);
		printf("Constant Memory: %f kb\n", (float) props.totalConstMem / kb);
		printf("Block registers: %d\n", props.regsPerBlock);

		printf("Warp size: %d\n", props.warpSize);
		printf("Threads per block: %d\n", props.maxThreadsPerBlock);
		printf("Max block dimensions: [%d, %d, %d]\n", props.maxThreadsDim[0], props.maxThreadsDim[1], props.maxThreadsDim[2]);
		printf("Max grid dimensions: [%d, %d, %d]\n", props.maxGridSize[0], props.maxGridSize[1], props.maxGridSize[2]);

		printf("Clock Rate: %d\n", props.memoryClockRate);
		printf("Memory Bus Widths %d\n", props.memoryBusWidth);


		printf("\n");
	}
}}


extern "C"{
void distance3D(float *x, float *y, float *dist, size_t nx, size_t ny, size_t T, size_t k)
{
	int n, m, i, j;
	float d, d_;

	for (n=0; n<nx; n++){
		for (m=0; m<ny; m++){
			d = 0;
			for (i=0; i<T; i++){
				d_ = 0;
				for (j =0; j<k; j++){
					d_ += pow((x[n*T*k + i*k + j] - y[m*T*k + i*k + j]), 2);
				}
				d += sqrt(d_);
			}
			dist[n*ny + m] = d;
		}
	}
}}
