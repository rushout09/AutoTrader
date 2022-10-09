# AutoTrader

This repo contains scripts to trade using Zerodha's KITE API.

### Todos (long term):

1. Send alerts on transactions/orders.
2. Get user input to confirm order transaction via call or message.
3. Automate accounting. Add script to use `db.log` to generate report.
4. Include the past results in ReadMe.

### Why AutoTrader for passive income in medium term.

- The disciplined compounding, low risk and low time/effort nature of makes it a good passive income tool (medium term).
- Intraday trading based on technical analysis is also a good passive income tool (once you have mastered it).
However, requires more time/effort and has more risk.

### Pros of AutoTrader.

- Disciplined Compounding: The biggest advantage of autotrader is that the least amount of human emotions, time, 
and effort will be involved, allowing small profits to compound over a long period of time without interruptions.
- Low Risk: The algorithm, the instrument of trade, and the margins/units are selected to have the least
possibility of losing money.

### Cons of AutoTrader.

- Need to pay server charges. Charges are minimal and can be further reduced if deployed on lambda.
- Need to pay API charges. This can be shared among small group of known people.
- Need to maintain it once in a while. Once set, very less frequent changes would be required.
- Increased accounting: Can be automated.
- Small manual intervention is still required daily/monthly: For CDSL authorization and request token.  
Transfer money on Account Settlement.

### The Algorithm and margin/units:

1. Buy certain units (150) of an instrument.
   1. If the opening price is lower than last day closing price by a certain margin (1 percent).
   2. If the noon price is lower than current day opening price by a certain margin (1 percent).
   3. If the closing price is lower than current day noon price by a certain margin (1 percent).
2. In both the above cases create a GTT to sell when the bought stocks are up by 1 percent.

### The Instrument:

- NIFTYBEES ETF: https://www.amfiindia.com/investor-corner/knowledge-center/etf.html#accordion1


### How to deploy on Deta

1. Git clone the repo using `git clone git@github.com:rushout09/AutoTrader.git`.
2. Run the following command to install Deta CLI `curl -fsSL https://get.deta.dev/cli.sh | sh`
3. Open a new CLI and run `deta --help` to confirm installation succeeded.
4. Login and deploy using command: `deta login` and `deta new`
5. Set the env variables: `deta update -e .env`
6. Set the cron: `deta cron set "40,50 3,9 ? * MON-FRI *"`
7. Deploy again using: `deta deploy`
8. View logs: `deta logs`
9. Useful links:
   1. https://docs.deta.sh/docs/home
   2. https://fastapi.tiangolo.com/deployment/deta/?h=deta#deploy-with-deta
   3. https://medium.com/tensult/aws-lambda-function-issues-with-global-variables-eb5785d4b876

### Prerequisites to install on a new machine.

Generate and add your ssh key to GitHub account:
   1. `ssh-keygen -t ed25519 -C "user@example.com"`
   2. `cat ~/.ssh/id_ed25519.pub`
   3. Paste the above key to github -> profile -> settings -> GPG and keys.

### How to set up locally:

1. Git clone the repo using `git clone git@github.com:rushout09/AutoTrader.git`.
2. Create and activate virtualenv using:
   1. `sudo apt update`
   2. `sudo apt install python3.10-venv`
   3. `python3 -m venv venv`.
   4. Activate the virtualenv using `source venv/bin/activate`.
3. Install the dependencies using `pip3 install -r requirements.txt`
4. Rename the sample.env file to .env the project root `cp sample.env .env`
5. Get the `REQUEST_TOKEN` by hitting the following URL: `https://kite.zerodha.com/connect/login?v=3&api_key={api_key}`

#### As a script:
1. Paste the updated `REQUEST_TOKEN` and other required variables in `.env` file.
2. Start the script using `python3 app.py`

#### As a service daemon:
1. Paste the updated `REQUEST_TOKEN` and other required variables in `.env` file.
2. Edit the autotrade.service file with correct Working directory path and python3 path.
3. Copy the autotrade.service file: `sudo cp autotrade.service /lib/systemd/system/autotrade.service`
4. Refresh demon registry: `sudo systemctl daemon-reload`
5. Start the service: `sudo service autotrade start`
