#!/bin/bash
#SBATCH --job-name=Atlas                         # Job name
#SBATCH --mail-type=ALL                          # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=razane.abu-aisheh@inria.fr   # Where to send mail
#SBATCH --output=output%A_%a.log                 # Standard output and error log

# If you use conda
source /home/$USER/.bashrc
conda activate py38
echo "Running RunOneSim.Sbatch"
python ../RunOneSim.py --simSetting "$1"



