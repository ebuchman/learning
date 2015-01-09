
////////////////////////////////////////////////////////////////////////////////

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>

#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif
 

////////////////////////////////////////////////////////////////////////////////

// Use a static data size for simplicity
#define MAX_SOURCE_SIZE (0x100000)



int main(int argc, char** argv)
{
    int err;                            // error code returned from api calls

    size_t global;                      // global domain size for our calculation
    size_t local;                       // local domain size for our calculation

    cl_device_id device_id;             // compute device id 
    cl_context context;                 // compute context
    cl_command_queue commands;          // compute command queue
    cl_program program;                 // compute program
    cl_kernel kernel;                   // compute kernel
    

    char kernel_name[100];
    int kernel_num = 0;
    
    if (kernel_num == 0)
       strcpy(kernel_name, "kernels/square.cl");
    else
       strcpy(kernel_name, "kernels/sum.cl");
    
    
    // load the kernel source:
    FILE *fp;
    char *source_str;
    size_t source_size;
    
    fp = fopen(kernel_name, "r");
    source_str = (char*)malloc(MAX_SOURCE_SIZE);
    source_size = fread( source_str, 1, MAX_SOURCE_SIZE, fp);
    fclose( fp );

	get_devices();   
 
    /*
        Global Setup: 
          - connect to device
          - create context
          - create commands
          - create program (from source buffer)
          - build program executable
          - create kernel in program
    */
    
    // Connect to a compute device
    int gpu = 1;
    
    /*cl_int clGetDeviceIDs( 	cl_platform_id platform,
                                cl_device_type device_type,
                                cl_uint num_entries,
                                cl_device_id *devices,
                                cl_uint *num_devices)
    */
    
    err = clGetDeviceIDs(NULL, gpu ? CL_DEVICE_TYPE_GPU : CL_DEVICE_TYPE_CPU, 1, &device_id, NULL);
    check_device_id(err);

    // Create a compute context 
    context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
    check_context(context);

    // Create a command commands
    commands = clCreateCommandQueue(context, device_id, 0, &err);
    check_command_queue(commands);

    // Create the compute program from the source buffer
    program = clCreateProgramWithSource(context, 1, (const char **) &source_str, (const size_t *)&source_size, &err);
    check_program(program);

    // Build the program executable
    err = clBuildProgram(program, 0, NULL, NULL, NULL, NULL);
    check_program_exec(err, program, device_id);

    // Create the compute kernel in the program we wish to run
    kernel = clCreateKernel(program, "square", &err);
    check_kernel(kernel, err);


    // make data, load it into kernel, execute it. everything.
    if (kernel_num == 0)
      square_vector(context, commands, kernel, device_id, global, local);
    else
      add_vectors(context, commands, kernel, device_id, global, local); 


    // Shutdown and cleanup
    clReleaseProgram(program);
    clReleaseKernel(kernel);
    clReleaseCommandQueue(commands);
    clReleaseContext(context);

    return 0;
}

