
UNAME := $(shell uname)

ifeq ($(UNAME), Linux)
	CC=gcc
	CFLAGS=
	LIB=-lOpenCL

	INC_DIRS=/opt/cuda-5.0/include/
	LIB_DIRS=/usr/lib/

else
	CC=gcc
	CLFLAGS=
	LIB=-framework OpenCl
	INC_DIRS=
	LIB_DIRS=
endif
all:
	@echo $(UNAME)
	$(CC) $(CFLAGS) main.c programs.c checks.c -o square -I$(INC_DIRS) -L$(LIB_DIRS) $(LIB)

