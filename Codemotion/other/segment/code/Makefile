INCDIR = -I.
DBG    = -g
OPT    = -O3
CPP    = g++
CFLAGS = $(DBG) $(OPT) $(INCDIR)
LINK   = -lm 

.cpp.o:
	$(CPP) $(CFLAGS) -c $< -o $@

all: segment

segment: segment.cpp segment-image.h segment-graph.h disjoint-set.h
	@printf "compiling... "
	@$(CPP) $(CFLAGS) -w -o segment segment.cpp $(LINK)
	@echo "done!"

clean:
	/bin/rm -f segment *.o

clean-all: clean
	/bin/rm -f *~ 



