compiler = g++
flag = -std=c++11

libPath = -I$(HOME)/workplace/lib/rapidcsv 

inputFile = VendorReportAutomation.cpp
outputFile = $(inputFile:.cpp=.o)
executeFile = a.out

all:
	$(compiler) $(flag) $(libPath) $(inputFile) -o $(executeFile)

clean:
	rm *.out
