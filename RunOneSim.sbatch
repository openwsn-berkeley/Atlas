#!/bin/bash
#SBATCH --job-name=Atlas                          # Job name
#SBATCH --mail-type=FAIL                          # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=razane.abu-aisheh@inria.fr    # Where to send mail
#SBATCH --gres=gpu:rtx6000:1                      # GPU nodes are only available in gpu partition
#SBATCH --mem=10G                                 # Total memory allocated
#SBATCH --time=24:00:00                           # total run time limit (HH:MM:SS)

# If you use conda
source /home/$USER/.bashrc
conda activate py38
echo "Running RunOneSim.sbatch"
python ../RunOneSim.py --simSetting "$1"



