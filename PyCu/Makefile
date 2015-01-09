
# specify architecture so atomic operations are legit
SRC=./src/

all:
	nvcc -arch=sm_20 -Xcompiler -fPIC -shared -o cuda_lib.so $(SRC)kernels.cu $(SRC)bindings.cu
