#!/bin/bash

# Clean Architecture Python - Build and Deploy Script
# Usage: ./build-and-deploy.sh [environment] [region]

set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
APP_NAME="myapp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo_error "Docker not found. Please install Docker."
    exit 1
fi

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ $? -ne 0 ]; then
    echo_error "Failed to get AWS Account ID. Check your AWS credentials."
    exit 1
fi

echo_info "Starting deployment for environment: $ENVIRONMENT in region: $REGION"
echo_info "AWS Account ID: $ACCOUNT_ID"

# Step 1: Deploy ECR repository
echo_info "Step 1: Deploying ECR repository..."
aws cloudformation deploy \
    --template-file ecr.yaml \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecr" \
    --parameter-overrides \
        EnvironmentName=$ENVIRONMENT \
        ApplicationName=$APP_NAME \
    --region $REGION \
    --tags \
        Environment=$ENVIRONMENT \
        Project="clean-py" \
        Component="ecr"

if [ $? -eq 0 ]; then
    echo_success "ECR repository deployed successfully"
else
    echo_error "Failed to deploy ECR repository"
    exit 1
fi

# Get ECR repository URI
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecr" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text \
    --region $REGION)

echo_info "ECR Repository URI: $ECR_URI"

# Step 2: Build and push Docker image
echo_info "Step 2: Building and pushing Docker image..."

# Login to ECR
echo_info "Logging into ECR..."
ECR_REGISTRY=$(echo $ECR_URI | cut -d'/' -f1)
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build Docker image
echo_info "Building Docker image..."
cd ..
docker build --platform linux/amd64 -t clean-py-$APP_NAME .
docker tag clean-py-$APP_NAME:latest "${ECR_URI}:latest"
docker tag clean-py-$APP_NAME:latest "${ECR_URI}:$(date +%Y%m%d-%H%M%S)"

# Push Docker image
echo_info "Pushing Docker image..."
docker push "${ECR_URI}:latest"
docker push "${ECR_URI}:$(date +%Y%m%d-%H%M%S)"

echo_success "Docker image built and pushed successfully"

# Return to cloudformation directory
cd cloudformation

# Step 3: Deploy VPC and ALB
echo_info "Step 3: Deploying VPC and ALB..."
aws cloudformation deploy \
    --template-file vpc-alb.yaml \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-vpc-alb" \
    --parameter-overrides \
        EnvironmentName=$ENVIRONMENT \
        ApplicationName=$APP_NAME \
    --region $REGION \
    --tags \
        Environment=$ENVIRONMENT \
        Project="clean-py" \
        Component="vpc"

if [ $? -eq 0 ]; then
    echo_success "VPC and ALB deployed successfully"
else
    echo_error "Failed to deploy VPC and ALB"
    exit 1
fi

# Step 4: Deploy ECS Fargate service
echo_info "Step 4: Deploying ECS Fargate service..."
aws cloudformation deploy \
    --template-file ecs-fargate.yaml \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecs" \
    --parameter-overrides \
        EnvironmentName=$ENVIRONMENT \
        ApplicationName=$APP_NAME \
        ImageURI=$ECR_URI:latest \
        DesiredCount=1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --tags \
        Environment=$ENVIRONMENT \
        Project="clean-py" \
        Component="ecs"

if [ $? -eq 0 ]; then
    echo_success "ECS Fargate service deployed successfully"
else
    echo_error "Failed to deploy ECS Fargate service"
    exit 1
fi

# Step 5: Force new deployment to ensure latest image is used
echo_info "Step 5: Forcing new deployment to use latest container image..."
aws ecs update-service \
    --cluster "$ENVIRONMENT-$APP_NAME-cluster" \
    --service "$ENVIRONMENT-$APP_NAME-service" \
    --force-new-deployment \
    --region $REGION > /dev/null

if [ $? -eq 0 ]; then
    echo_success "Forced deployment initiated successfully"
    echo_info "Waiting for deployment to complete (this may take 2-3 minutes)..."

    # Wait for deployment to complete
    aws ecs wait services-stable \
        --cluster "$ENVIRONMENT-$APP_NAME-cluster" \
        --services "$ENVIRONMENT-$APP_NAME-service" \
        --region $REGION

    if [ $? -eq 0 ]; then
        echo_success "Deployment completed and services are stable"
    else
        echo_warning "Deployment timeout - services may still be starting"
    fi
else
    echo_warning "Failed to force new deployment, but initial deployment was successful"
fi

# Get application URLs
echo_info "Getting application URLs..."
STREAMLIT_URL=$(aws cloudformation describe-stacks \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecs" \
    --query 'Stacks[0].Outputs[?OutputKey==`StreamlitURL`].OutputValue' \
    --output text \
    --region $REGION)

FASTAPI_URL=$(aws cloudformation describe-stacks \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecs" \
    --query 'Stacks[0].Outputs[?OutputKey==`FastAPIURL`].OutputValue' \
    --output text \
    --region $REGION)

echo_success "Deployment completed successfully!"
echo ""
echo "=== Application URLs ==="
echo_info "Streamlit App: $STREAMLIT_URL"
echo_info "FastAPI Docs: $FASTAPI_URL"
echo ""
echo_warning "Note: It may take a few minutes for the services to be healthy and accessible."
echo_info "You can check the ECS service status in the AWS Console."
