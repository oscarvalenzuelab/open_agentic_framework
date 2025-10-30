#!/bin/bash

# DigitalOcean Droplet Deployment Script
# Run this script after creating a Ubuntu 22.04 Droplet with at least 4GB RAM

echo "=== Open Agentic Framework - DigitalOcean Deployment ==="
echo ""

# Update system
echo "1. Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "2. Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
echo "3. Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
echo "4. Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
echo "5. Cloning repository..."
git clone https://github.com/oscarvalenzuelab/open_agentic_framework.git
cd open_agentic_framework/agentic_ai_framework

# Create .env file
echo "6. Creating environment file..."
cat > .env << 'EOF'
# DigitalOcean Deployment Configuration
OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=granite3.2:2b
DATABASE_PATH=/app/data/agentic_ai.db
API_HOST=0.0.0.0
API_PORT=8000

# OpenAI Configuration (replace with your key)
OPENAI_ENABLED=true
OPENAI_API_KEY=your-openai-api-key-here
DEFAULT_LLM_PROVIDER=openai
OPENAI_DEFAULT_MODEL=gpt-3.5-turbo

# Optional: Email Configuration
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
EOF

echo ""
echo "IMPORTANT: Edit .env file to add your OPENAI_API_KEY"
echo "Run: nano agentic_ai_framework/.env"
echo ""

# Configure firewall
echo "7. Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API/Web UI
sudo ufw allow 11434/tcp # Ollama
sudo ufw --force enable

# Create systemd service for auto-start
echo "8. Creating systemd service..."
sudo cat > /etc/systemd/system/agentic-framework.service << 'EOF'
[Unit]
Description=Open Agentic Framework
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/open_agentic_framework/agentic_ai_framework
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable agentic-framework

echo ""
echo "=== Deployment Script Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano open_agentic_framework/agentic_ai_framework/.env"
echo "2. Add your OPENAI_API_KEY"
echo "3. Start the application: cd open_agentic_framework/agentic_ai_framework && docker-compose up -d"
echo "4. Check logs: docker-compose logs -f"
echo "5. Access the application at: http://YOUR_DROPLET_IP:8000"
echo ""
echo "The application will download models on first startup (5-10 minutes)"