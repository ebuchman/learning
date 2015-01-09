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
 
#define DATA_SIZE (1024)


void square_vector(cl_context context, cl_command_queue commands, cl_kernel kernel, cl_device_id device_id, size_t global, size_t local)
{
    int err;
    float data[DATA_SIZE];              // original data set given to device
    float results[DATA_SIZE];           // results returned from device
    unsigned int correct;               // number of correct results returned  

    double elapsed;

    cl_mem input;                       // device memory used for the input array
    cl_mem output;                      // device memory used for the output array
    
    // Fill our data set with random float values
    //
    int i = 0;
    unsigned int count = DATA_SIZE;
    for(i = 0; i < count; i++)
        data[i] = rand() / (float)RAND_MAX;
        
        
    /*
        Memory Allocation: 
          - create arrays in device memory
          - write data into device memory
    */
    
    
    // Create the input and output arrays in device memory for our calculation
    input = clCreateBuffer(context,  CL_MEM_READ_ONLY,  sizeof(float) * count, NULL, NULL);
    output = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(float) * count, NULL, NULL);
    check_mem_arrays(input);
    check_mem_arrays(output);
 
    // Write our data set into the input array in device memory 
    err = clEnqueueWriteBuffer(commands, input, CL_TRUE, 0, sizeof(float) * count, data, 0, NULL, NULL);
    check_write_to_buf(err);


    /*
        Execution:
          - set arguments for kernel
          - get maximum work group size for kernel execution on device
          - execute kernel
          - read back results
    */


    // Set the arguments to our compute kernel
    err = 0;
    err  = clSetKernelArg(kernel, 0, sizeof(cl_mem), &input);
    err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &output);
    err |= clSetKernelArg(kernel, 2, sizeof(unsigned int), &count);
    check_set_kernel_arg(err);
    
    // Get the maximum work group size for executing the kernel on the device
    err = clGetKernelWorkGroupInfo(kernel, device_id, CL_KERNEL_WORK_GROUP_SIZE, sizeof(local), &local, NULL);
    check_work_group_info(err);


    //printf("pre timer \n");
    // time the kernel
    //gcl_start_timer();
    //printf("got timer \n");


    // Execute the kernel over the entire range of our 1d input data set
    // using the maximum number of work group items for this device
    global = count;
    err = clEnqueueNDRangeKernel(commands, kernel, 1, NULL, &global, &local, 0, NULL, NULL);
    check_kernel_exec(err);

    //stop the timer
    //double gcl_stop_timer(cl_timer timer);
    //gcl_stop_timer(timer);
    //elapsed = timer;
    
    //printf("kernel ran in %f s\n", elapsed);



    // Wait for the command commands to get serviced before reading back results
    clFinish(commands);

    // Read back the results from the device to verify the output
    err = clEnqueueReadBuffer( commands, output, CL_TRUE, 0, sizeof(float) * count, results, 0, NULL, NULL );  
    check_read_back(err);


    /* 
        Validate
    */

    correct = validate_square(data, results, count);
    printf("Computed '%d/%d' correct values!\n", correct, count);
    
    
    clReleaseMemObject(input);
    clReleaseMemObject(output);

}



void add_vectors(cl_context context, cl_command_queue commands, cl_kernel kernel, cl_device_id device_id, size_t global, size_t local)
{
    int err;
    float data1[DATA_SIZE];              // original data set given to device
    float data2[DATA_SIZE];              // original data set given to device
    float results[DATA_SIZE];           // results returned from device
    unsigned int correct;               // number of correct results returned  

    double elapsed;
    
    cl_mem input1;                       // device memory used for the input array
    cl_mem input2;                       // device memory used for the input array
    cl_mem output;                      // device memory used for the output array
    
    // Fill our data set with random float values
    //
    int i = 0;
    unsigned int count = DATA_SIZE;
    for(i = 0; i < count; i++)
    {
        data1[i] = rand() / (float)RAND_MAX;
        data2[i] = 1 - data1[i];
    }
        
    /*
        Memory Allocation: 
          - create arrays in device memory
          - write data into device memory
    */
    
    
    // Create the input and output arrays in device memory for our calculation
    input1 = clCreateBuffer(context,  CL_MEM_READ_ONLY,  sizeof(float) * count, NULL, NULL);
    input2 = clCreateBuffer(context,  CL_MEM_READ_ONLY,  sizeof(float) * count, NULL, NULL);
    output = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(float) * count, NULL, NULL);
    check_mem_arrays(input1);
    check_mem_arrays(input2);
    check_mem_arrays(output);
 
    // Write our data set into the input array in device memory 
    err = clEnqueueWriteBuffer(commands, input1, CL_TRUE, 0, sizeof(float) * count, data1, 0, NULL, NULL);
    check_write_to_buf(err);
    err = clEnqueueWriteBuffer(commands, input2, CL_TRUE, 0, sizeof(float) * count, data2, 0, NULL, NULL);
    check_write_to_buf(err);

    /*
        Execution:
          - set arguments for kernel
          - get maximum work group size for kernel execution on device
          - execute kernel
          - read back results
    */


    // Set the arguments to our compute kernel
    err = 0;
    err  = clSetKernelArg(kernel, 0, sizeof(cl_mem), &input1);
    err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &input2);
    err |= clSetKernelArg(kernel, 2, sizeof(cl_mem), &output);
    err |= clSetKernelArg(kernel, 3, sizeof(unsigned int), &count);
    check_set_kernel_arg(err);
    
    // Get the maximum work group size for executing the kernel on the device
    err = clGetKernelWorkGroupInfo(kernel, device_id, CL_KERNEL_WORK_GROUP_SIZE, sizeof(local), &local, NULL);
    check_work_group_info(err);

    // Execute the kernel over the entire range of our 1d input data set
    // using the maximum number of work group items for this device
    global = count;
    err = clEnqueueNDRangeKernel(commands, kernel, 1, NULL, &global, &local, 0, NULL, NULL);
    check_kernel_exec(err);

    // Wait for the command commands to get serviced before reading back results
    clFinish(commands);

    // Read back the results from the device to verify the output
    err = clEnqueueReadBuffer( commands, output, CL_TRUE, 0, sizeof(float) * count, results, 0, NULL, NULL );  
    check_read_back(err);


    /* 
        Validate
    */

    correct = validate_sum(data1, data2, results, count);
    printf("Computed '%d/%d' correct values!\n", correct, count);
    
    
    clReleaseMemObject(input1);
    clReleaseMemObject(input2);
    clReleaseMemObject(output);

}

