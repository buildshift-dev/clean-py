#!/bin/bash

# Clean Architecture Python - Cleanup Script
# Usage: ./cleanup.sh [environment] [region]

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

echo_warning "This will delete all demo resources for environment: $ENVIRONMENT in region: $REGION"
echo_warning "This action cannot be undone!"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Cleanup cancelled."
    exit 0
fi

echo_info "Starting cleanup for environment: $ENVIRONMENT in region: $REGION"

# Step 1: Delete ECS service
echo_info "Step 1: Deleting ECS Fargate service..."
aws cloudformation delete-stack \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecs" \
    --region $REGION

echo_info "Waiting for ECS stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecs" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo_success "ECS Fargate service deleted successfully"
else
    echo_error "Failed to delete ECS Fargate service"
fi

# Step 2: Delete VPC and ALB
echo_info "Step 2: Deleting VPC and ALB..."
aws cloudformation delete-stack \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-vpc" \
    --region $REGION

echo_info "Waiting for VPC stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-vpc" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo_success "VPC and ALB deleted successfully"
else
    echo_error "Failed to delete VPC and ALB"
fi

# Step 3: Clean up ECR repository (optional)
echo ""
echo_warning "ECR repository contains Docker images that may be useful to keep."
read -p "Do you want to delete the ECR repository and all images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Step 3: Deleting ECR repository..."
    
    # First, delete all images in the repository
    REPO_NAME="clean-py-$ENVIRONMENT-$APP_NAME-app"
    echo_info "Deleting all images in repository: $REPO_NAME"
    
    # Get list of image digests
    IMAGE_DIGESTS=$(aws ecr list-images \
        --repository-name $REPO_NAME \
        --query 'imageIds[*].imageDigest' \
        --output text \
        --region $REGION 2>/dev/null)
    
    if [ ! -z "$IMAGE_DIGESTS" ]; then
        # Delete images in batches
        for digest in $IMAGE_DIGESTS; do
            aws ecr batch-delete-image \
                --repository-name $REPO_NAME \
                --image-ids imageDigest=$digest \
                --region $REGION >/dev/null 2>&1
        done
        echo_info "All images deleted from ECR repository"
    fi
    
    # Delete the ECR repository
    aws cloudformation delete-stack \
        --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecr" \
        --region $REGION
    
    echo_info "Waiting for ECR stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "clean-py-$ENVIRONMENT-$APP_NAME-ecr" \
        --region $REGION
    
    if [ $? -eq 0 ]; then
        echo_success "ECR repository deleted successfully"
    else
        echo_error "Failed to delete ECR repository"
    fi
else
    echo_info "ECR repository preserved"
fi

# Step 4: Clean up local Docker images (optional)
echo ""
read -p "Do you want to clean up local Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Cleaning up local Docker images..."
    docker rmi clean-py-$APP_NAME:latest 2>/dev/null || true
    docker system prune -f
    echo_success "Local Docker images cleaned up"
fi

echo ""
echo_success "Cleanup completed!"
echo_info "All demo resources for environment '$ENVIRONMENT' have been removed."