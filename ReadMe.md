
### Prerequisites on a new machine.

Generate and add your ssh key to GitHub account:
   1. `ssh-keygen -t ed25519 -C "user@example.com"`
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
4. Rename the sample.env file to .env the project root `cp sample.env .env`

### Running the script:

Get the `REQUEST_TOKEN` by hitting the following URL: `https://kite.zerodha.com/connect/login?v=3&api_key={api_key}`


#### Directly on terminal:
1. Paste the updated `REQUEST_TOKEN` and other required variables in `.env` file.
2. Start the script using `python3 main.py`

#### As a service daemon in ubuntu:
1. Paste the updated `REQUEST_TOKEN` and other required variables in `.env` file.
2. Edit the autotrade.service file with correct Working directory path and python3 path.
3. Copy the autotrade.service file: `sudo cp autotrade.service /lib/systemd/system/autotrade.service`
4. Refresh demon registry: `sudo systemctl daemon-reload`
5. Start the service: `sudo service autotrade start`