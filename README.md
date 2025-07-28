# Phiduhok bot

[@phiduhok_bot](https://t.me/phiduhok_bot) is a simple telegram bot for memes sharing, inspired by Zhvanetzky.

## Usage

### Prepare environment

```bash
cd /opt
apt install git python3 python3-pip python3-venv
git clone https://github.com/AleksejEgorov/phiduhok_bot.git autoposter
cd autoposter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

### Create service

First, create system user:

```bash
sudo useradd -r -s /bin/false botrunner
```

Next, create systemd unit file `/etc/systemd/system/phiduhok-bot.service` with:

```ini
[Unit]
Description=Phiduhok!
After=network.target

[Service]
User=botrunner
Group=botrunner
Type=simple
WorkingDirectory=/opt/phiduhok_bot
ExecStart=/opt/phiduhok_bot/.venv/bin/python3 /opt/phiduhok_bot/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Configuration

Copy `config_sample.yaml` to `config.yaml` and populate with your values. Config contains sensitive information, so secure it with `chmod 600`.

### Run

```bash
sudo systemctl daemon-reload
sudo systemctl enable phiduhok-bot
sudo systemctl start phiduhok-bot
sudo systemctl status phiduhok-bot
# and take a look to the log:
journalctl -xeu phiduhok-bot
```

When configuration changed, don't forget to restart sercice with `sudo systemctl restart phiduhok-bot`.

### Update

```bash
/opt/phiduhok_bot/updater.sh
```
