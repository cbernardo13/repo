#!/bin/bash
# ClawBrain EC2 Deployment Script
# Deploys ClawBrain to /home/ubuntu/ClawBrain on EC2

set -e

# Configuration
EC2_HOST="3.85.117.123"
EC2_USER="ubuntu"
KEY_FILE="new_openclaw_key.pem"
REMOTE_DIR="/home/ubuntu/ClawBrain"
LOCAL_DIR="."

echo "🧠 ClawBrain EC2 Deployment"
echo "=============================="
echo ""

# Ensure key permissions are correct
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Error: SSH key not found: $KEY_FILE"
    exit 1
fi

chmod 400 "$KEY_FILE"
echo "✅ SSH key permissions set"

# Create remote directory
echo "📁 Creating remote directory: $REMOTE_DIR..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_HOST}" "mkdir -p ${REMOTE_DIR}"

if [ $? -eq 0 ]; then
    echo "✅ Remote directory created"
else
    echo "❌ Failed to create remote directory"
    exit 1
fi

# Sync files
echo ""
echo "📦 Syncing files to EC2..."
rsync -avz -e "ssh -i $KEY_FILE -o StrictHostKeyChecking=no" \
    --exclude 'node_modules/' \
    --exclude 'web-dashboard/node_modules/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.DS_Store' \
    --exclude '.idea/' \
    --exclude '.vscode/' \
    --exclude '.wwebjs_auth/' \
    --exclude '.wwebjs_cache/' \
    --exclude 'test_*.py' \
    --exclude 'test_*.sh' \
    --exclude '*.log' \
    --exclude 'daily_schedule.md' \
    --exclude 'memory/*.json' \
    --exclude '.pytest_cache/' \
    --progress \
    ${LOCAL_DIR}/ \
    "${EC2_USER}@${EC2_HOST}:${REMOTE_DIR}/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Files synced successfully"
else
    echo "❌ Sync failed"
    exit 1
fi

# Copy .env separately (ensure it exists)
if [ -f ".env" ]; then
    echo ""
    echo "🔐 Copying .env file..."
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        .env \
        "${EC2_USER}@${EC2_HOST}:${REMOTE_DIR}/.env"
    
    # Set restrictive permissions on .env
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        "${EC2_USER}@${EC2_HOST}" \
        "chmod 600 ${REMOTE_DIR}/.env"
    
    echo "✅ .env copied and secured"
else
    echo "⚠️  Warning: .env file not found locally"
fi

# Make clawbrain executable
echo ""
echo "⚙️  Setting permissions..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    "${EC2_USER}@${EC2_HOST}" \
    "chmod +x ${REMOTE_DIR}/clawbrain"

echo "✅ Permissions set"

# Copy and run remote setup script
echo ""
echo "🔧 Running remote setup..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    "${EC2_USER}@${EC2_HOST}" \
    "cd ${REMOTE_DIR} && bash remote_clawbrain_setup.sh"

echo ""
echo "🚀 Restarting Service..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    "${EC2_USER}@${EC2_HOST}" \
    "pkill -f llm_brain_api.py; cd ${REMOTE_DIR} && nohup python3 llm_brain_api.py > server.log 2>&1 &"

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================="
    echo "✅ Deployment Complete!"
    echo "=============================="
    echo ""
    echo "Server URL: http://${EC2_HOST}:8001"
    echo ""
else
    echo "❌ Remote setup/restart failed"
    exit 1
fi
