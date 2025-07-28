#!/bin/bash
cd /opt/phiduhok_bot
systemctl stop phiduhok-bot
sudo -u botrunner git pull --rebase
#rm -rf /opt/phiduhok_bot/.venv
#sudo -u botrunner python3 -m venv .venv
sudo -u botrunner /opt/phiduhok_bot/.venv/bin/pip install -r requirements.txt --no-cache-dir
chown botrunner:botrunner /opt/phiduhok_bot -R
systemctl start phiduhok-bot
systemctl status phiduhok-bot
