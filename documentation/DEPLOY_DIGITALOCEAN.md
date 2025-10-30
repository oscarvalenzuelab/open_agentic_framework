# Deploy to DigitalOcean - Quick Guide

## Option 1: App Platform (Easiest - 5 minutes)

### Steps:
1. **Push code to GitHub** (if not already done)
2. **Create App** at https://cloud.digitalocean.com/apps
3. **Connect GitHub** → Select your repo
4. **Auto-detect Dockerfile** → Set source dir: `/agentic_ai_framework`
5. **Add Environment Variables:**
   ```
   OPENAI_API_KEY=your-key-here
   OPENAI_ENABLED=true
   DEFAULT_LLM_PROVIDER=openai
   ```
6. **Choose Plan:** Professional-S (4GB RAM) ~$40/month
7. **Deploy** → Wait 10-15 minutes

**Access at:** `https://your-app-name.ondigitalocean.app`

## Option 2: Droplet (More Control - 20 minutes)

### Steps:
1. **Create Droplet:**
   - Ubuntu 22.04 LTS
   - 4GB RAM / 2 vCPUs ($24/month)
   - NYC or SFO region

2. **SSH into Droplet:**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Run deployment script:**
   ```bash
   # Download and run the script
   curl -O https://raw.githubusercontent.com/oscarvalenzuelab/open_agentic_framework/main/deploy-digitalocean.sh
   chmod +x deploy-digitalocean.sh
   ./deploy-digitalocean.sh
   ```

4. **Configure API Key:**
   ```bash
   nano open_agentic_framework/agentic_ai_framework/.env
   # Add your OPENAI_API_KEY
   ```

5. **Start the application:**
   ```bash
   cd open_agentic_framework/agentic_ai_framework
   docker-compose up -d
   ```

6. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

**Access at:** `http://your-droplet-ip:8000`

## Environment Variables

### Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_ENABLED=true` - Enable OpenAI provider
- `DEFAULT_LLM_PROVIDER=openai` - Use OpenAI as default

### Optional:
- `SMTP_HOST` - Email server for notifications
- `SMTP_USERNAME` - Email username
- `SMTP_PASSWORD` - Email password

## Monitoring

- **Health Check:** `/health`
- **API Docs:** `/docs`
- **Web UI:** `/ui`
- **Provider Status:** `/providers`

## Troubleshooting

### App Platform Issues:
- Check build logs in DigitalOcean dashboard
- Ensure Dockerfile path is correct
- Verify environment variables are set

### Droplet Issues:
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs agentic-ai

# Restart services
docker-compose restart

# Check disk space
df -h

# Check memory
free -m
```

## Cost Breakdown

| Option | Monthly Cost | Specs |
|--------|-------------|-------|
| App Platform Basic | $25 | 1GB RAM, 0.5 vCPU |
| App Platform Pro | $40 | 2GB RAM, 1 vCPU |
| Droplet Basic | $24 | 4GB RAM, 2 vCPUs |
| Droplet + Backups | $29 | 4GB RAM + weekly backups |

## Security Recommendations

1. **Enable firewall** (Droplet only):
   ```bash
   ufw allow 22,8000,11434/tcp
   ufw enable
   ```

2. **Use HTTPS** (App Platform includes SSL)

3. **Set strong passwords** for email/SMTP

4. **Regular updates:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Support

- DigitalOcean Docs: https://docs.digitalocean.com
- App Platform Guide: https://docs.digitalocean.com/products/app-platform/
- Open Agentic Framework: https://github.com/oscarvalenzuelab/open_agentic_framework