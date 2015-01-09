#include <stdio.h>
#include <stdlib.h>
#include <time.h>

__device__ float ed1D(float *x, float *y, int K){
	int i;
	float d=0;

	for(i=0;i<K;i++)
		d += pow((x[i] - y[i]), 2);
	
	return sqrt(d);
}

__device__ float ed2D(float *x, float *y, int T, int K){
	int i;
	float d=0;
	
	for (i =0; i < T; i++){	
		d += ed1D(&x[i*K], &y[i*K], K);
	}

	return d;
}

#define R 10
__device__ float DTW(float *x, float *y, int T, int K){
	int i, j;
	float dd[2*R+1][2]; // use this to walk through the dtw matrix one column at a time (only for values within constraint)
	float n1, n2, n3, min; // dtw neighbours

	// first column is just distances (between first R+1 of x-series and first frame of y)	
	dd[0][0] = ed1D(x, y, K);
	for(j=1;j<R+1;j++){
		dd[j][0] = ed1D(&x[j*K], y, K) + dd[j-1][0];
	}

	// now we step across the y-series.  for each frame, we compute the next column of the dtw matrix, alternating its placement in the one of two columns on dd
	
	int v = 1; // the next column of dtw-matrix is written into  this column of dd
	int w = 0;

	for(i=1;i<T;i++){
		// the diagonal of the dtw matrix in (i, j) is (i, 0).  i+j takes values from R below to R above the diagonal (indexing the rows (frames of x-series) in DTW matrix).  j+R indexes dd.
		for(j= -R ;j< R+1 ;j++){
			// bottom row is just the distancess (between first R+1 of y-series and first frame of x)
			if (i+j==0){
				dd[j+R][v] = ed1D(x, &y[i*K], K) + dd[0][w];
			}
			
			else if (i+j > 0 && i+j < T){
				
				n1 = dd[j+R+1][w];
				n2 = dd[j+R][w];
				n3 = dd[j+R-1][v];
				
				min = fminf(n1, n2);
				min = fminf(min, n3);	
				
				dd[j][v] = ed1D(&x[(i+j)*K], &y[i*K], K) + min;
			}
		}
		v = (v+1)%2;
		w = (w+1)%2;
	}
	return dd[2*R][w];
}

/* 	KNN	*/
__global__ void knn(float *train, float *test, float *dist, size_t N_train, size_t T, size_t K, size_t d_mode)
{
	/* each block processes an instance of test (load it into shared)
	   each thread loads a few elements of the test instance into shared memory
	   each thread computes the distance between the test instance and a train instance, until all train instances have been seen.

	   Assumptions:
	     - NUM_THREADS = N_TRAIN (so a single block can process the whole train set).
	*/

	extern __shared__ float Q[]; // query (test instance);

	int NUM_THREADS = N_train;
	int bx = blockIdx.x; // indexes the test instance (we have as many blocks as test instances)
	int tx = threadIdx.x; // indexes the train instance
	int M = T*K; // size of a test instance (to load into shared memory)
	int S = (T + NUM_THREADS-1) / NUM_THREADS; //number of frames in time series loaded by each thread
	int rr = S*K; // num elements each thread must load
	float d;
	int i;

	// load test instance into shared (each thread loads R elements of test instance, corresponding to S rows of Q)
	for (i=0; i < rr; i++){
		int frame_num = tx*S + i/K;
		if (frame_num < T)
			Q[(tx*S + i/K)*K + (i%K)] = test[bx * M + tx * rr + i];
	}
	__syncthreads();	
	
	// compute distance between test instance (Q) and a train instance
	if (d_mode == 0)
		d = ed2D(Q, &train[tx*M], T, K);
	else
		d = DTW(Q, &train[tx*M], T, K);
	
	dist[bx*N_train + tx] = d;

	__syncthreads();
}

extern "C"{
void launch_kernel_knn(void *train, void *test, void *dist, size_t N_train, size_t N_test, size_t T, size_t K, size_t mode)
{
	// for nuw, num_threads and n_train are the same (so we can use a single block to process a test case against the full training set).  Relieve this limitation by looping over the kernel...

	int M = T*K; // for shared memory	
	int NUM_THREADS = N_train;
	knn<<<N_test, NUM_THREADS, M*sizeof(float)>>>((float*)train, (float*)test, (float*)dist, N_train, T, K, mode);

}}

__global__ void dtw_kern(float *Q, float *S, float *D, size_t T, size_t K){

	*D = DTW(Q, S, T, K);
}
extern "C"{
void launch_kernel_dtw(void *Q, void *S, void *D, size_t T, size_t K)
{
	dtw_kern<<<1, 1>>>((float*)Q, (float*)S, (float*)D,T, K);

}}
/* 	Vector Addition */

__global__ void add_0(float *a, float *b, float *c, size_t N){
	int tid = blockIdx.x;
	if (tid < N)
		c[tid] = a[tid] + b[tid];
}

__global__ void add_1(float *a, float *b, float *c, size_t N){
	int tid = threadIdx.x;
	if (tid < N)
		c[tid] = a[tid] + b[tid];
}

__global__ void add_2(float *a, float *b, float *c, size_t N){
	int tid = threadIdx.x + blockIdx.x * blockDim.x;
	if (tid < N)
		c[tid] = a[tid] + b[tid];
}


extern "C"{
void launch_kernel_add(void *d_a, void *d_b, void *d_c, size_t N, int mode)
{
	
	// launch kernel
	if (mode == 0)
		add_0<<<N, 1>>>((float*)d_a, (float*)d_b, (float *)d_c, N);
	else if (mode == 1)
		add_1<<<1, N>>>((float*)d_a, (float*)d_b, (float *)d_c, N);
	else
		add_2<<<(N + mode-1)/mode, mode>>>((float *)d_a, (float *)d_b, (float *)d_c, N);
}}


/* Vector Multiplication */
__global__ void multiply_0(float *a, float *b, float *c, size_t N){
	extern __shared__ float temp[];
	int tid = threadIdx.x;
	if (tid < N)
		temp[tid] = a[tid] * b[tid];

	__syncthreads();

	// thread 0 sums pairwise products
	if ( tid == 0){
		float sum = 0;
		for (int i =0; i < N; i++)
			sum += temp[i];
		c[0] = sum;
	}
}

__global__ void multiply_1(float *a, float *b, float *c, size_t N, size_t M){
	c[0] = 0.0; // necessary to initialize since malloc doesn't clear memory
	extern __shared__ float temp[];
	int tid = threadIdx.x + blockIdx.x * blockDim.x;
	if (tid < N)
		temp[threadIdx.x] = a[tid] * b[tid];

	__syncthreads();
	
	if (0 == threadIdx.x){
		float sum = 0;
		for (int i=0; i < M; i++)
			sum += temp[i];

		// now we add sum to c.  but since different blocks are doing this potentially simultaneous (read-modify-write), one might read before another writes and hence over write eachother.  so we need to use atomic operations - then read-modify-write is uninteruptable
	atomicAdd(c, sum);
	}
}


extern "C"{
void launch_kernel_multiply(void *d_a, void *d_b, void *d_c, size_t N, size_t M)
{
	printf("%ld, %ld\n", N, M);
	if (M==0)
		multiply_0<<<1, N, N*sizeof(float)>>>((float*)d_a, (float*)d_b, (float *)d_c, N);
	else
		multiply_1<<<(N + M-1)/M, M, M*sizeof(float)>>>((float*)d_a, (float*)d_b, (float *)d_c, N, M);

	printf("%s\n", cudaGetErrorString(cudaGetLastError()));
}}


/*  Matrix Multiplication */


__global__ void matmult_0(float *a, float *b, float *c, size_t W1, size_t W2, size_t W3){
	float cval = 0;

	int col = threadIdx.x + blockIdx.x * blockDim.x;
	int row = threadIdx.y + blockIdx.y * blockDim.y;
	if (row < W1 && col < W3){
		for (int i=0; i<W2; i++)
			cval += a[row*W2 + i] * b[i*W3 + col];
		c[row*W3 + col] = cval;

	}
}

#define TILE_WIDTH 32
__global__ void matmult_1(float *a, float *b, float *c, size_t W1, size_t W2, size_t W3){
	__shared__ float as[TILE_WIDTH][TILE_WIDTH];
	__shared__ float bs[TILE_WIDTH][TILE_WIDTH];

	int bx = blockIdx.x, by = blockIdx.y, tx = threadIdx.x, ty = threadIdx.y;
	int row = by * TILE_WIDTH + ty;
	int col = bx * TILE_WIDTH + tx;
	
	float cval =0;

	for (int i =0; i < (W2-1)/TILE_WIDTH+1; ++i){
		if (row < W1 && i*TILE_WIDTH + tx < W2)
			as[ty][tx] = a[row*W2 + i*TILE_WIDTH + tx];
		else
			as[ty][tx] = 0;
		if (col < W3 && i*TILE_WIDTH+ty < W2)
			bs[ty][tx] = b[(i*TILE_WIDTH+ty)*W3 + col];
		else
			bs[ty][tx] = 0;

		__syncthreads();
		for(int k=0; k <TILE_WIDTH; ++k)
			cval += as[ty][k] * bs[k][tx];
		__syncthreads();
	}
	if (row < W1 && col < W3)
		c[row*W3 + col] = cval;

}


extern "C"{
void launch_kernel_matmul(void *da, void *db, void *dc, size_t W1, size_t W2, size_t W3, size_t mode){

	if (mode == 0){
		dim3 dimBlock(16, 16);
		dim3 dimGrid((W3 + dimBlock.x - 1)/dimBlock.x, (W1 + dimBlock.y - 1)/dimBlock.y);
		matmult_0<<<dimGrid, dimBlock>>>((float*)da, (float*)db, (float*)dc, W1, W2, W3);	
	}
	else{
		dim3 dimBlock(TILE_WIDTH, TILE_WIDTH);
		dim3 dimGrid((W3-1)/TILE_WIDTH+1, (W1-1)/TILE_WIDTH+1);
		matmult_1<<<dimGrid, dimBlock>>>((float*)da, (float*)db, (float*)dc, W1, W2, W3);

	}

}}














/*
__global__ void stencil_1d(int *in, int *out, int RADIUS){
	__shared__ int temp[BLOCK_SIZE + 2*RADIUS];
	int gindex = threadIdx.x + blockIdx.x*blockDim.x;
	int lindex = threadIdx.x + RADIUS;

	// read input into shared
	temp[lindex] = in[gindex];
	if (threadIdx.x < RADIUS){
		temp[lindex - RADIUS] = in[gindex - RADIUS];
		temp[lindex + BLOCK_SIZE] = in[gindex + BLOCK_SIZE];
	}

	__syncthreads();

	int result = 0;
	for (int offset = -RADIUS ; offset <= RADIUS ; offset ++)
		result += temp[lindex + offset];

	out[gindex] = result;
}



*/
