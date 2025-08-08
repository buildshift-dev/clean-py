# AWS Security Patterns for Clean Architecture

This document provides comprehensive security patterns and best practices specifically for AWS-deployed Clean Architecture applications, covering infrastructure security, application security, and operational security.

## Table of Contents

- [Infrastructure Security](#infrastructure-security)
- [Application Security](#application-security)
- [Data Security](#data-security)
- [Network Security](#network-security)
- [Identity and Access Management](#identity-and-access-management)
- [Monitoring and Compliance](#monitoring-and-compliance)
- [Incident Response](#incident-response)
- [Security Automation](#security-automation)

## Infrastructure Security

### AWS Account Security Foundation

**Account Structure:**
```
┌─────────────────┐
│   Master Org    │
│   Account       │
└─────┬───────────┘
      │
      ├── Dev Account (Sandbox)
      ├── Staging Account (Pre-prod)
      ├── Production Account (Prod)
      └── Security Account (Logging/Monitoring)
```

**Core Security Services:**
- **AWS Organizations**: Centralized account management
- **AWS Control Tower**: Governance and compliance
- **AWS Config**: Configuration compliance monitoring
- **AWS CloudTrail**: API audit logging
- **AWS GuardDuty**: Threat detection
- **AWS Security Hub**: Centralized security findings

### ECS/Fargate Security Patterns

**Container Security Configuration:**
```json
{
  "taskDefinition": {
    "family": "clean-py-api",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
    "containerDefinitions": [
      {
        "name": "api",
        "image": "your-account.dkr.ecr.region.amazonaws.com/clean-py:latest",
        "essential": true,
        "portMappings": [
          {
            "containerPort": 8000,
            "protocol": "tcp"
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "/aws/ecs/clean-py",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "ecs"
          }
        },
        "environment": [
          {
            "name": "ENVIRONMENT",
            "value": "production"
          }
        ],
        "secrets": [
          {
            "name": "DATABASE_URL",
            "valueFrom": "arn:aws:secretsmanager:region:account:secret:database-url"
          },
          {
            "name": "JWT_SECRET_KEY",
            "valueFrom": "arn:aws:secretsmanager:region:account:secret:jwt-private-key"
          }
        ],
        "readonlyRootFilesystem": true,
        "user": "1000:1000",
        "linuxParameters": {
          "capabilities": {
            "drop": ["ALL"]
          }
        }
      }
    ]
  }
}
```

**Security Best Practices:**
- Use read-only root filesystem
- Run as non-root user
- Drop all Linux capabilities
- Use AWS Secrets Manager for sensitive data
- Enable container insights for monitoring
- Scan images with ECR vulnerability scanning

### Lambda Security Patterns

**Function Configuration:**
```python
# serverless.yml or CloudFormation
Resources:
  CleanPyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: clean-py-api
      Runtime: python3.11
      Handler: lambda_function.lambda_handler
      Code:
        S3Bucket: your-deployment-bucket
        S3Key: clean-py.zip
      Role: !GetAtt LambdaExecutionRole.Arn
      Environment:
        Variables:
          ENVIRONMENT: production
          LOG_LEVEL: INFO
      VpcConfig:
        SecurityGroupIds:
          - !Ref LambdaSecurityGroup
        SubnetIds:
          - !Ref PrivateSubnet1
          - !Ref PrivateSubnet2
      DeadLetterQueue:
        TargetArn: !GetAtt DeadLetterQueue.Arn
      ReservedConcurrencyLimit: 100
      Timeout: 30
      KMSKeyArn: !GetAtt LambdaKMSKey.Arn

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
      Policies:
        - PolicyName: CleanPyLambdaPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource:
                  - !Ref DatabaseSecret
                  - !Ref JWTSecret
              - Effect: Allow
                Action:
                  - kms:Decrypt
                Resource: !GetAtt LambdaKMSKey.Arn
```

**Lambda Security Checklist:**
- [ ] Use least-privilege IAM roles
- [ ] Enable VPC configuration for database access
- [ ] Use environment encryption with KMS
- [ ] Configure dead letter queues
- [ ] Set appropriate timeout and memory limits
- [ ] Enable X-Ray tracing for observability
- [ ] Use reserved concurrency to prevent cost overruns

## Application Security

### Secure Configuration Management

**Environment-Based Configuration:**
```python
# src/infrastructure/config/aws_config.py

import os
import boto3
from typing import Dict, Any, Optional
from functools import lru_cache

class AWSConfigManager:
    """Secure configuration management for AWS environments."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'local')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.secrets_client = boto3.client('secretsmanager', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
    
    @lru_cache(maxsize=32)
    def get_secret(self, secret_name: str) -> str:
        """Get secret from AWS Secrets Manager with caching."""
        try:
            full_secret_name = f"{self.environment}/{secret_name}"
            response = self.secrets_client.get_secret_value(SecretId=full_secret_name)
            return response['SecretString']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ConfigurationError(f"Secret not found: {full_secret_name}")
            raise ConfigurationError(f"Failed to retrieve secret: {str(e)}")
    
    @lru_cache(maxsize=64)
    def get_parameter(self, parameter_name: str, decrypt: bool = False) -> str:
        """Get parameter from AWS Systems Manager Parameter Store."""
        try:
            full_parameter_name = f"/{self.environment}/{parameter_name}"
            response = self.ssm_client.get_parameter(
                Name=full_parameter_name,
                WithDecryption=decrypt
            )
            return response['Parameter']['Value']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                raise ConfigurationError(f"Parameter not found: {full_parameter_name}")
            raise ConfigurationError(f"Failed to retrieve parameter: {str(e)}")
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration securely."""
        return {
            'host': self.get_parameter('database/host'),
            'port': int(self.get_parameter('database/port')),
            'database': self.get_parameter('database/name'),
            'username': self.get_parameter('database/username'),
            'password': self.get_secret('database/password'),
            'ssl_mode': 'require' if self.environment == 'production' else 'prefer',
        }
    
    def get_jwt_config(self) -> Dict[str, str]:
        """Get JWT configuration securely."""
        return {
            'private_key': self.get_secret('jwt/private-key'),
            'public_key': self.get_secret('jwt/public-key'),
            'algorithm': 'RS256',
            'audience': self.get_parameter('jwt/audience'),
            'issuer': self.get_parameter('jwt/issuer'),
            'access_token_expire_minutes': int(self.get_parameter('jwt/access-token-expire-minutes')),
            'refresh_token_expire_days': int(self.get_parameter('jwt/refresh-token-expire-days')),
        }
```

### Input Validation and Sanitization

**Pydantic Security Models:**
```python
# src/application/security/validation.py

from typing import Optional, List
from pydantic import BaseModel, Field, validator, root_validator
import re
from datetime import datetime

class SecureInputModel(BaseModel):
    """Base model with security validations."""
    
    class Config:
        # Prevent extra fields
        extra = "forbid"
        # Validate assignment to prevent injection
        validate_assignment = True
        # Use enum values for consistency
        use_enum_values = True

class SecureEmailModel(BaseModel):
    """Secure email validation."""
    
    email: str = Field(..., min_length=5, max_length=254)
    
    @validator('email')
    def validate_email(cls, v):
        # Email regex pattern (RFC 5322 compliant)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        
        # Prevent common injection patterns
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Email contains prohibited content')
        
        return v.lower().strip()

class SecureUserInput(SecureInputModel):
    """Secure user input validation."""
    
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., min_length=5, max_length=254)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        # Only allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name contains invalid characters')
        
        # Prevent XSS
        if any(char in v for char in '<>"\'&'):
            raise ValueError('Name contains prohibited characters')
        
        return v.strip().title()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', v)
        
        # Validate phone number length
        if len(digits) not in [10, 11]:
            raise ValueError('Invalid phone number length')
        
        return f"+{digits}" if len(digits) == 11 else f"+1{digits}"

class SecureSearchQuery(SecureInputModel):
    """Secure search query validation."""
    
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=10000)
    
    @validator('query')
    def validate_search_query(cls, v):
        # Prevent SQL injection patterns
        sql_patterns = [
            r'\bselect\b', r'\binsert\b', r'\bupdate\b', r'\bdelete\b',
            r'\bdrop\b', r'\balter\b', r'\bcreate\b', r'\bunion\b',
            r'--', r'/\*', r'\*/', r';', r'\bor\b\s+\d+\s*=\s*\d+',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Search query contains prohibited content')
        
        # Prevent XSS
        if any(char in v for char in '<>"\'&'):
            raise ValueError('Search query contains prohibited characters')
        
        return v.strip()

# Usage in FastAPI
from fastapi import HTTPException

@app.post("/users")
async def create_user(user_data: SecureUserInput):
    try:
        # Validation happens automatically
        user = await user_service.create_user(user_data)
        return {"user_id": user.id}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### SQL Injection Prevention

**SQLAlchemy Security Patterns:**
```python
# src/infrastructure/database/repositories/secure_repository.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

class SecureRepository:
    """Repository with SQL injection prevention."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def safe_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute parameterized query safely."""
        
        # Always use parameterized queries
        if params:
            result = await self.session.execute(text(query), params)
        else:
            result = await self.session.execute(text(query))
        
        return [dict(row) for row in result.mappings()]
    
    async def search_customers_safely(
        self, 
        search_term: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Safe customer search with parameterized query."""
        
        # ✅ Good - Parameterized query
        query = """
            SELECT id, first_name, last_name, email, created_at
            FROM customers 
            WHERE 
                (first_name ILIKE :search_term 
                OR last_name ILIKE :search_term 
                OR email ILIKE :search_term)
                AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params = {
            'search_term': f'%{search_term}%',
            'limit': limit,
            'offset': offset,
        }
        
        return await self.safe_query(query, params)
    
    # ❌ Bad - Never do this (SQL injection vulnerable)
    async def unsafe_search(self, search_term: str):
        """Example of what NOT to do."""
        # This is vulnerable to SQL injection
        query = f"SELECT * FROM customers WHERE name = '{search_term}'"
        # DON'T DO THIS!

# SQLAlchemy ORM patterns (inherently safe)
class CustomerRepositoryImpl:
    """SQLAlchemy ORM repository (safe by default)."""
    
    async def get_customers_by_status(
        self, 
        status: str, 
        limit: int = 20
    ) -> List[Customer]:
        """ORM queries are automatically parameterized."""
        
        result = await self.session.execute(
            select(CustomerModel)
            .where(CustomerModel.status == status)  # Automatically parameterized
            .limit(limit)
        )
        
        return [model.to_domain() for model in result.scalars().all()]
```

## Data Security

### Encryption at Rest

**RDS Encryption Configuration:**
```yaml
# CloudFormation/Terraform
Resources:
  PostgreSQLDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: '15.4'
      DBInstanceIdentifier: clean-py-db
      DBInstanceClass: db.t3.micro
      AllocatedStorage: 20
      StorageType: gp3
      StorageEncrypted: true
      KmsKeyId: !Ref DatabaseKMSKey
      BackupRetentionPeriod: 7
      DeletionProtection: true
      MultiAZ: true
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup
      MasterUsername: !Ref DatabaseUsername
      ManageMasterUserPassword: true  # AWS managed master password
      
  DatabaseKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: KMS key for database encryption
      KeyPolicy:
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Sid: Allow RDS access
            Effect: Allow
            Principal:
              Service: rds.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: '*'
```

### Encryption in Transit

**Application-Level TLS Configuration:**
```python
# src/infrastructure/security/tls_config.py

import ssl
from typing import Optional
import asyncpg

class TLSConfig:
    """TLS configuration for secure connections."""
    
    @staticmethod
    def create_ssl_context(
        verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED,
        ca_file: Optional[str] = None
    ) -> ssl.SSLContext:
        """Create secure SSL context."""
        
        context = ssl.create_default_context()
        context.verify_mode = verify_mode
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Disable weak ciphers
        context.set_ciphers(
            'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
        )
        
        if ca_file:
            context.load_verify_locations(ca_file)
        
        return context
    
    @staticmethod
    async def create_secure_db_connection(
        host: str,
        port: int,
        database: str, 
        user: str,
        password: str
    ) -> asyncpg.Connection:
        """Create secure database connection with TLS."""
        
        ssl_context = TLSConfig.create_ssl_context()
        
        return await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=ssl_context,
            server_settings={
                'application_name': 'clean-py-api',
                'sslmode': 'require',
            }
        )

# FastAPI TLS configuration
from fastapi import FastAPI
import uvicorn

app = FastAPI()

if __name__ == "__main__":
    # Production TLS configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="path/to/private.key",
        ssl_certfile="path/to/certificate.crt",
        ssl_version=ssl.PROTOCOL_TLSv1_2,
        ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    )
```

### Data Classification and Handling

**PII Protection Patterns:**
```python
# src/domain/value_objects/sensitive_data.py

from typing import Optional
import hashlib
import hmac
from cryptography.fernet import Fernet

class SensitiveString:
    """Value object for sensitive string data."""
    
    def __init__(self, value: str, encryption_key: bytes = None):
        self._encrypted_value = None
        self._hash = None
        
        if encryption_key:
            cipher = Fernet(encryption_key)
            self._encrypted_value = cipher.encrypt(value.encode())
        else:
            # Store hash for comparison without storing actual value
            self._hash = hashlib.sha256(value.encode()).hexdigest()
    
    def decrypt(self, encryption_key: bytes) -> str:
        """Decrypt and return the actual value."""
        if not self._encrypted_value:
            raise ValueError("Value was not encrypted")
        
        cipher = Fernet(encryption_key)
        return cipher.decrypt(self._encrypted_value).decode()
    
    def verify(self, value: str) -> bool:
        """Verify value matches without revealing actual value."""
        if self._hash:
            return self._hash == hashlib.sha256(value.encode()).hexdigest()
        return False
    
    def masked_display(self, visible_chars: int = 4) -> str:
        """Return masked version for display."""
        if self._encrypted_value:
            return f"****{str(self._encrypted_value)[-visible_chars:]}"
        return "****[HASHED]"

class PIIField:
    """Personal Identifiable Information field wrapper."""
    
    def __init__(self, value: str, field_type: str):
        self.field_type = field_type
        self.value = SensitiveString(value, self._get_encryption_key())
        self.created_at = datetime.utcnow()
    
    def _get_encryption_key(self) -> bytes:
        """Get field-specific encryption key."""
        # In production, get from AWS Secrets Manager
        key_name = f"pii-encryption-key-{self.field_type}"
        # return aws_secrets_manager.get_secret(key_name)
        return Fernet.generate_key()  # Example only
    
    def for_logging(self) -> Dict[str, Any]:
        """Return safe version for logging."""
        return {
            "field_type": self.field_type,
            "masked_value": self.value.masked_display(),
            "created_at": self.created_at.isoformat(),
        }

# Usage in domain entities
class Customer:
    def __init__(
        self, 
        customer_id: CustomerId,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None
    ):
        self.id = customer_id
        self.email = PIIField(email, "email")  # Encrypted PII
        self.first_name = PIIField(first_name, "name")
        self.last_name = PIIField(last_name, "name") 
        self.phone = PIIField(phone, "phone") if phone else None
    
    def safe_for_logging(self) -> Dict[str, Any]:
        """Return customer data safe for logging."""
        return {
            "customer_id": str(self.id),
            "email": self.email.for_logging(),
            "first_name": self.first_name.for_logging(),
            "last_name": self.last_name.for_logging(),
            "phone": self.phone.for_logging() if self.phone else None,
        }
```

## Network Security

### VPC Security Configuration

**Network Architecture:**
```yaml
# CloudFormation template for secure VPC
AWSTemplateFormatVersion: '2010-09-09'
Description: Secure VPC for Clean Architecture application

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-clean-py-vpc'

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-clean-py-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Public Subnets (for ALB)
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-1'

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-2'

  # Private Subnets (for ECS/Lambda)
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.11.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-1'

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.12.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-2'

  # Database Subnets (isolated)
  DatabaseSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.21.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-database-subnet-1'

  DatabaseSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.22.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-database-subnet-2'

  # NAT Gateway for private subnet internet access
  NATGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NATGatewayEIP.AllocationId
      SubnetId: !Ref PublicSubnet1
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-nat-gateway'

  NATGatewayEIP:
    Type: AWS::EC2::EIP
    DependsOn: AttachGateway
    Properties:
      Domain: vpc

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-rt'

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-rt'

  PrivateRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NATGateway

  DatabaseRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-database-rt'
  # Note: Database subnets have no internet route (completely isolated)

  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: HTTPS from internet
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
          Description: HTTP from internet (redirect to HTTPS)
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-alb-sg'

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref ALBSecurityGroup
          Description: HTTP from ALB
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-ecs-sg'

  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS database
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref ECSSecurityGroup
          Description: PostgreSQL from ECS
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-database-sg'
```

### WAF Configuration

**AWS WAF Rules:**
```json
{
  "WebACL": {
    "Name": "clean-py-web-acl",
    "Scope": "REGIONAL",
    "DefaultAction": {
      "Allow": {}
    },
    "Rules": [
      {
        "Name": "AWSManagedRulesCommonRuleSet",
        "Priority": 1,
        "OverrideAction": {
          "None": {}
        },
        "Statement": {
          "ManagedRuleGroupStatement": {
            "VendorName": "AWS",
            "Name": "AWSManagedRulesCommonRuleSet"
          }
        }
      },
      {
        "Name": "AWSManagedRulesKnownBadInputsRuleSet",
        "Priority": 2,
        "OverrideAction": {
          "None": {}
        },
        "Statement": {
          "ManagedRuleGroupStatement": {
            "VendorName": "AWS",
            "Name": "AWSManagedRulesKnownBadInputsRuleSet"
          }
        }
      },
      {
        "Name": "RateLimitRule",
        "Priority": 3,
        "Action": {
          "Block": {}
        },
        "Statement": {
          "RateBasedStatement": {
            "Limit": 2000,
            "AggregateKeyType": "IP"
          }
        }
      },
      {
        "Name": "GeoBlockRule",
        "Priority": 4,
        "Action": {
          "Block": {}
        },
        "Statement": {
          "GeoMatchStatement": {
            "CountryCodes": ["CN", "RU", "KP"]
          }
        }
      }
    ]
  }
}
```

## Identity and Access Management

### IAM Role Patterns

**Principle of Least Privilege:**
```json
{
  "ECSTaskRole": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "SecretsManagerAccess",
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": [
          "arn:aws:secretsmanager:region:account:secret:production/database/*",
          "arn:aws:secretsmanager:region:account:secret:production/jwt/*"
        ]
      },
      {
        "Sid": "ParameterStoreAccess", 
        "Effect": "Allow",
        "Action": [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ],
        "Resource": [
          "arn:aws:ssm:region:account:parameter/production/*"
        ]
      },
      {
        "Sid": "CloudWatchLogs",
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": [
          "arn:aws:logs:region:account:log-group:/aws/ecs/clean-py:*"
        ]
      },
      {
        "Sid": "KMSDecrypt",
        "Effect": "Allow",
        "Action": [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ],
        "Resource": [
          "arn:aws:kms:region:account:key/key-id"
        ],
        "Condition": {
          "StringEquals": {
            "kms:ViaService": [
              "secretsmanager.region.amazonaws.com",
              "ssm.region.amazonaws.com"
            ]
          }
        }
      }
    ]
  }
}
```

### Cross-Account Access Patterns

**Multi-Account Security:**
```json
{
  "CrossAccountRole": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AssumeRoleForDeployment",
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::DEPLOYMENT-ACCOUNT:role/DeploymentRole"
        },
        "Action": "sts:AssumeRole",
        "Condition": {
          "StringEquals": {
            "sts:ExternalId": "unique-external-id"
          },
          "IpAddress": {
            "aws:SourceIp": ["203.0.113.0/24"]
          }
        }
      }
    ]
  }
}
```

This comprehensive security documentation provides a solid foundation for implementing security in AWS-deployed Clean Architecture applications, covering all major security domains from infrastructure to application-level security controls.