import ctypes 
from ctypes import *

dll = ctypes.CDLL('./cuda_lib.so', mode=ctypes.RTLD_GLOBAL)

def build_pycu_alloc_f(dll):
	func = dll.alloc_gpu_mem
	func.argtypes = [c_size_t]
	func.restype = c_void_p
	return func

pycu_alloc = build_pycu_alloc_f(dll)

def build_pycu_host2gpu_f(dll):
	func = dll.host2gpu
	func.argtypes = [c_void_p, c_void_p, c_size_t]
	return func

pycu_host2gpu = build_pycu_host2gpu_f(dll)

def build_pycu_gpu2host_f(dll):
	func = dll.gpu2host
	func.argtypes = [c_void_p, c_void_p, c_size_t]

	return func

pycu_gpu2host = build_pycu_gpu2host_f(dll)

def build_gpu_free_mem_f(dll):
	func = dll.free_gpu_mem
	func.argtypes = [c_void_p]

	return func

pycu_free_gpu = build_gpu_free_mem_f(dll)


def build_free_mem_f(dll):
	func = dll.free_mem
	func.argtypes = [POINTER(c_float)]

	return func

pycu_free = build_free_mem_f(dll)

def build_get_cuda_info(dll):
	func = dll.get_cuda_info
	return func

get_device_info = build_get_cuda_info(dll)

def build_dist3D_f(dll):
	func = dll.distance3D
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t]
	return func

pycu_dist3D = build_dist3D_f(dll)


################## Launch Functions ##########################

def build_kernel_launch_f_add(dll):
	func = dll.launch_kernel_add
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_int]
	return func

pycu_launch_add = build_kernel_launch_f_add(dll)


def build_kernel_launch_f_multiply(dll):
	func = dll.launch_kernel_multiply
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_size_t]
	return func

pycu_launch_multiply = build_kernel_launch_f_multiply(dll)


def build_kernel_launch_f_matmul(dll):
	func = dll.launch_kernel_matmul
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t]
	return func

pycu_launch_matmul = build_kernel_launch_f_matmul(dll)

def build_kernel_launch_f_dtw(dll):
	func = dll.launch_kernel_dtw
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_size_t]
	return func

pycu_launch_dtw = build_kernel_launch_f_dtw(dll)

def build_kernel_launch_f_knn(dll):
	func = dll.launch_kernel_knn
	func.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t]
	return func

pycu_launch_knn = build_kernel_launch_f_knn(dll)
