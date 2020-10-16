#!/bin/bash

#$ -m e
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=1G
#$ -l h_rt=12:00:00
#$ -o log
#$ -e log
#$ -pe ib 20

mpirun python batch.py "scenario/$1.json"

