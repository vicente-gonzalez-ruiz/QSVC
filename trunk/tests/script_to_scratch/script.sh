#!/bin/bash
#./script.sh

sbatch -N 1 scriptA1.sh
sbatch -N 1 scriptA2.sh
sbatch -N 1 scriptA3.sh
sbatch -N 1 scriptA4.sh
sbatch -N 1 scriptA5.sh
sbatch -N 1 scriptA6.sh

sbatch -N 1 scriptB1.sh
sbatch -N 1 scriptB2.sh
sbatch -N 1 scriptB3.sh
sbatch -N 1 scriptB4.sh
sbatch -N 1 scriptB5.sh
sbatch -N 1 scriptB6.sh

sbatch -N 1 scriptC1.sh
sbatch -N 1 scriptC2.sh
sbatch -N 1 scriptC3.sh
sbatch -N 1 scriptC4.sh
sbatch -N 1 scriptC5.sh
sbatch -N 1 scriptC6.sh

sbatch -N 1 scriptD1.sh
sbatch -N 1 scriptD2.sh
sbatch -N 1 scriptD3.sh
sbatch -N 1 scriptD4.sh
sbatch -N 1 scriptD5.sh
sbatch -N 1 scriptD6.sh

exit 0
