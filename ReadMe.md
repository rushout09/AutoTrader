
### Prerequisites on a new machine.

Generate and add your ssh key to GitHub account:
   1. `ssh-keygen -t ed25519 -C "rushabh.agarwal9@gmail.com"`
   2. `cat ~/.ssh/id_ed25519.pub`
   3. Paste the above key to github -> profile -> settings -> GPG and keys.

### How to install

1. Git clone the repo using `git clone git@github.com:rushout09/AutoTrader.git`.
2. Create and activate virtualenv using:
   1. `sudo apt update`
   2. `sudo apt install python3.10-venv`
   3. `python3 -m venv venv`.
   4. Activate the virtualenv using `source venv/bin/activate`.
3. Install the dependencies using `pip3 install -r requirements.txt`