#!/bin/bash

#$ -m be
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=1G
#$ -l h_rt=4:00:00
#$ -o log
#$ -e log

python batch.py "scenario/$1.json" "scenario/$1.csv"

