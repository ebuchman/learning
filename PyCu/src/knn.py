import numpy as np
import pickle
from ctypes import c_void_p
from scipy import stats
import time
from bindings import *
from dtw import knn_dtw, dtw_py

# max blocks:  65536
# max threads: 1024

# max T is max_bytes/bytes_per_float/K = (48*1024)/4K
# max N_TRAIN is 1024, since N_THREADS=N_TRAIN

def test_knn():
	dataset = '/export/mlrg/ebuchman/datasets/AUSL_data_norm.pkl'
	params = '/export/mlrg/ebuchman/Programming/machine_learning/DTW/data/results/AUSL_data_norm/dtw_/LRi_0.10000_reg_0.00/2014_2_13_17_41/params_AUSL_data_norm_dtw__LRi_0.10000_reg_0.00_inf.pkl'

	f = open(dataset)
	dataset = pickle.load(f)
	f.close()
	
	f = open(params)
	params = pickle.load(f)
	f.close()

	p1,p2 = params
	p1 = p1[0]
	weights = p1[0]
	something = p1[1]
	details = p2
	print details
	print weights.shape
	print details


	knn_k = 1

	tr, val, tst = dataset
	tr_x, tr_y = tr
	tst_x, tst_y = tst

	# project time series to feature space
	tr_x = np.dot(tr_x, weights)
	tst_x = np.dot(tst_x, weights)

	N_TRAIN_glob, T, K = tr_x.shape
	N_TEST = tst_x.shape[0]

	mode = 1

	print N_TRAIN_glob, N_TEST, T, K

	
	test = tst_x.astype('float32')

	# since we can only do 1024 train data at a time, must loop over blocks if too many
	big_D = np.zeros((N_TEST, N_TRAIN_glob))

	for i in xrange((N_TRAIN_glob + 1023)/ 1024):
		lim = (i+1)*1024 if (i+1)*1024 < N_TRAIN_glob else N_TRAIN_glob
		tr_x = tr_x[i*1024:lim]

		train = tr_x.astype('float32')

		N_TRAIN = lim - i*1024

		dist = np.zeros((N_TEST, N_TRAIN)).astype('float32')

		c_tr, c_ts, c_d  = map(c_void_p, [train.ctypes.data, test.ctypes.data, dist.ctypes.data])
		dtr, dts, dd = map(pycu_alloc, [N_TRAIN*T*K, N_TEST*T*K, N_TEST*N_TRAIN])

		pycu_host2gpu(c_tr, dtr, N_TRAIN*T*K)
		pycu_host2gpu(c_ts, dts, N_TEST*T*K)
		pycu_host2gpu(c_d, dd, N_TEST*N_TRAIN)
		
		start = time.time()
		pycu_launch_knn(dtr, dts, dd, N_TRAIN, N_TEST, T, K, mode)
		print "kernel computation time for knn: ", time.time()-start
		pycu_gpu2host(c_d, dd, N_TEST*N_TRAIN)

		big_D[:, i*1024:lim] = dist

		map(pycu_free_gpu, [dtr, dts, dd])

	sorted_dists = big_D.argsort()
	nn = sorted_dists[:,:knn_k]
	nn_class = tr_y[nn]
	pred = stats.mode(nn_class, axis=1)[0].reshape(N_TEST)
	

	print sum(pred==tst_y) / float(N_TEST)




if __name__ == '__main__':
	test_knn()
