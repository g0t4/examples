# this is for a sizes.cpp exe file that I want to be sizes.out
#
cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 11)
# set(CMAKE_EXE_LINKER_FLAGS "-static") -- interesting, proposed by my ask-openai helper... come back to this, its missing a library right now
add_executable(sizes.out sizes.cpp)
# now I have added the output name as 'sizes.out' to overwrite the 'sizes.exe'

add_executable(unions.out unions.cpp)

