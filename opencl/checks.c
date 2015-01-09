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
 
int check_device_id(int err)
{

    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to create a device group!\n");
        return EXIT_FAILURE;
    }
    
    else return 0;
}  


int check_context(cl_context context)
{
    if (!context)
    {
        printf("Error: Failed to create a compute context!\n");
        return EXIT_FAILURE;
    }
  else return 0;
}


int check_command_queue(cl_command_queue commands)
{
    if (!commands)
    {
        printf("Error: Failed to create a command commands!\n");
        return EXIT_FAILURE;
    }
    else return 0;

}


int check_program(cl_program program)
{

    if (!program)
    {
        printf("Error: Failed to create compute program!\n");
        return EXIT_FAILURE;
    }
    else return 0;

}


void check_program_exec(int err, cl_program program, cl_device_id device_id)
{
    if (err != CL_SUCCESS)
    {
        size_t len;
        char buffer[2048];

        printf("Error: Failed to build program executable!\n");
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, sizeof(buffer), buffer, &len);
        printf("%s\n", buffer);
        exit(1);
    }
}

void check_kernel(cl_kernel kernel, int err)
{

    if (!kernel || err != CL_SUCCESS)
    {
        printf("Error: Failed to create compute kernel!\n");
        exit(1);
    }
}

void check_mem_arrays(cl_mem array)
{
    if (!array)
    {
        printf("Error: Failed to allocate device memory!\n");
        exit(1);
    }    
}   

void check_write_to_buf(int err)
{
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to write to source array!\n");
        exit(1);
    }
}

void check_set_kernel_arg(int err)
{

    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to set kernel arguments! %d\n", err);
        exit(1);
    }
}

void check_work_group_info(int err)
{
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to retrieve kernel work group info! %d\n", err);
        exit(1);
    }
}

int check_kernel_exec(int err)
{    
  
    if (err)
    {
        printf("Error: Failed to execute kernel!\n");
        return EXIT_FAILURE;
    }
    else return 0;
}

void check_read_back(int err)
{

    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to read output array! %d\n", err);
        exit(1);
    }
}

int validate_square(float * data, float * results, int count)
{    
    // Validate our results
    //
    int i;
    int correct = 0;
    for(i = 0; i < count; i++)
    {
        if(results[i] == data[i] * data[i])
            correct++;
        //printf("%f, %f\n", results[i], data[i]*data[i]);

    }

  return correct;
}

int validate_sum(float * data1, float * data2, float * results, int count)
{    
    // Validate our results
    //
    int i;
    int correct = 0;
    for(i = 0; i < count; i++)
    {
        if(results[i] - (data1[i] + data2[i]) < 0.01)
            correct++;
        //printf("%f, %f\n", results[i], data1[i]+data2[i]);
    }

  return correct;
}


void get_devices(){ 
    cl_uint num_devices, i;
    clGetDeviceIDs(NULL, CL_DEVICE_TYPE_ALL, 0, NULL, &num_devices);

    cl_device_id* devices = calloc(sizeof(cl_device_id), num_devices);
    clGetDeviceIDs(NULL, CL_DEVICE_TYPE_ALL, num_devices, devices, NULL);

    char buf[128];
    for (i = 0; i < num_devices; i++) {
        clGetDeviceInfo(devices[i], CL_DEVICE_NAME, 128, buf, NULL);
        fprintf(stdout, "Device %s supports ", buf);

        clGetDeviceInfo(devices[i], CL_DEVICE_VERSION, 128, buf, NULL);
        fprintf(stdout, "%s\n", buf);
    }

    free(devices);
}
