A year long project myself and two teammates completed for our senior capstone that improved upon a previous group's codebase. This program takes as input an excel sheet containing names and graduation dates of all of Western's Computer Science alumni and generates a personalized video for each alumni asking them to donate to the CS department.

Prior to my team's iteration of this project, the program ran exclusively through commandline and was not user-friendly. So we created a simple python GUI to streamline the user process. Our other main focus was decreasing runtime and increasing readability in the code for future iterations of the project. 

The main way we were able to decrease the runtime of the program was by introducing multiprogramming through multithreading, this came with its own challenges like interthread communication and dealing with race conditions on any common resources, but eventually we worked our way through it and significantly decreased the runtime by a significant margin.

We made a few modifications to the codebase to increase readability, one of the ways we acheieved that was through increasing the modularity of the code and separating functionalities into different functions and python files and changed how each of these parts of the overall program communicated with each other. We also split up the video generation into different "chapters" and created the framework for creating new chapters so that changing the contents of the videos and adding further personalization down the line would be sigfnificantly easier for any teams picking up the project in the coming years. 


Below are a few demo videos of our finished product as well as a few example videos (quality scaled down, length of clips shortened to fit max github upload file size, and using fake data to preserve alumni privacy):

Example video of a generated video before my team's changes:

https://github.com/user-attachments/assets/b22fc140-b126-4d04-ab7b-84f4a7537417

An example of a generated video after our changes:

https://github.com/user-attachments/assets/d5974368-2ec1-46cf-8563-b9cdb3ca62f3

Demo video of the video generation process:

https://github.com/user-attachments/assets/4e5f99b6-6d85-4ea3-8676-0af0f4531ac6

Screenshot of the hosted website that alumni are sent a link to that has relevant information to donate to the CS department at Western:

![website ss](https://github.com/user-attachments/assets/40fd099e-2995-4fbd-9006-27f001bb78eb)

