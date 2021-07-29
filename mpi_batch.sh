#!/bin/bash

#$ -m e
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=4G
#$ -l h_rt=4:00:00
#$ -o log
#$ -e log
#$ -pe smp 24

mpirun python batch_simple.py "scenario/$1.json"

