# source files.
SRC = src/heteromap.cpp src/packers.cpp src/protocol.cpp src/transport_factories.cpp src/transports.cpp src/utils.cpp 

OBJ = $(SRC:.cpp=.o)

STATIC_OUT = libagnos.a
SHARED_OUT = libagnos.so.1

# include directories
INCLUDES = -I. -Isrc/include -I/usr/include -I/usr/local/include

# C++ compiler flags (-g -O2 -Wall)
CCFLAGS = -O3 -Wall

# compiler
CCC = g++

# library paths
LIBS := -lboost_thread -lboost_date_time -lboost_iostreams -lboost_system

# compile flags
LDFLAGS = -g

.SUFFIXES: .cpp

default: static

.cpp.o:
	$(CCC) $(INCLUDES) $(CCFLAGS) -c $< -o $@

static: $(OBJ)
	ar rcs $(STATIC_OUT) $(OBJ)

shared: $(OBJ)
	gcc -shared -Wl,-soname,$(SHARED_OUT) -o $(SHARED_OUT) $(OBJ)

clean:
	rm -f $(OBJ) $(STATIC_OUT) $(SHARED_OUT) # DO NOT DELETE
# DO NOT DELETE
