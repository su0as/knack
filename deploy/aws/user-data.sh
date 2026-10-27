#!/bin/bash
# Knack on one AWS Graviton instance (Ubuntu 24.04 arm64): console on port 80 + practice runs with OpenCV 5 perception.
# Secrets come from SSM Parameter Store (SecureString), never from this file. No SSH port: use Session Manager.
set -euxo pipefail
REGION=ap-southeast-1
BUCKET=__BUCKET__          # set at launch: private S3 bucket holding the source tarball and run summaries
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q python3-venv python3-pip libosmesa6 libgl1 curl
# small instance: add 2 GiB swap so parallel MuJoCo episodes cannot OOM the console
if [ ! -f /swapfile ]; then fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && echo '/swapfile none swap sw 0 0' >> /etc/fstab; fi
useradd -m -s /bin/bash knack || true
mkdir -p /opt/knack /var/lib/knack/runs && chown -R knack:knack /var/lib/knack /opt/knack
sudo -u knack python3 -m venv /opt/knack/.venv
sudo -u knack /opt/knack/.venv/bin/pip install -q boto3 awscli
sudo -u knack /opt/knack/.venv/bin/aws s3 cp "s3://$BUCKET/src/knack.tar.gz" /tmp/knack.tar.gz --region $REGION
sudo -u knack tar -xzf /tmp/knack.tar.gz -C /opt/knack --strip-components=1
sudo -u knack /opt/knack/.venv/bin/pip install -q -e /opt/knack
param() { /opt/knack/.venv/bin/python -c "import boto3,sys;print(boto3.client('ssm',region_name='$REGION').get_parameter(Name=sys.argv[1],WithDecryption=True)['Parameter']['Value'])" "$1"; }
umask 077
cat > /etc/knack.env <<ENV
NEBIUS_API_KEY=$(param /knack/NEBIUS_API_KEY)
KNACK_PASSCODE=$(param /knack/PASSCODE)
MUJOCO_GL=osmesa
PYOPENGL_PLATFORM=osmesa
KNACK_BUCKET=$BUCKET
ENV
chown root:knack /etc/knack.env && chmod 640 /etc/knack.env
cat > /etc/systemd/system/knack-ui.service <<'UNIT'
[Unit]
Description=Knack console (public, read-only without passcode)
After=network-online.target
[Service]
User=knack
EnvironmentFile=/etc/knack.env
WorkingDirectory=/var/lib/knack
ExecStart=/opt/knack/.venv/bin/python -m knack ui --host 0.0.0.0 --port 80 --public --no-browser --runs /var/lib/knack/runs
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=always
NoNewPrivileges=true
ProtectSystem=full
[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/knack-sync.service <<'UNIT'
[Unit]
Description=Copy run summaries to S3
[Service]
Type=oneshot
User=knack
EnvironmentFile=/etc/knack.env
ExecStart=/bin/bash -c '[ -n "$KNACK_BUCKET" ] && /opt/knack/.venv/bin/aws s3 sync /var/lib/knack/runs "s3://$KNACK_BUCKET/runs" --region ap-southeast-1 --exclude "*.tmp" || true'
UNIT
cat > /etc/systemd/system/knack-sync.timer <<'UNIT'
[Unit]
Description=Sync Knack runs to S3 every 10 minutes
[Timer]
OnBootSec=5min
OnUnitActiveSec=10min
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now knack-ui.service knack-sync.timer
# One demo practice run on this instance (capped at $0.10 of Token Factory calls), so the console has a live AWS run.
sudo -u knack bash -c 'set -a; . /etc/knack.env; set +a; cd /var/lib/knack && /opt/knack/.venv/bin/python -m knack learn lift --coder super --realism vision --rounds 6 --n 8 --eval 50 --budget 0.10 --workers 2 --runs /var/lib/knack/runs > /var/lib/knack/first-run.log 2>&1' &
