# !/bin/bash

python3 -m venv venv
source venv/bin/activate
sudo dnf install glibc-all-langpacks bc smartmontools hdparm
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
