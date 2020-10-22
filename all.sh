#!/bin/bash

qsub batch.sh 1event
qsub mpi_batch.sh 2events
qsub mpi_batch.sh 3events
qsub mpi_batch.sh 4events
qsub mpi_batch.sh 5events
qsub mpi_batch.sh 6events
qsub mpi_batch.sh 7events
qsub mpi_batch.sh 8events
qsub mpi_batch.sh 9events
qsub mpi_batch.sh 10events

