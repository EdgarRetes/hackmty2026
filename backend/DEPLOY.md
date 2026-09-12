# Deploying to a plain Ubuntu VPS

No Docker. Gunicorn runs as a systemd service behind Nginx. Copy-paste
these commands on the server, in order.

## 0. One-time server setup

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx

# Non-root user the app runs as (matches deploy/gunicorn.service's User=deploy)
sudo adduser --disabled-password --gecos "" deploy
```

## 1. Get the code onto the server

```bash
sudo -iu deploy
mkdir -p ~/factorai
cd ~/factorai
git clone <your-repo-url> .
cd backend
```

(Adjust the clone step if you deploy by `scp`/`rsync` instead of git — the
important part is that the code ends up at `/home/deploy/factorai/backend`,
which is what `deploy/gunicorn.service` points at.)

## 2. Create the virtualenv and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Set up the .env file

```bash
cp .env.example .env
nano .env
```

Fill in real values. At minimum: `SECRET_KEY`, `DATABASE_URL`,
`DB_PASSWORD` (Tiger Cloud omits the password from the connection string
— see README.md), `ALLOWED_HOSTS` (your server's domain/IP),
`CORS_ALLOWED_ORIGINS` (your Vercel frontend URL). Also add this line so
both `manage.py` and Gunicorn use production settings:

```
DJANGO_SETTINGS_MODULE=factorai_config.settings.production
```

## 4. Run migrations

```bash
set -a
source .env
set +a
python manage.py migrate
```

## 5. Install and start the Gunicorn service

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl status gunicorn   # should show "active (running)"
```

Whenever you change code and redeploy: `sudo systemctl restart gunicorn`.

## 6. Install and reload the Nginx config

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/factorai
sudo ln -sf /etc/nginx/sites-available/factorai /etc/nginx/sites-enabled/factorai
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Verify

```bash
curl http://localhost/api/health/
```

Should return `{"status": "ok", "service": "factorai-backend"}`. If it
works locally on the server but not from outside, check your VPS
provider's firewall/security group allows inbound port 80.
