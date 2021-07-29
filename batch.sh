#!/bin/bash

#$ -m be
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=1G
#$ -l h_rt=8:00:00
#$ -o log
#$ -e log

# bail if no conda env activated
[[ -z $CONDA_DEFAULT_ENV ]] && { echo "No conda env activated, exiting"; exit 1; }

python batch_simple.py "scenario/$1.json"
