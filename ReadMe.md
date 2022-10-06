# AutoTrader

This repo contains a simple script to trade using Zerodha's KITE API. 

The algorithm to trade is based on really simple trading principle of buying low and selling high.
Buy certain units of an instrument.
1. If the opening price is lower than last day closing price by a certain margin (example 1 percent).
2. If the noon price is lower than current day opening price by a certain margin (example 1 percent).
3. If the closing price is lower than current day noon price by a certain margin (example 1 percent). 

In both the above cases create a GTT to sell when the same stocks are up by 1 percent.


This algorithm makes following assumption for it to make profit:
1. Market will fluctuate.
2. It will stay the same or go up in the long term.


### Todos (immediate):

0. Change code to trade only at opening, mid-hour and closing hours. done.
1. Deploy at 12:20pm.
2. Keep the instance running.
3. Confirm if it requires request token daily.


### Todos (long term):

0. Change code to trade only at opening, mid-hour and closing hours. 
1. Add a GET endpoint to get `REQUEST_TOKEN` automatically.
2. Add script to use `db.log` to generate report.
3. add a cron job to trigger during opening, mid and closing hours.
4. Send alerts on transactions/orders.
5. Get user input to confirm order transaction via call or message.
6. Move this to AWS Lambda.


### Manual things that would be needed to done when Automated:
Once in the morning:
1. Authorize CDSL. (Add a reminder for this)
2. Give request token.

### Manual things that would be needed to done when Automated:
Once in the morning:
1. Authorize CDSL.
2. Create an order.

Once in the evening:



### Prerequisites to install on a new machine.

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