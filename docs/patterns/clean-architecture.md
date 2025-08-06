# Clean Architecture - E-commerce Demo Platform

## Overview
This document details the architecture patterns and design decisions for the e-commerce demo platform, emphasizing Domain-Driven Design (DDD) and Clean Architecture principles with PostgreSQL hybrid storage.

## Core Architecture Principles

### 1. Domain-Driven Design (DDD)
The domain model captures the essential business concepts and rules of e-commerce operations, independent of technical implementation details.

### 2. Clean Architecture
Dependencies flow inward: Infrastructure → Application → Domain. The domain layer remains pure with no external dependencies.

### 3. Repository Pattern
Abstracts data persistence behind interfaces, allowing infrastructure flexibility.

### 4. Dependency Injection
Loose coupling through interface-based dependencies injected at runtime.

## Domain Model Design

### Core Aggregates

#### Product Aggregate (Aggregate Root)
```python
# domain/entities/product.py
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from uuid import UUID

from domain.value_objects import DateRange, ProductCode, ProductVersion

@dataclass(frozen=True)
class Product:
    """Product aggregate root - demonstrates complex domain modeling with versions"""
    id: UUID
    sku: ProductCode
    overview: str
    is_confidential: bool
    versions: List[ProductVersion]
    created_at: date
    updated_at: date
    
    def get_version_for_date(self, target_date: date) -> Optional[ProductVersion]:
        """Get the product version applicable for a given date"""
        for version in self.versions:
            if version.date_range.contains(target_date):
                return version
        return None
    
    def add_version(self, version: ProductVersion) -> 'Product':
        """Add a new version ensuring no date overlaps"""
        # Business logic to validate no overlapping date ranges
        self._validate_no_overlap(version)
        new_versions = self.versions + [version]
        return Product(
            id=self.id,
            mnemonic=self.mnemonic,
            overview=self.overview,
            is_confidential=self.is_confidential,
            versions=new_versions,
            created_at=self.created_at,
            updated_at=date.today()
        )
```

#### ProductField Entity
```python
# domain/entities/item.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

class FieldType(Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    COMPUTED = "COMPUTED"
    REFERENCE = "REFERENCE"
    DESCRIPTIVE = "DESCRIPTIVE"

@dataclass(frozen=True)
class ProductField:
    """ProductField entity - represents a data field within a product version"""
    id: UUID
    name: str
    label: str
    description: str
    field_type: FieldType
    is_confidential: bool
    data_type: str
    is_nullable: bool
    product_version_id: UUID
    
    def is_computed(self) -> bool:
        return self.field_type == FieldType.COMPUTED
    
    def is_required(self) -> bool:
        return self.field_type == FieldType.REQUIRED
```

#### BusinessRule Entity
```python
# domain/entities/business_rule.py
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional
from uuid import UUID

from domain.value_objects import DateRange

@dataclass(frozen=True)
class BusinessRuleTemplate:
    """Reusable validation rule template"""
    id: UUID
    name: str
    description: str
    execution_type: str  # e.g., "great_expectations", "custom"
    parameter_schema: Dict[str, Any]  # JSON schema for parameters

@dataclass(frozen=True)
class BusinessRuleInstance:
    """Applied validation rule with specific parameters"""
    id: UUID
    template_id: UUID
    product_id: UUID
    date_range: DateRange
    parameters: Dict[str, Any]
    is_active: bool
    
    def applies_to_date(self, target_date: date) -> bool:
        """Check if this validation applies to a given date"""
        return self.is_active and self.date_range.contains(target_date)
```

### Value Objects

#### DateRange
```python
# domain/value_objects/date_range.py
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass(frozen=True)
class DateRange:
    """Value object representing a date range"""
    start_date: date
    end_date: Optional[date] = None
    
    def __post_init__(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must be before or equal to end date")
    
    def contains(self, target_date: date) -> bool:
        """Check if a date falls within this range"""
        if target_date < self.start_date:
            return False
        if self.end_date and target_date > self.end_date:
            return False
        return True
    
    def overlaps_with(self, other: 'DateRange') -> bool:
        """Check if two date ranges overlap"""
        # Implementation of overlap logic
        pass
```

#### ProductVersion
```python
# domain/value_objects/product_version.py
from dataclasses import dataclass
from typing import List
from uuid import UUID

from domain.value_objects import DateRange
from domain.entities.product_field import ProductField

@dataclass(frozen=True)
class ProductVersion:
    """Value object representing a version of a product"""
    id: UUID
    version_label: str
    version_caption: str
    description: str
    date_range: DateRange
    items: List[ProductField]
    
    def has_field(self, item_name: str) -> bool:
        """Check if this version contains a specific field"""
        return any(item.name == item_name for item in self.items)
```

### Repository Interfaces

#### Product Repository
```python
# domain/repositories/product_repository.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from domain.entities.product import Product
from domain.value_objects import ProductCode

class ProductRepository(ABC):
    """Repository interface for Product aggregate"""
    
    @abstractmethod
    async def find_by_id(self, product_id: UUID) -> Optional[Product]:
        """Find a product by its ID"""
        pass
    
    @abstractmethod
    async def find_by_sku(self, sku: ProductCode) -> Optional[Product]:
        """Find a product by its mnemonic"""
        pass
    
    @abstractmethod
    async def save(self, product: Product) -> Product:
        """Save a product (create or update)"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Product]:
        """List all product"""
        pass
    
    @abstractmethod
    async def find_product_for_date(self, target_date: date) -> List[Product]:
        """Find all product that have versions applicable for a given date"""
        pass
```

#### Validation Repository
```python
# domain/repositories/validation_repository.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from domain.entities.validation_rule import BusinessRuleTemplate, BusinessRuleInstance

class BusinessRuleRepository(ABC):
    """Repository interface for validation rules"""
    
    @abstractmethod
    async def find_template_by_id(self, template_id: UUID) -> Optional[BusinessRuleTemplate]:
        """Find a validation template by ID"""
        pass
    
    @abstractmethod
    async def save_template(self, template: BusinessRuleTemplate) -> BusinessRuleTemplate:
        """Save a validation template"""
        pass
    
    @abstractmethod
    async def find_instances_for_product(
        self, 
        product_id: UUID, 
        target_date: date
    ) -> List[BusinessRuleInstance]:
        """Find all validation instances for a product on a given date"""
        pass
    
    @abstractmethod
    async def save_instance(self, instance: BusinessRuleInstance) -> BusinessRuleInstance:
        """Save a validation instance"""
        pass
```

### Domain Services

#### Catalog Processing Service
```python
# domain/services/catalog_processing_service.py
from datetime import date
from typing import List, Dict, Any
from uuid import UUID

from domain.entities.product import Product
from domain.entities.validation_rule import BusinessRuleInstance
from domain.repositories.product_repository import ProductRepository
from domain.repositories.validation_repository import BusinessRuleRepository

class CatalogProcessingService:
    """Domain service for catalog processing logic"""
    
    def __init__(
        self,
        product_repository: ProductRepository,
        validation_repository: BusinessRuleRepository
    ):
        self._product_repo = product_repository
        self._validation_repo = validation_repository
    
    async def get_processing_catalog(
        self, 
        product_id: UUID, 
        data_date: date
    ) -> Dict[str, Any]:
        """Get all catalog needed to process data for a specific date"""
        product = await self._product_repo.find_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        version = product.get_version_for_date(data_date)
        if not version:
            raise ValueError(f"No product version found for date {data_date}")
        
        validations = await self._validation_repo.find_instances_for_product(
            product_id, 
            data_date
        )
        
        return {
            "product": product,
            "version": version,
            "items": version.items,
            "validations": validations
        }
```

## Infrastructure Layer

### PostgreSQL Hybrid Implementation

#### Database Models
```python
# infrastructure/database/models.py
from sqlalchemy import Column, String, Boolean, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ProductModel(Base):
    __tablename__ = "product"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    mnemonic = Column(String(50), unique=True, nullable=False, index=True)
    overview = Column(String(500))
    is_confidential = Column(Boolean, default=False)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=False)
    
    # Relationships
    versions = relationship("ProductVersionModel", back_populates="product")

class ProductVersionModel(Base):
    __tablename__ = "product_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"), nullable=False)
    version_label = Column(String(50), nullable=False)
    version_caption = Column(String(200))
    description = Column(String(500))
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, index=True)
    
    # Relationships
    product = relationship("ProductModel", back_populates="versions")
    items = relationship("ProductFieldModel", back_populates="product_version")

class ProductFieldModel(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    product_version_id = Column(UUID(as_uuid=True), ForeignKey("product_versions.id"))
    name = Column(String(100), nullable=False, index=True)
    label = Column(String(200))
    description = Column(String(500))
    item_class = Column(String(20), nullable=False)
    is_confidential = Column(Boolean, default=False)
    data_type = Column(String(50))
    is_nullable = Column(Boolean, default=True)
    
    # JSONB for flexible catalog
    extended_properties = Column(JSONB, default={})
    
    # Relationships
    product_version = relationship("ProductVersionModel", back_populates="items")

class BusinessRuleTemplateModel(Base):
    __tablename__ = "validation_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    execution_type = Column(String(50), nullable=False)
    
    # JSONB for flexible parameter schema
    parameter_schema = Column(JSONB, nullable=False)

class BusinessRuleInstanceModel(Base):
    __tablename__ = "validation_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("validation_templates.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"))
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, index=True)
    is_active = Column(Boolean, default=True)
    
    # JSONB for flexible parameters
    parameters = Column(JSONB, nullable=False)
    
    # Relationships
    template = relationship("BusinessRuleTemplateModel")
    product = relationship("ProductModel")
```

#### Repository Implementations
```python
# infrastructure/database/repositories/product_repository_impl.py
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from domain.entities.product import Product
from domain.repositories.product_repository import ProductRepository
from infrastructure.database.models import ProductModel, ProductVersionModel
from infrastructure.database.mappers import ProductMapper

class PostgresProductRepository(ProductRepository):
    """PostgreSQL implementation of ProductRepository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = ProductMapper()
    
    async def find_by_id(self, product_id: UUID) -> Optional[Product]:
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        result = await self._session.execute(stmt)
        product_model = result.scalar_one_or_none()
        
        if not product_model:
            return None
        
        return self._mapper.model_to_entity(product_model)
    
    async def save(self, product: Product) -> Product:
        product_model = self._mapper.entity_to_model(product)
        self._session.add(product_model)
        await self._session.commit()
        return product
    
    async def find_product_for_date(self, target_date: date) -> List[Product]:
        stmt = (
            select(ProductModel)
            .join(ProductVersionModel)
            .where(
                and_(
                    ProductVersionModel.start_date <= target_date,
                    (ProductVersionModel.end_date.is_(None)) | 
                    (ProductVersionModel.end_date >= target_date)
                )
            )
            .distinct()
        )
        result = await self._session.execute(stmt)
        product_models = result.scalars().all()
        
        return [self._mapper.model_to_entity(model) for model in product_models]
```

## Application Layer

### Use Cases

#### Create Product Use Case
```python
# application/use_cases/create_product.py
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID, uuid4

from domain.entities.product import Product
from domain.value_objects import ProductCode
from domain.repositories.product_repository import ProductRepository

@dataclass
class CreateProductCommand:
    """Command for creating a new product"""
    mnemonic: str
    overview: str
    is_confidential: bool
    initial_version_label: str
    initial_version_description: str
    start_date: date

class CreateProductUseCase:
    """Use case for creating a new product"""
    
    def __init__(self, product_repository: ProductRepository):
        self._product_repo = product_repository
    
    async def execute(self, command: CreateProductCommand) -> Product:
        # Check if product with mnemonic already exists
        existing = await self._product_repo.find_by_sku(
            ProductCode(command.mnemonic)
        )
        if existing:
            raise ValueError(f"Product with mnemonic {command.mnemonic} already exists")
        
        # Create new product with initial version
        product = Product(
            id=uuid4(),
            mnemonic=ProductCode(command.mnemonic),
            overview=command.overview,
            is_confidential=command.is_confidential,
            versions=[],  # Will add initial version
            created_at=date.today(),
            updated_at=date.today()
        )
        
        # Save product
        return await self._product_repo.save(product)
```

#### Process Data Use Case
```python
# application/use_cases/process_data.py
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, List
from uuid import UUID

from domain.services.catalog_processing_service import CatalogProcessingService

@dataclass
class ProcessDataCommand:
    """Command for processing data"""
    product_id: UUID
    data_date: date
    data_rows: List[Dict[str, Any]]

class ProcessDataUseCase:
    """Use case for processing data with catalog rules"""
    
    def __init__(self, catalog_service: CatalogProcessingService):
        self._catalog_service = catalog_service
    
    async def execute(self, command: ProcessDataCommand) -> Dict[str, Any]:
        # Get processing catalog for the date
        catalog = await self._catalog_service.get_processing_catalog(
            command.product_id,
            command.data_date
        )
        
        # Process data rows according to catalog
        results = {
            "processed_count": 0,
            "validation_errors": [],
            "derived_values": []
        }
        
        for row in command.data_rows:
            # Apply validations
            # Calculate derivations
            # Store results
            results["processed_count"] += 1
        
        return results
```

## Presentation Layer

### FastAPI Application

#### API Models
```python
# presentation/schemas/product_schemas.py
from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

class CreateProductRequest(BaseModel):
    mnemonic: str = Field(..., min_length=1, max_length=50)
    overview: str = Field(..., max_length=500)
    is_confidential: bool = False
    initial_version_label: str = Field(..., min_length=1)
    initial_version_description: str
    start_date: date
    
    @validator('mnemonic')
    def validate_mnemonic(cls, v: str) -> str:
        # Validate mnemonic format
        if not v.isalnum():
            raise ValueError("Mnemonic must be alphanumeric")
        return v.upper()

class ProductResponse(BaseModel):
    id: UUID
    mnemonic: str
    overview: str
    is_confidential: bool
    version_count: int
    created_at: date
    updated_at: date
    
    class Config:
        orm_mode = True

class ItemResponse(BaseModel):
    id: UUID
    name: str
    label: str
    description: str
    item_class: str
    is_confidential: bool
    data_type: str
    is_nullable: bool
```

#### API Routes
```python
# presentation/api/v1/product_routes.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.create_product import CreateProductUseCase, CreateProductCommand
from presentation.schemas.product_schemas import CreateProductRequest, ProductResponse
from presentation.dependencies import get_create_product_use_case

router = APIRouter(prefix="/api/v1/product", tags=["product"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest,
    use_case: CreateProductUseCase = Depends(get_create_product_use_case)
) -> ProductResponse:
    """Create a new product with initial version"""
    try:
        command = CreateProductCommand(
            mnemonic=request.mnemonic,
            overview=request.overview,
            is_confidential=request.is_confidential,
            initial_version_label=request.initial_version_label,
            initial_version_description=request.initial_version_description,
            start_date=request.start_date
        )
        product = await use_case.execute(command)
        
        return ProductResponse(
            id=product.id,
            mnemonic=product.mnemonic.value,
            overview=product.overview,
            is_confidential=product.is_confidential,
            version_count=len(product.versions),
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    product_repo: ProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """Get product by ID"""
    product = await product_repo.find_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        id=product.id,
        mnemonic=product.mnemonic.value,
        overview=product.overview,
        is_confidential=product.is_confidential,
        version_count=len(product.versions),
        created_at=product.created_at,
        updated_at=product.updated_at
    )
```

### Dependency Injection

```python
# presentation/dependencies.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import Depends

from domain.repositories.product_repository import ProductRepository
from domain.repositories.validation_repository import BusinessRuleRepository
from infrastructure.database.repositories.product_repository_impl import PostgresProductRepository
from infrastructure.database.repositories.validation_repository_impl import PostgresBusinessRuleRepository
from domain.services.catalog_processing_service import CatalogProcessingService
from application.use_cases.create_product import CreateProductUseCase

# Database setup
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/catalog_db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Repositories
async def get_product_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ProductRepository:
    return PostgresProductRepository(session)

async def get_validation_repository(
    session: AsyncSession = Depends(get_db_session)
) -> BusinessRuleRepository:
    return PostgresBusinessRuleRepository(session)

# Domain services
async def get_catalog_processing_service(
    product_repo: ProductRepository = Depends(get_product_repository),
    validation_repo: BusinessRuleRepository = Depends(get_validation_repository)
) -> CatalogProcessingService:
    return CatalogProcessingService(product_repo, validation_repo)

# Use cases
async def get_create_product_use_case(
    product_repo: ProductRepository = Depends(get_product_repository)
) -> CreateProductUseCase:
    return CreateProductUseCase(product_repo)
```

## Testing Strategy

### Domain Layer Tests
```python
# tests/domain/entities/test_product.py
import pytest
from datetime import date
from uuid import uuid4

from domain.entities.product import Product
from domain.value_objects import ProductCode, DateRange, ProductVersion

def test_product_get_version_for_date():
    """Test getting correct version for a given date"""
    product = Product(
        id=uuid4(),
        mnemonic=ProductCode("TEST"),
        overview="Test product",
        is_confidential=False,
        versions=[
            ProductVersion(
                id=uuid4(),
                version_label="v1",
                version_caption="Version 1",
                description="Initial version",
                date_range=DateRange(
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 6, 30)
                ),
                items=[]
            ),
            ProductVersion(
                id=uuid4(),
                version_label="v2",
                version_caption="Version 2",
                description="Updated version",
                date_range=DateRange(
                    start_date=date(2024, 7, 1),
                    end_date=None
                ),
                items=[]
            )
        ],
        created_at=date.today(),
        updated_at=date.today()
    )
    
    # Test version 1 date
    v1 = product.get_version_for_date(date(2024, 3, 15))
    assert v1 is not None
    assert v1.version_label == "v1"
    
    # Test version 2 date
    v2 = product.get_version_for_date(date(2024, 8, 1))
    assert v2 is not None
    assert v2.version_label == "v2"
    
    # Test date before any version
    v_none = product.get_version_for_date(date(2023, 12, 1))
    assert v_none is None
```

### Repository Tests with Mocks
```python
# tests/application/use_cases/test_create_product.py
import pytest
from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

from application.use_cases.create_product import CreateProductUseCase, CreateProductCommand
from domain.entities.product import Product
from domain.value_objects import ProductCode

@pytest.mark.asyncio
async def test_create_product_success():
    """Test successful product creation"""
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.find_by_sku.return_value = None  # No existing product
    mock_repo.save.side_effect = lambda s: s  # Return saved product
    
    # Create use case
    use_case = CreateProductUseCase(mock_repo)
    
    # Execute command
    command = CreateProductCommand(
        mnemonic="TEST",
        overview="Test product",
        is_confidential=False,
        initial_version_label="v1",
        initial_version_description="Initial version",
        start_date=date.today()
    )
    
    result = await use_case.execute(command)
    
    # Assertions
    assert result.mnemonic.value == "TEST"
    assert result.overview == "Test product"
    mock_repo.find_by_sku.assert_called_once()
    mock_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_product_duplicate_mnemonic():
    """Test product creation with duplicate mnemonic"""
    # Mock repository with existing product
    mock_repo = AsyncMock()
    existing_product = Product(
        id=uuid4(),
        mnemonic=ProductCode("TEST"),
        overview="Existing product",
        is_confidential=False,
        versions=[],
        created_at=date.today(),
        updated_at=date.today()
    )
    mock_repo.find_by_sku.return_value = existing_product
    
    # Create use case
    use_case = CreateProductUseCase(mock_repo)
    
    # Execute command and expect error
    command = CreateProductCommand(
        mnemonic="TEST",
        overview="New product",
        is_confidential=False,
        initial_version_label="v1",
        initial_version_description="Initial version",
        start_date=date.today()
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(command)
```

## Migration Strategy

### From Demo to Production

1. **Database Migration Path**
   - Demo: Local PostgreSQL with simple schema
   - Production: Amazon RDS PostgreSQL with replication
   - Alternative: DynamoDB migration if needed (repository pattern enables this)

2. **Code Organization Evolution**
   - Start with single module per layer
   - Split into feature modules as complexity grows
   - Maintain clean architecture boundaries

3. **Testing Evolution**
   - Demo: Unit tests with mocks
   - Integration: Add database integration tests
   - Production: Add performance and load tests

## Key Benefits of This Architecture

1. **Testability**: Business logic isolated from infrastructure
2. **Flexibility**: Easy to change database technology
3. **Maintainability**: Clear separation of concerns
4. **Type Safety**: Full type hints throughout
5. **Domain Focus**: Business rules in pure Python
6. **PostgreSQL Hybrid**: Structured + flexible data in one database

---
*Document Version: 1.0*
*Last Updated: 2025-08-06*
*Status: Clean Architecture Guide*