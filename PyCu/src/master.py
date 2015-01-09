import numpy as np
from ctypes import c_void_p
import time
from bindings import *
from dtw import knn_dtw, dtw_py

# max blocks:  65536
# max threads: 1024


def test_knn():
	# time series of length T and dimension K
	T = 128 
	# max T is max_bytes/bytes_per_float/K = (48*1024)/4K
	# fix T at 1024 for convenience.  Max K = 12
	K = 4
	N_TRAIN = 8 # max N_TRAIN is 1024, since N_THREADS=N_TRAIN
	N_TEST = 1
	mode = 1

	np.random.seed(10)

	train = np.random.randn(N_TRAIN, T, K).astype('float32')
	test = np.random.randn(N_TEST, T, K).astype('float32')	
	dist = np.zeros((N_TEST, N_TRAIN)).astype('float32')
	dist_ = np.zeros((N_TEST, N_TRAIN)).astype('float32')

	c_tr, c_ts, c_d, c_d_ = map(c_void_p, [train.ctypes.data, test.ctypes.data, dist.ctypes.data, dist_.ctypes.data])
	dtr, dts, dd = map(pycu_alloc, [N_TRAIN*T*K, N_TEST*T*K, N_TEST*N_TRAIN])

	pycu_host2gpu(c_tr, dtr, N_TRAIN*T*K)
	pycu_host2gpu(c_ts, dts, N_TEST*T*K)
	pycu_host2gpu(c_d, dd, N_TEST*N_TRAIN)
	
	start = time.time()
	pycu_launch_knn(dtr, dts, dd, N_TRAIN, N_TEST, T, K, mode)
	print "kernel computation time for knn: ", time.time()-start
	pycu_gpu2host(c_d, dd, N_TEST*N_TRAIN)


	start = time.time()
	if mode == 0:	
		pycu_dist3D(c_ts, c_tr, c_d_, N_TEST, N_TRAIN, T, K)
		print "c computation time for knn", time.time() - start
	else:
		knn_dtw(train, test, dist_)

	error = np.sum((dist - dist_)**2)**0.5

	print "error: ", error

	map(pycu_free_gpu, [dtr, dts, dd])

def test_dtw():
	T = 128
	K = 4
	
	np.random.seed(10)
	Q = np.random.randn(T, K).astype('float32')
	S = np.random.randn(T, K).astype('float32')
	d = np.zeros(1).astype('float32')

	cQ, cS, cD = map(c_void_p, [Q.ctypes.data, S.ctypes.data, d.ctypes.data])
	dQ, dS, dD = map(pycu_alloc, [T*K, T*K, 1])

	pycu_host2gpu(cQ, dQ, T*K)
	pycu_host2gpu(cS, dS, T*K)
	pycu_host2gpu(cD, dD, 1)

	pycu_launch_dtw(dQ, dS, dD, T, K)

	pycu_gpu2host(cD, dD, 1)

	print "cuda: ", d

	d_ = dtw_py(Q, S, T)[1]
	print "python: ", d_

	print "error: ", d-d_

	map(pycu_free_gpu, [cQ, cS, cD])

def test_mat_mul():
	W1, W2, W3 = 1024, 2048, 2048
	mode = 0 

	np.random.seed(10)

	a = np.random.randn(W1, W2).astype('float32')
	b = np.random.randn(W2, W3).astype('float32')
	c = np.zeros((W1, W3)).astype('float32')

	c_a, c_b, c_c = map(c_void_p, [a.ctypes.data, b.ctypes.data, c.ctypes.data])
	da, db, dc  = map(pycu_alloc, [W1*W2, W2*W3, W1*W3])
	
	pycu_host2gpu(c_a, da, W1*W2)
	pycu_host2gpu(c_b, db, W2*W3)
	pycu_host2gpu(c_c, dc, W1*W3) # this will clear the memory in dc

	start = time.time()
	pycu_launch_matmul(da, db, dc, W1, W2, W3, mode)
	print "kernel computation time for matmul: ", time.time()-start
	pycu_gpu2host(c_c, dc, W1*W3)
	#print "kernel c", c

	start = time.time()
	cc = np.dot(a,b)
	print "python computation time for matmul: ", time.time() - start
	#	print 'python c', cc
	error = np.sum((c - cc)**2)**0.5
	print "error: ", error

	map(pycu_free_gpu, [da, db, dc])

def test_vector_dot():
	N = 1024 #28672 #if this is any larger, the computation fails.  Why?!
	M = 32

	np.random.seed(19)

	a = np.random.randn(N).astype('float32')
	b = np.random.randn(N).astype('float32')
	c = np.zeros(1).astype('float32')

	c_a, c_b, c_c = map(c_void_p, [a.ctypes.data, b.ctypes.data, c.ctypes.data])
	da, db  = map(pycu_alloc, [N]*2)
	dc = pycu_alloc(1)

	pycu_host2gpu(c_a, da, N)
	pycu_host2gpu(c_b, db, N)


	start = time.time()
	pycu_launch_multiply(da, db, dc, N, M)
	print "kernel computation time for dot product: ", time.time()-start

	pycu_gpu2host(c_c, dc, 1)
	print "kernel c", c

	start = time.time()
	cc = np.dot(a,b)
	print "python computation time for dot product: ", time.time() - start
	print 'python c', cc
	error = np.sum((c - cc)**2)**0.5
	print "error: ", error

	map(pycu_free_gpu, [da, db, dc])

def test_vector_addition():
	N = 10240*6
	mode = 0 # 0 for just blocks, 1 for just threads, other as threads/block
 
	a = np.random.randn(N).astype('float32')
	b = np.random.randn(N).astype('float32')
	c = np.zeros(N).astype('float32')

	c_a, c_b, c_c = map(c_void_p, [a.ctypes.data, b.ctypes.data, c.ctypes.data])
	da, db, dc = map(pycu_alloc, [N]*3)

	pycu_host2gpu(c_a, da, N)
	pycu_host2gpu(c_b, db, N)

	start = time.time()
	pycu_launch_add(da, db, dc, N, mode)
	print "kernel computation time for simple addition: ", time.time()-start

	pycu_gpu2host(c_c, dc, N)

	start = time.time()
	cc = a + b
	print "python computation time for simple addition: ", time.time() - start

	error = np.sum(c - cc)
	print "error: ", error

	map(pycu_free_gpu, [da, db, dc])



if __name__ == '__main__':
	#test_vector_addition()
	#test_vector_dot()
	get_device_info()
	#test_mat_mul()
	test_knn()
	#test_dtw()
