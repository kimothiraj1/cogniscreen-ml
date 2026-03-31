#!/bin/bash
# CogniScreen ML — Full AWS ECR + ECS Deploy Script
# Run this from your project root (where Dockerfile lives)
# Prerequisites: AWS CLI installed + configured (aws configure)

set -e  # exit on any error

# ── CONFIG — edit these ──────────────────────────────────────────────────────
AWS_REGION="ap-south-1"          # Mumbai — closest to India
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="cogniscreen-ml"
IMAGE_TAG="latest"
CLUSTER_NAME="cogniscreen-cluster"
SERVICE_NAME="cogniscreen-ml-service"

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo ""
echo "=========================================="
echo "  CogniScreen ML — AWS Deploy"
echo "  Account: ${AWS_ACCOUNT_ID}"
echo "  Region:  ${AWS_REGION}"
echo "=========================================="

# ── STEP 1: Generate API key if not in .env ───────────────────────────────────
if [ ! -f .env ]; then
  echo ""
  echo "STEP 1: No .env found — generating API key..."
  python generate_api_key.py
  echo ""
  echo "  >> Paste the key above into .env as ML_API_KEY=csk_..."
  echo "  >> Then re-run this script."
  exit 1
fi

source .env
if [ -z "$ML_API_KEY" ]; then
  echo "ERROR: ML_API_KEY not set in .env"
  exit 1
fi

echo "STEP 1: API key found in .env ✓"

# ── STEP 2: Push secrets to AWS SSM Parameter Store ──────────────────────────
echo ""
echo "STEP 2: Storing secrets in AWS SSM Parameter Store..."

aws ssm put-parameter \
  --name "/cogniscreen/ML_API_KEY" \
  --value "$ML_API_KEY" \
  --type "SecureString" \
  --overwrite \
  --region $AWS_REGION

aws ssm put-parameter \
  --name "/cogniscreen/TWILIO_ACCOUNT_SID" \
  --value "${TWILIO_ACCOUNT_SID:-placeholder}" \
  --type "SecureString" \
  --overwrite \
  --region $AWS_REGION

aws ssm put-parameter \
  --name "/cogniscreen/TWILIO_AUTH_TOKEN" \
  --value "${TWILIO_AUTH_TOKEN:-placeholder}" \
  --type "SecureString" \
  --overwrite \
  --region $AWS_REGION

aws ssm put-parameter \
  --name "/cogniscreen/TWILIO_FROM_PHONE" \
  --value "${TWILIO_FROM_PHONE:-+10000000000}" \
  --type "SecureString" \
  --overwrite \
  --region $AWS_REGION

echo "  Secrets stored in SSM ✓"

# ── STEP 3: Create ECR repo (skip if exists) ──────────────────────────────────
echo ""
echo "STEP 3: Creating ECR repository..."
aws ecr create-repository \
  --repository-name $ECR_REPO \
  --region $AWS_REGION 2>/dev/null || echo "  Repo already exists, skipping."

# ── STEP 4: Build and push Docker image ──────────────────────────────────────
echo ""
echo "STEP 4: Building Docker image..."
docker build -t ${ECR_REPO}:${IMAGE_TAG} .

echo "  Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "  Tagging and pushing image..."
docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:${IMAGE_TAG}
echo "  Image pushed to ECR ✓"

# ── STEP 5: Update task definition with real account ID ───────────────────────
echo ""
echo "STEP 5: Updating task definition..."
sed "s/YOUR_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" aws_ecs_task_definition.json > /tmp/task_def.json

aws ecs register-task-definition \
  --cli-input-json file:///tmp/task_def.json \
  --region $AWS_REGION > /dev/null

echo "  Task definition registered ✓"

# ── STEP 6: Create or update ECS service ─────────────────────────────────────
echo ""
echo "STEP 6: Deploying to ECS..."

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $AWS_REGION \
  --query 'services[0].status' \
  --output text 2>/dev/null || echo "MISSING")

if [ "$SERVICE_EXISTS" = "ACTIVE" ]; then
  echo "  Updating existing service..."
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition cogniscreen-ml \
    --force-new-deployment \
    --region $AWS_REGION > /dev/null
else
  echo "  NOTE: ECS cluster/service not found."
  echo "  Create it manually in AWS Console first (see doc), then re-run."
  echo "  Your image is ready at: ${ECR_URI}:${IMAGE_TAG}"
fi

# ── DONE ──────────────────────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  Deploy complete!"
echo ""
echo "  ECR Image:  ${ECR_URI}:${IMAGE_TAG}"
echo "  API Key:    stored in SSM /cogniscreen/ML_API_KEY"
echo ""
echo "  Share with backend team:"
echo "  URL: http://YOUR_ECS_PUBLIC_IP:8000"
echo "  Key: (send via Slack DM, get from .env)"
echo "=========================================="
