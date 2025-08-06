# Lambda-Compatible Routing Pattern

## Overview
Design route handlers that work seamlessly with both FastAPI (ECS deployment) and AWS Lambda Powertools (serverless deployment), enabling deployment flexibility without changing business logic.

## Core Principle
Separate handler logic from framework-specific decorators, allowing the same business logic to be wrapped by either FastAPI or Lambda Powertools.

## Implementation Pattern

### 1. Pure Handler Functions
```python
# presentation/handlers/product_handlers.py
from typing import Dict, Any
from uuid import UUID

from application.use_cases.create_product import CreateProductUseCase, CreateProductCommand
from presentation.schemas.product_schemas import CreateProductRequest, ProductResponse
from presentation.dependencies import get_dependencies

async def create_product_handler(
    body: Dict[str, Any],
    dependencies: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Pure handler function that works with both FastAPI and Lambda
    
    Args:
        body: Request body as dictionary
        dependencies: Injected dependencies (repos, use cases)
    
    Returns:
        Response as dictionary
    """
    # Parse and validate request
    request = CreateProductRequest(**body)
    
    # Get dependencies
    deps = dependencies or get_dependencies()
    use_case: CreateProductUseCase = deps['create_product_use_case']
    
    # Execute business logic
    command = CreateProductCommand(
        mnemonic=request.mnemonic,
        overview=request.overview,
        is_confidential=request.is_confidential,
        initial_version_label=request.initial_version_label,
        initial_version_description=request.initial_version_description,
        start_date=request.start_date
    )
    
    try:
        product = await use_case.execute(command)
        response = ProductResponse.from_domain(product)
        return {
            "statusCode": 201,
            "body": response.dict()
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": {"error": str(e)}
        }

async def get_product_handler(
    path_parameters: Dict[str, Any],
    dependencies: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Get product by ID handler"""
    product_id = UUID(path_parameters['product_id'])
    
    deps = dependencies or get_dependencies()
    product_repo = deps['product_repository']
    
    product = await product_repo.find_by_id(product_id)
    if not product:
        return {
            "statusCode": 404,
            "body": {"error": "Product not found"}
        }
    
    response = ProductResponse.from_domain(product)
    return {
        "statusCode": 200,
        "body": response.dict()
    }
```

### 2. FastAPI Wrapper (ECS Deployment)
```python
# presentation/api/v1/product_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from presentation.handlers.product_handlers import (
    create_product_handler,
    get_product_handler
)
from presentation.schemas.product_schemas import CreateProductRequest, ProductResponse
from presentation.dependencies import get_fastapi_dependencies

router = APIRouter(prefix="/api/v1/product", tags=["product"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest,
    dependencies: Dict[str, Any] = Depends(get_fastapi_dependencies)
):
    """FastAPI route wrapper"""
    result = await create_product_handler(
        body=request.dict(),
        dependencies=dependencies
    )
    
    if result["statusCode"] != 201:
        raise HTTPException(
            status_code=result["statusCode"],
            detail=result["body"]
        )
    
    return result["body"]

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    dependencies: Dict[str, Any] = Depends(get_fastapi_dependencies)
):
    """FastAPI route wrapper"""
    result = await get_product_handler(
        path_parameters={"product_id": str(product_id)},
        dependencies=dependencies
    )
    
    if result["statusCode"] != 200:
        raise HTTPException(
            status_code=result["statusCode"],
            detail=result["body"]
        )
    
    return result["body"]
```

### 3. Lambda Powertools Wrapper (Serverless Deployment)
```python
# presentation/lambda/app.py
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from presentation.handlers.product_handlers import (
    create_product_handler,
    get_product_handler
)
from presentation.dependencies import get_lambda_dependencies

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Initialize dependencies once (Lambda container reuse)
dependencies = None

@app.post("/api/v1/product")
@tracer.capture_method
async def create_product():
    """Lambda Powertools route wrapper"""
    global dependencies
    if not dependencies:
        dependencies = await get_lambda_dependencies()
    
    body = app.current_event.json_body
    result = await create_product_handler(body, dependencies)
    
    return result["body"], result["statusCode"]

@app.get("/api/v1/product/<product_id>")
@tracer.capture_method
async def get_product(product_id: str):
    """Lambda Powertools route wrapper"""
    global dependencies
    if not dependencies:
        dependencies = await get_lambda_dependencies()
    
    result = await get_product_handler(
        path_parameters={"product_id": product_id},
        dependencies=dependencies
    )
    
    return result["body"], result["statusCode"]

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Lambda entry point"""
    return app.resolve(event, context)
```

### 4. Dependency Injection Strategy
```python
# presentation/dependencies.py
from typing import Dict, Any
import os

from infrastructure.database.connection import (
    get_ecs_session_factory,
    get_lambda_session
)

def get_dependencies() -> Dict[str, Any]:
    """Get dependencies based on runtime environment"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return get_lambda_dependencies()
    else:
        return get_fastapi_dependencies()

async def get_lambda_dependencies() -> Dict[str, Any]:
    """Lambda-specific dependencies (single connection)"""
    session = await get_lambda_session()
    
    # Create repositories
    product_repo = PostgresProductRepository(session)
    validation_repo = PostgresBusinessRuleRepository(session)
    
    # Create services
    catalog_service = CatalogProcessingService(product_repo, validation_repo)
    
    # Create use cases
    create_product_uc = CreateProductUseCase(product_repo)
    
    return {
        "product_repository": product_repo,
        "validation_repository": validation_repo,
        "catalog_service": catalog_service,
        "create_product_use_case": create_product_uc,
        "db_session": session
    }

async def get_fastapi_dependencies() -> Dict[str, Any]:
    """FastAPI dependencies (connection pool)"""
    session_factory = get_ecs_session_factory()
    async with session_factory() as session:
        # Similar setup but with pooled connections
        # ...
        return dependencies
```

### 5. Database Connection Management
```python
# infrastructure/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# Lambda: Single connection (no pool)
lambda_engine = None
lambda_session = None

async def get_lambda_session() -> AsyncSession:
    """Get or create Lambda database session"""
    global lambda_engine, lambda_session
    
    if not lambda_engine:
        lambda_engine = create_async_engine(
            os.getenv("DATABASE_URL"),
            pool_pre_ping=True,
            pool_size=1,  # Single connection for Lambda
            max_overflow=0
        )
    
    if not lambda_session:
        lambda_session = AsyncSession(lambda_engine)
    
    return lambda_session

# ECS: Connection pool
def get_ecs_session_factory() -> async_sessionmaker:
    """Get ECS session factory with connection pool"""
    engine = create_async_engine(
        os.getenv("DATABASE_URL"),
        pool_pre_ping=True,
        pool_size=20,  # Connection pool for ECS
        max_overflow=10
    )
    
    return async_sessionmaker(engine, expire_on_commit=False)
```

## Testing Strategy

### 1. Handler Unit Tests
```python
# tests/unit/handlers/test_product_handlers.py
import pytest
from unittest.mock import AsyncMock

from presentation.handlers.product_handlers import create_product_handler

@pytest.mark.asyncio
async def test_create_product_handler():
    """Test handler logic independent of framework"""
    # Mock dependencies
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = Product(...)
    
    dependencies = {
        "create_product_use_case": mock_use_case
    }
    
    # Test handler
    body = {
        "mnemonic": "TEST",
        "overview": "Test product",
        "is_confidential": False,
        "initial_version_label": "v1",
        "initial_version_description": "Initial",
        "start_date": "2024-01-01"
    }
    
    result = await create_product_handler(body, dependencies)
    
    assert result["statusCode"] == 201
    assert "id" in result["body"]
```

### 2. Framework Integration Tests
```python
# tests/integration/test_fastapi_routes.py
from fastapi.testclient import TestClient

def test_fastapi_create_product(client: TestClient, mock_dependencies):
    """Test FastAPI wrapper"""
    response = client.post(
        "/api/v1/product",
        json={...}
    )
    assert response.status_code == 201

# tests/integration/test_lambda_routes.py
from aws_lambda_powertools.utilities.testing import make_event

def test_lambda_create_product(lambda_handler, mock_dependencies):
    """Test Lambda wrapper"""
    event = make_event(
        method="POST",
        path="/api/v1/product",
        body={...}
    )
    
    result = lambda_handler(event, {})
    assert result["statusCode"] == 201
```

## Deployment Configuration

### 1. FastAPI Dockerfile (ECS)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# FastAPI with uvicorn
CMD ["uvicorn", "presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Lambda Dockerfile
```dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

# Lambda handler
CMD ["presentation.lambda.app.lambda_handler"]
```

### 3. Shared Requirements
```txt
# requirements.txt
# Core dependencies (both deployments)
sqlalchemy>=2.0
asyncpg
pydantic>=2.0
python-dateutil

# FastAPI dependencies
fastapi>=0.100.0
uvicorn[standard]

# Lambda dependencies  
aws-lambda-powertools[all]>=2.20.0

# Development
pytest>=7.0
pytest-asyncio
```

## Migration Guide

### From FastAPI to Lambda
1. Deploy same container with different CMD
2. Change environment variables for Lambda context
3. Route handlers remain unchanged
4. Monitor cold starts and adjust memory/timeout

### From Lambda to FastAPI
1. Deploy to ECS with FastAPI CMD
2. Configure ALB and target groups
3. Same business logic, better connection pooling
4. Scale based on CPU/memory metrics

## Best Practices

1. **Keep handlers pure**: No framework-specific code in handlers
2. **Consistent response format**: Always return statusCode + body
3. **Dependency injection**: Different strategies for Lambda vs ECS
4. **Connection management**: Single connection for Lambda, pool for ECS
5. **Error handling**: Consistent error format across deployments
6. **Logging**: Use appropriate logger for each platform

---
*Document Version: 1.0*
*Last Updated: 2025-08-01*
*Status: Lambda Compatibility Guide*