# Clean Architecture Python - AWS Deployment

This directory contains CloudFormation templates and deployment scripts for deploying the Clean Architecture Python demo to AWS ECS Fargate.

## Architecture Overview

The deployment consists of:
- **ECR Repository**: Stores the Docker container images
- **VPC with ALB**: Network infrastructure with Application Load Balancer
- **ECS Fargate**: Container orchestration running StreamLit + FastAPI

## Files

### CloudFormation Templates
- `ecr.yaml` - ECR repository for container images
- `vpc-alb.yaml` - VPC, subnets, NAT gateway, ALB, and security groups
- `ecs-fargate.yaml` - ECS cluster, service, task definition, and ALB listeners

### Deployment Scripts
- `build-and-deploy.sh` - Complete deployment script
- `cleanup.sh` - Cleanup script to remove all resources

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed and running
- Bash shell

### Deploy Everything
```bash
# Make scripts executable
chmod +x cloudformation/build-and-deploy.sh cloudformation/cleanup.sh

# Deploy to dev environment in us-east-1
cloudformation/build-and-deploy.sh

# Deploy to specific environment and region
cloudformation/build-and-deploy.sh prod us-west-2
```

### Manual Deployment Steps

If you prefer to deploy step by step:

#### 1. Deploy ECR Repository
```bash
aws cloudformation deploy \
    --template-file cloudformation/ecr.yaml \
    --stack-name "clean-py-dev-myapp-ecr" \
    --parameter-overrides \
        EnvironmentName=dev \
        ApplicationName=myapp \
    --region us-east-1
```

#### 2. Build and Push Container
```bash
# Get ECR URI
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name "clean-py-dev-myapp-ecr" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text)

# Login to ECR
ECR_REGISTRY=$(echo $ECR_URI | cut -d'/' -f1)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push (with correct platform for AWS Fargate)
docker build --platform linux/amd64 -t clean-py-myapp .
docker tag clean-py-myapp:latest "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"


```

#### 3. Deploy VPC and ALB
```bash
aws cloudformation deploy \
    --template-file cloudformation/vpc-alb.yaml \
    --stack-name "clean-py-dev-myapp-vpc-alb" \
    --parameter-overrides \
        EnvironmentName=dev \
        ApplicationName=myapp \
    --region us-east-1
```

#### 4. Deploy ECS Service
```bash
aws cloudformation deploy \
    --template-file cloudformation/ecs-fargate.yaml \
    --stack-name "clean-py-dev-myapp-ecs" \
    --parameter-overrides \
        EnvironmentName=dev \
        ApplicationName=myapp \
        ImageURI="${ECR_URI}:latest" \
        DesiredCount=1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

## Access the Application

After deployment, get the URLs:

```bash
# Streamlit App
aws cloudformation describe-stacks \
    --stack-name "clean-py-dev-myapp-ecs" \
    --query 'Stacks[0].Outputs[?OutputKey==`StreamlitURL`].OutputValue' \
    --output text

# FastAPI Docs
aws cloudformation describe-stacks \
    --stack-name "clean-py-dev-myapp-ecs" \
    --query 'Stacks[0].Outputs[?OutputKey==`FastAPIURL`].OutputValue' \
    --output text
```

## URL Structure

The ALB routes traffic based on path patterns:
- `/` → StreamLit application (port 8501)
- `/api/*` → FastAPI application (port 8000)
- `/docs` → FastAPI documentation
- `/health` → FastAPI health check

## Cleanup

To remove all resources:
```bash
cloudformation/cleanup.sh

# Or for specific environment/region
cloudformation/cleanup.sh prod us-west-2
```

## Cost Considerations

This deployment includes:
- **NAT Gateway**: ~$45/month (can be removed for public subnet deployment)
- **Application Load Balancer**: ~$22/month
- **ECS Fargate**: ~$15/month for 1 task (0.5 vCPU, 1GB RAM)
- **CloudWatch Logs**: Minimal cost
- **ECR**: $0.10/GB/month for stored images

**Total estimated cost**: ~$82/month for dev environment

## Troubleshooting

### Common Issues

1. **ECS Service fails to start**
   - Check CloudWatch logs: `/ecs/dev-myapp`
   - Verify security groups allow ALB → ECS communication
   - Check task definition resource allocation

2. **ALB health checks fail**
   - Ensure applications bind to `0.0.0.0` not `127.0.0.1`
   - Check health check paths: `/health` for FastAPI, `/` for StreamLit
   - Verify container ports match ALB target group ports

3. **New code not visible after deployment**
   - ECS doesn't automatically restart when pushing new images with same tag
   - Force new deployment: `aws ecs update-service --cluster dev-myapp-cluster --service dev-myapp-service --force-new-deployment`
   - Clear browser cache (Ctrl+F5 / Cmd+Shift+R)
   - Wait 2-3 minutes for deployment to complete

4. **Docker build fails**
   - Ensure you're in the project root directory
   - Check Dockerfile paths and dependencies
   - Verify requirements.txt includes all dependencies

5. **ECR push permission denied**
   - Verify AWS credentials have ECR permissions
   - Check ECR login command output
   - Ensure repository exists before pushing

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services \
    --cluster dev-myapp-cluster \
    --services dev-myapp-service

# View ECS service logs
aws logs tail /ecs/dev-myapp --follow

# Force deployment with latest container image (after pushing new image)
aws ecs update-service \
    --cluster dev-myapp-cluster \
    --service dev-myapp-service \
    --force-new-deployment

# Check deployment progress
aws ecs describe-services \
    --cluster dev-myapp-cluster \
    --services dev-myapp-service \
    --query 'services[0].deployments[?status==`PRIMARY`].{Status:rolloutState,Updated:updatedAt}' \
    --output table

# Connect to running ECS task
aws ecs execute-command \
    --cluster dev-myapp-cluster \
    --task TASK_ID \
    --container dev-myapp-container \
    --command "/bin/bash" \
    --interactive
```

## Security Notes

- ECS tasks run in private subnets with no direct internet access
- ALB is internet-facing but access is controlled by security groups
- All communication between ALB and ECS is within the VPC
- ECR images are scanned for vulnerabilities
- Task execution role has minimal required permissions

## Customization

### Environment Variables
Add environment variables to the task definition in `ecs-fargate.yaml`:
```yaml
Environment:
  - Name: ENV
    Value: !Ref EnvironmentName
  - Name: DATABASE_URL
    Value: "your-database-url"
```

### Scaling
Modify auto-scaling parameters in `ecs-fargate.yaml`:
- `MinCapacity`: Minimum number of tasks
- `MaxCapacity`: Maximum number of tasks
- `TargetValue`: CPU utilization target for scaling

### Custom Domain
To use a custom domain:
1. Add SSL certificate ARN to ALB listener
2. Create Route53 record pointing to ALB
3. Update security groups if needed

## Updating CloudFormation Stacks

If you modify YAML templates locally, you can update the deployed stacks:

### Option 1: Re-run Full Deployment (Recommended)
```bash
# Updates all stacks with local changes
./build-and-deploy.sh
```

### Option 2: Update Individual Stacks
```bash
# Update VPC/ALB stack
aws cloudformation deploy \
    --template-file vpc-alb.yaml \
    --stack-name "clean-py-dev-myapp-vpc-alb" \
    --parameter-overrides \
        EnvironmentName=dev \
        ApplicationName=myapp \
    --region us-east-1

# Update ECS stack
aws cloudformation deploy \
    --template-file ecs-fargate.yaml \
    --stack-name "clean-py-dev-myapp-ecs" \
    --parameter-overrides \
        EnvironmentName=dev \
        ApplicationName=myapp \
        ImageURI=YOUR_ECR_URI:latest \
        DesiredCount=1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

### Preview Changes Before Applying
```bash
# See what will change without applying
aws cloudformation deploy \
    --template-file your-template.yaml \
    --stack-name your-stack-name \
    --no-execute-changeset \
    --parameter-overrides ...
```

**Note**: Replace `YOUR_ECR_URI` with your actual ECR repository URI from the ECR stack outputs.
