#!/bin/bash --login
#SBATCH --partition=ibmulticore
#SBATCH --job-name=MCSJ2K

#  1. "PTS"       Progressive Transmission by Subbands.
#  2. "PTL"       Progressive Transmission by Layers.
#  3. "AmPTL"     Attenuation-modulated PTL.
#  4. "FS"        Full Search R/D optimization.
#  5. "SR"        Subband Removing R/D optimization.
#  6. "ISR"       Isolated Subband Removing.

srun -n 1 MCSJ2K-subbanYcapas_TM-transcodeB.sh SR

exit 0
