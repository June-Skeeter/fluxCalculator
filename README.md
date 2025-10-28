# fluxCalculator

This code is a "fork" of [EddypPro&reg;](https://github.com/LI-COR-Environmental/eddypro-engine).  All credit for contirbutions prior to 2025 go to the creators of EddyPro, namely Gerardo Fratini.  I have detached this fork the source repository because the official version is not being actively maintained and does not support community contributions.

The modifications made here include:

* Correction of path length variables for Gill anemometers
* Improved support for reading high frequency binary files
* Support for IRGASON as a default instrument
* Scripts for building from compiling from source code
* Bugfix in makefile to for compiling on windows


## Setup

### For linux:

1. Clone the repo

`git clone https://github.com/June-Skeeter/fluxCalculator`

2. Install dependencies (make & Fortran)

`sudo apt-get update`

`sudo apt-get make`

`sudo apt-get install gfortran`

3. Build and run using using the test data

`bash run.sh build run`

### For windows:

