import numpy as np
import pickle
import time
import scipy


def euc_dist(a, b):
  d = np.sum((a-b)**2)**0.5
  
  return d


def dtw_py(s1, s2, constraint):
  t = len(s1)
  d = len(s1[0])


  if constraint == t:
	indices = np.asarray([[i+1,j+1] for i in xrange(t) for j in xrange(t)])
  else:
	indices = np.asarray([[i+1, j+1] for i in xrange(t) for j in xrange(np.maximum(0, i-constraint), np.minimum(i+constraint, t))], dtype='int32')
  
  dtw = np.ones((t+1, t+1))*10000000 # dtw distance from 0,0 to each point in the matrix
  euclidis = np.zeros((t, t))

  dtw[0, :] = np.inf
  dtw[:, 0] = np.inf
  dtw[0, 0] = 0

  for i in indices:
    ix, iy = i
    dist = euc_dist(s1[ix-1], s2[iy-1])
    #euclidis[ix-1, iy-1] = dist
    n = np.minimum(np.minimum(dtw[ix-1, iy], dtw[ix, iy-1]), dtw[ix-1, iy-1])
    dtw[ix, iy] = dist + n

  dtw[dtw> 10000] = 0
  
  dtw_dist = dtw[-1,-1]
  
  return dtw[1:, 1:], dtw_dist
  

def knn_dtw(train, test, dist_mat):
	print train.shape, test.shape
	for i in xrange(len(test)):
		for j in xrange(len(train)):
			#print i,j
			dist_mat[i,j] = dtw_py(test[i], train[j], len(train[j]))[1]


        
def dtw_knn(k=10):
  f = open('../DTW/data/BFC.pkl')
  d = pickle.load(f)
  f.close()
  
  tr, val, tst = d
  
  tr_x, tr_y = tr
  tst_x, tst_y = tst
  
  t = len(tr_x[0])
  constraint = 10
  
  th_F = dtw_th_func()
  indices = np.asarray([[i+1, j+1] for i in xrange(t) for j in xrange(np.maximum(0, i-constraint), np.minimum(i+constraint, t))], dtype='int32')

  print 'total: ', len(tst_x)
  
  correct = 0
  for j in xrange(len(tst_x)):
    D = []
    for i in xrange(len(tr_x)):
      #dtw, dtw_dist = dtw_py(tst_x[j], tr_x[i])
      dtw, dtw_dist = th_F(tst_x[j], tr_x[i], indices)

      D.append(dtw_dist)
      #print i, tst_y[0], tr_y[i], dtw_dist
      
    sorted_i = np.argsort(D)
    knn_i = sorted_i[:k]
    pred = scipy.stats.mode(tr_y[knn_i])[0]
  
    print j, pred, tst_y[j]
    if pred[0] == tst_y[j]:
      correct += 1
      
  print 'correct: ', correct
  print 'percent correct: ', correct/float(len(tst_x))
 
 
