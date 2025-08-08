# Logging Examples and Usage Patterns

This document provides comprehensive examples of how to use the AWS-optimized logging infrastructure in various scenarios.

## Table of Contents

- [FastAPI Integration Examples](#fastapi-integration-examples)
- [Lambda Function Examples](#lambda-function-examples)
- [Domain Layer Logging](#domain-layer-logging)
- [Repository Pattern Logging](#repository-pattern-logging)
- [Error Handling Patterns](#error-handling-patterns)
- [Performance Monitoring](#performance-monitoring)
- [Business Event Logging](#business-event-logging)
- [Testing Examples](#testing-examples)

## FastAPI Integration Examples

### Complete Application Setup

```python
# src/presentation/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from src.infrastructure.logging import (
    configure_logging,
    LoggingMiddleware,
    CorrelationMiddleware,
    get_logger
)

# Configure logging at startup
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Clean Architecture Demo",
    version="1.0.0"
)

# Add middleware (order matters!)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    LoggingMiddleware,
    skip_paths={"/health", "/metrics"},  # Skip health checks
    log_request_body=False,  # Don't log request bodies in production
    sensitive_headers={"authorization", "x-api-key"},
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global exception handler with structured logging."""
    logger.error(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.on_event("startup")
async def startup_event():
    logger.info(
        "Application starting up",
        extra={
            "service": "clean-py",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "local"),
        }
    )

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")
    from src.infrastructure.logging.logger import shutdown_logging
    shutdown_logging()
```

### API Endpoint Examples

```python
# src/presentation/api/v1/customers.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from src.infrastructure.logging import get_logger
from src.infrastructure.logging.decorators import log_execution, log_performance

router = APIRouter(prefix="/customers", tags=["customers"])
logger = get_logger(__name__)

@router.post("/", response_model=CustomerResponse)
@log_execution(log_args=False, log_result=False, log_performance=True)
async def create_customer(
    customer_data: CreateCustomerRequest,
    use_case: CreateCustomerUseCase = Depends(),
) -> CustomerResponse:
    """Create a new customer with comprehensive logging."""
    
    logger.info(
        "Customer creation requested",
        extra={
            "email_domain": customer_data.email.split("@")[1],
            "country": customer_data.address.country if customer_data.address else None,
            "source": "api_v1",
        }
    )
    
    try:
        customer = await use_case.execute(customer_data)
        
        logger.info(
            "Customer created successfully",
            extra={
                "customer_id": customer.id,
                "email_domain": customer.email.split("@")[1],
                "account_type": customer.account_type,
                "created_at": customer.created_at.isoformat(),
            }
        )
        
        return CustomerResponse.from_domain(customer)
        
    except DomainException as e:
        logger.warning(
            "Customer creation failed - business rule violation",
            extra={
                "error_code": e.error_code,
                "error_message": str(e),
                "email_domain": customer_data.email.split("@")[1],
            }
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(
            "Customer creation failed - unexpected error",
            extra={
                "error_type": type(e).__name__,
                "email_domain": customer_data.email.split("@")[1],
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{customer_id}", response_model=CustomerResponse)
@log_performance(threshold_ms=500)
async def get_customer(
    customer_id: str,
    repository: CustomerRepository = Depends(),
) -> CustomerResponse:
    """Get customer with performance monitoring."""
    
    logger.debug(
        "Customer lookup requested",
        extra={"customer_id": customer_id}
    )
    
    customer = await repository.get_by_id(customer_id)
    if not customer:
        logger.info(
            "Customer not found",
            extra={"customer_id": customer_id}
        )
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse.from_domain(customer)

@router.get("/", response_model=List[CustomerResponse])
async def search_customers(
    query: str = None,
    limit: int = 20,
    offset: int = 0,
    search_use_case: SearchCustomersUseCase = Depends(),
) -> List[CustomerResponse]:
    """Search customers with query logging."""
    
    search_context = {
        "query_length": len(query) if query else 0,
        "limit": limit,
        "offset": offset,
        "has_query": bool(query),
    }
    
    logger.info(
        "Customer search requested",
        extra=search_context
    )
    
    results = await search_use_case.execute(
        query=query,
        limit=limit,
        offset=offset
    )
    
    logger.info(
        "Customer search completed",
        extra={
            **search_context,
            "results_count": len(results),
            "more_available": len(results) == limit,
        }
    )
    
    return [CustomerResponse.from_domain(c) for c in results]
```

## Lambda Function Examples

### HTTP API Lambda

```python
# lambda/api_handler.py
import json
import time
from typing import Dict, Any
from src.infrastructure.logging.lambda_utils import (
    configure_lambda_logging,
    lambda_request_logger,
    lambda_response_logger,
    lambda_error_logger
)
from src.infrastructure.logging import get_logger

# Configure at module level
configure_lambda_logging(log_level="INFO")
logger = get_logger(__name__)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler with comprehensive logging."""
    start_time = time.perf_counter()
    
    # Log incoming request
    lambda_request_logger(event, context)
    
    try:
        # Extract request details
        http_method = event.get("httpMethod", "UNKNOWN")
        path = event.get("path", "/")
        query_params = event.get("queryStringParameters") or {}
        
        logger.info(
            f"Processing {http_method} request",
            extra={
                "path": path,
                "query_params": query_params,
                "user_agent": event.get("headers", {}).get("User-Agent"),
            }
        )
        
        # Route to appropriate handler
        if path == "/customers" and http_method == "GET":
            result = handle_get_customers(query_params)
        elif path.startswith("/customers/") and http_method == "GET":
            customer_id = path.split("/")[-1]
            result = handle_get_customer(customer_id)
        else:
            raise ValueError(f"Unknown path: {path}")
        
        # Build success response
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-ID": context.aws_request_id,
            },
            "body": json.dumps(result)
        }
        
        # Log successful response
        duration = (time.perf_counter() - start_time) * 1000
        lambda_response_logger(response, context, duration)
        
        return response
        
    except ValueError as e:
        # Handle client errors
        logger.warning(
            "Client error in Lambda request",
            extra={
                "error": str(e),
                "path": event.get("path"),
                "method": event.get("httpMethod"),
            }
        )
        
        response = {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
        return response
        
    except Exception as e:
        # Log and handle server errors
        lambda_error_logger(e, context, event)
        
        response = {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
        return response

def handle_get_customers(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Handle GET /customers with logging."""
    search_term = query_params.get("search", "")
    limit = int(query_params.get("limit", "20"))
    
    logger.info(
        "Searching customers",
        extra={
            "search_term_length": len(search_term),
            "limit": limit,
            "has_search": bool(search_term),
        }
    )
    
    # Simulate business logic
    customers = search_customers(search_term, limit)
    
    logger.info(
        "Customer search completed",
        extra={
            "results_count": len(customers),
            "search_term_length": len(search_term),
        }
    )
    
    return {
        "customers": customers,
        "total": len(customers),
        "search_term": search_term,
    }
```

### Event-Driven Lambda

```python
# lambda/event_processor.py
import json
from typing import Dict, Any, List
from src.infrastructure.logging.lambda_utils import configure_lambda_logging
from src.infrastructure.logging import get_logger

configure_lambda_logging()
logger = get_logger(__name__)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Process SQS events with detailed logging."""
    
    logger.info(
        "SQS event received",
        extra={
            "records_count": len(event.get("Records", [])),
            "function_name": context.function_name,
        }
    )
    
    processed_count = 0
    failed_count = 0
    batch_item_failures = []
    
    for record in event.get("Records", []):
        message_id = record.get("messageId")
        
        try:
            # Process individual message
            result = process_message(record, context)
            processed_count += 1
            
            logger.info(
                "Message processed successfully",
                extra={
                    "message_id": message_id,
                    "result_type": type(result).__name__,
                }
            )
            
        except Exception as e:
            failed_count += 1
            batch_item_failures.append({"itemIdentifier": message_id})
            
            logger.error(
                "Message processing failed",
                extra={
                    "message_id": message_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True
            )
    
    # Log batch summary
    logger.info(
        "Batch processing completed",
        extra={
            "total_records": len(event.get("Records", [])),
            "processed_count": processed_count,
            "failed_count": failed_count,
            "success_rate": processed_count / len(event.get("Records", [])) if event.get("Records") else 0,
        }
    )
    
    # Return partial batch failure info for SQS
    return {
        "batchItemFailures": batch_item_failures
    }

def process_message(record: Dict[str, Any], context) -> Any:
    """Process individual SQS message."""
    body = json.loads(record.get("body", "{}"))
    message_type = body.get("type", "unknown")
    
    logger.debug(
        "Processing message",
        extra={
            "message_type": message_type,
            "body_size": len(record.get("body", "")),
        }
    )
    
    if message_type == "customer_created":
        return process_customer_created(body)
    elif message_type == "order_completed":
        return process_order_completed(body)
    else:
        raise ValueError(f"Unknown message type: {message_type}")
```

## Domain Layer Logging

### Domain Entity Logging

```python
# src/domain/entities/customer.py
from src.infrastructure.logging import get_logger
from src.shared_kernel.base import AggregateRoot

logger = get_logger(__name__)

class Customer(AggregateRoot):
    """Customer aggregate with integrated logging."""
    
    def update_email(self, new_email: Email) -> None:
        """Update customer email with business rule validation."""
        old_email_domain = self.email.domain
        new_email_domain = new_email.domain
        
        logger.info(
            "Customer email update initiated",
            extra={
                "customer_id": str(self.id),
                "old_email_domain": old_email_domain,
                "new_email_domain": new_email_domain,
                "email_change": old_email_domain != new_email_domain,
            }
        )
        
        # Business rule: Can't change to same email
        if self.email == new_email:
            logger.warning(
                "Email update rejected - same email",
                extra={
                    "customer_id": str(self.id),
                    "email_domain": new_email_domain,
                }
            )
            raise DomainException("Email is already set to this value")
        
        # Business rule: Check for email format
        if not new_email.is_valid():
            logger.warning(
                "Email update rejected - invalid format",
                extra={
                    "customer_id": str(self.id),
                    "email_domain": new_email_domain,
                    "validation_error": "invalid_format",
                }
            )
            raise DomainException("Invalid email format")
        
        # Update email
        old_email = self.email
        self.email = new_email
        
        # Add domain event
        self.add_domain_event(CustomerEmailChangedEvent(
            customer_id=self.id,
            old_email=old_email,
            new_email=new_email
        ))
        
        logger.info(
            "Customer email updated successfully",
            extra={
                "customer_id": str(self.id),
                "old_email_domain": old_email_domain,
                "new_email_domain": new_email_domain,
            }
        )
    
    def place_order(self, order_data: Dict[str, Any]) -> 'Order':
        """Place order with comprehensive logging."""
        order_value = order_data.get("total_amount", 0)
        items_count = len(order_data.get("items", []))
        
        logger.info(
            "Order placement initiated",
            extra={
                "customer_id": str(self.id),
                "order_value": float(order_value),
                "items_count": items_count,
                "customer_tier": self.tier,
            }
        )
        
        # Business rules validation
        if not self.can_place_order():
            logger.warning(
                "Order placement rejected - customer restrictions",
                extra={
                    "customer_id": str(self.id),
                    "restriction_reason": self.get_restriction_reason(),
                    "order_value": float(order_value),
                }
            )
            raise DomainException(f"Customer cannot place order: {self.get_restriction_reason()}")
        
        # Apply customer tier discount
        discount = self.calculate_discount(order_value)
        if discount > 0:
            logger.info(
                "Customer discount applied",
                extra={
                    "customer_id": str(self.id),
                    "customer_tier": self.tier,
                    "original_amount": float(order_value),
                    "discount_amount": float(discount),
                    "discount_percentage": float(discount / order_value * 100),
                }
            )
        
        # Create order (this would typically call a factory)
        order = Order.create_for_customer(self, order_data)
        
        logger.info(
            "Order placed successfully",
            extra={
                "customer_id": str(self.id),
                "order_id": str(order.id),
                "final_amount": float(order.total_amount),
                "items_count": len(order.items),
            }
        )
        
        return order
```

### Domain Service Logging

```python
# src/domain/services/pricing_service.py
from decimal import Decimal
from typing import List, Dict, Any
from src.infrastructure.logging import get_logger
from src.infrastructure.logging.decorators import log_execution, log_performance

logger = get_logger(__name__)

class PricingService:
    """Domain service for pricing calculations with detailed logging."""
    
    @log_execution(log_args=False, log_result=False)
    @log_performance(threshold_ms=100)
    def calculate_order_total(
        self,
        items: List['OrderItem'],
        customer: 'Customer',
        promotions: List['Promotion'] = None
    ) -> Decimal:
        """Calculate order total with comprehensive logging."""
        
        base_total = sum(item.price * item.quantity for item in items)
        items_count = len(items)
        
        logger.info(
            "Order total calculation started",
            extra={
                "customer_id": str(customer.id),
                "items_count": items_count,
                "base_total": float(base_total),
                "customer_tier": customer.tier,
                "promotions_count": len(promotions) if promotions else 0,
            }
        )
        
        # Apply customer tier discount
        tier_discount = self._calculate_tier_discount(customer, base_total)
        if tier_discount > 0:
            logger.info(
                "Tier discount applied",
                extra={
                    "customer_id": str(customer.id),
                    "tier": customer.tier,
                    "discount_amount": float(tier_discount),
                    "discount_rate": float(tier_discount / base_total),
                }
            )
        
        # Apply promotions
        promotion_discount = Decimal(0)
        applied_promotions = []
        
        if promotions:
            for promotion in promotions:
                if promotion.is_applicable_to(customer, items):
                    discount = promotion.calculate_discount(base_total, items)
                    promotion_discount += discount
                    applied_promotions.append(promotion.id)
                    
                    logger.info(
                        "Promotion applied",
                        extra={
                            "customer_id": str(customer.id),
                            "promotion_id": str(promotion.id),
                            "promotion_type": promotion.type,
                            "discount_amount": float(discount),
                        }
                    )
        
        # Calculate final total
        final_total = base_total - tier_discount - promotion_discount
        
        # Log final calculation
        logger.info(
            "Order total calculation completed",
            extra={
                "customer_id": str(customer.id),
                "base_total": float(base_total),
                "tier_discount": float(tier_discount),
                "promotion_discount": float(promotion_discount),
                "final_total": float(final_total),
                "savings": float(tier_discount + promotion_discount),
                "savings_percentage": float((tier_discount + promotion_discount) / base_total * 100),
                "applied_promotions": applied_promotions,
            }
        )
        
        return final_total
    
    def _calculate_tier_discount(self, customer: 'Customer', amount: Decimal) -> Decimal:
        """Calculate customer tier discount."""
        discount_rates = {
            "bronze": Decimal("0.00"),
            "silver": Decimal("0.05"),
            "gold": Decimal("0.10"),
            "platinum": Decimal("0.15"),
        }
        
        rate = discount_rates.get(customer.tier, Decimal("0.00"))
        discount = amount * rate
        
        logger.debug(
            "Tier discount calculated",
            extra={
                "customer_tier": customer.tier,
                "discount_rate": float(rate),
                "amount": float(amount),
                "discount": float(discount),
            }
        )
        
        return discount
```

## Repository Pattern Logging

### Repository Implementation with Logging

```python
# src/infrastructure/database/repositories/customer_repository_impl.py
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.logging import get_logger
from src.infrastructure.logging.decorators import log_performance

logger = get_logger(__name__)

class CustomerRepositoryImpl(CustomerRepository):
    """Customer repository with comprehensive logging."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @log_performance(threshold_ms=100)
    async def save(self, customer: Customer) -> None:
        """Save customer with performance logging."""
        logger.info(
            "Customer save operation started",
            extra={
                "customer_id": str(customer.id),
                "is_new": customer.is_new,
                "has_changes": customer.has_changes(),
            }
        )
        
        try:
            if customer.is_new:
                # Insert new customer
                db_customer = CustomerModel.from_domain(customer)
                self.session.add(db_customer)
                
                logger.info(
                    "New customer inserted",
                    extra={
                        "customer_id": str(customer.id),
                        "email_domain": customer.email.domain,
                        "account_type": customer.account_type,
                    }
                )
            else:
                # Update existing customer
                updates = customer.get_changes()  # Assume this method exists
                if updates:
                    await self.session.execute(
                        update(CustomerModel)
                        .where(CustomerModel.id == customer.id)
                        .values(**updates)
                    )
                    
                    logger.info(
                        "Customer updated",
                        extra={
                            "customer_id": str(customer.id),
                            "updated_fields": list(updates.keys()),
                            "changes_count": len(updates),
                        }
                    )
            
            await self.session.flush()
            
        except Exception as e:
            logger.error(
                "Customer save failed",
                extra={
                    "customer_id": str(customer.id),
                    "error_type": type(e).__name__,
                    "is_new": customer.is_new,
                },
                exc_info=True
            )
            raise
    
    @log_performance(threshold_ms=50)
    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID with caching awareness."""
        logger.debug(
            "Customer lookup by ID",
            extra={"customer_id": customer_id}
        )
        
        try:
            result = await self.session.execute(
                select(CustomerModel).where(CustomerModel.id == customer_id)
            )
            db_customer = result.scalar_one_or_none()
            
            if db_customer:
                customer = db_customer.to_domain()
                logger.debug(
                    "Customer found",
                    extra={
                        "customer_id": customer_id,
                        "customer_tier": customer.tier,
                        "last_updated": customer.updated_at.isoformat(),
                    }
                )
                return customer
            else:
                logger.info(
                    "Customer not found",
                    extra={"customer_id": customer_id}
                )
                return None
                
        except Exception as e:
            logger.error(
                "Customer lookup failed",
                extra={
                    "customer_id": customer_id,
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise
    
    async def search(
        self,
        query: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Customer]:
        """Search customers with query performance logging."""
        search_context = {
            "query": query,
            "query_length": len(query) if query else 0,
            "limit": limit,
            "offset": offset,
        }
        
        logger.info(
            "Customer search started",
            extra=search_context
        )
        
        try:
            # Build query
            stmt = select(CustomerModel)
            if query:
                stmt = stmt.where(
                    CustomerModel.email.ilike(f"%{query}%") |
                    CustomerModel.first_name.ilike(f"%{query}%") |
                    CustomerModel.last_name.ilike(f"%{query}%")
                )
            
            stmt = stmt.offset(offset).limit(limit)
            
            # Execute query
            result = await self.session.execute(stmt)
            db_customers = result.scalars().all()
            
            # Convert to domain objects
            customers = [db_customer.to_domain() for db_customer in db_customers]
            
            logger.info(
                "Customer search completed",
                extra={
                    **search_context,
                    "results_count": len(customers),
                    "has_more": len(customers) == limit,
                }
            )
            
            return customers
            
        except Exception as e:
            logger.error(
                "Customer search failed",
                extra={
                    **search_context,
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise
```

## Error Handling Patterns

### Global Error Handler

```python
# src/presentation/error_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.infrastructure.logging import get_logger
from src.shared_kernel.exceptions import DomainException

logger = get_logger(__name__)

async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle domain exceptions with structured logging."""
    
    logger.warning(
        "Domain exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "error_code": exc.error_code,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None),
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "domain_error",
                "code": exc.error_code,
                "message": str(exc),
            }
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors with field details."""
    
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "Validation error occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "field_errors": field_errors,
            "errors_count": len(field_errors),
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": field_errors,
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with full context."""
    
    logger.error(
        "Unhandled exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
        },
        exc_info=True
    )
    
    # Don't expose internal errors in production
    if os.getenv("ENVIRONMENT") == "production":
        message = "Internal server error"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": message,
            }
        }
    )
```

### Circuit Breaker with Logging

```python
# src/infrastructure/resilience/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass
import time
from typing import Callable, Any
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    timeout_seconds: int = 60
    success_threshold: int = 2

class CircuitBreaker:
    """Circuit breaker with comprehensive logging."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
        logger.info(
            "Circuit breaker initialized",
            extra={
                "circuit_name": name,
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            }
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    "Circuit breaker attempting reset",
                    extra={
                        "circuit_name": self.name,
                        "time_since_failure": time.time() - self.last_failure_time,
                    }
                )
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                logger.warning(
                    "Circuit breaker is open - call rejected",
                    extra={
                        "circuit_name": self.name,
                        "failure_count": self.failure_count,
                        "time_until_retry": self.config.timeout_seconds - (time.time() - self.last_failure_time),
                    }
                )
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is open")
        
        try:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Success - reset failure count
            self.on_success(duration_ms)
            return result
            
        except Exception as e:
            self.on_failure(e)
            raise
    
    def on_success(self, duration_ms: float) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            logger.info(
                "Circuit breaker success in half-open state",
                extra={
                    "circuit_name": self.name,
                    "success_count": self.success_count,
                    "duration_ms": round(duration_ms, 2),
                }
            )
            
            if self.success_count >= self.config.success_threshold:
                logger.info(
                    "Circuit breaker reset to closed",
                    extra={
                        "circuit_name": self.name,
                        "success_count": self.success_count,
                    }
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset on any success
    
    def on_failure(self, exception: Exception) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            "Circuit breaker recorded failure",
            extra={
                "circuit_name": self.name,
                "failure_count": self.failure_count,
                "exception_type": type(exception).__name__,
                "error_message": str(exception),
            }
        )
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            
            logger.error(
                "Circuit breaker opened due to failures",
                extra={
                    "circuit_name": self.name,
                    "failure_count": self.failure_count,
                    "threshold": self.config.failure_threshold,
                    "timeout_seconds": self.config.timeout_seconds,
                }
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.config.timeout_seconds
        )
```

## Testing Examples

### Unit Test with Log Verification

```python
# tests/test_customer_service.py
import pytest
import logging
from unittest.mock import Mock
from src.domain.services.customer_service import CustomerService
from src.infrastructure.logging import get_logger

def test_customer_creation_logging(caplog):
    """Test that customer creation logs correctly."""
    
    # Arrange
    logger = get_logger("src.domain.services.customer_service")
    mock_repository = Mock()
    service = CustomerService(mock_repository)
    
    customer_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    
    # Act
    with caplog.at_level(logging.INFO):
        service.create_customer(customer_data)
    
    # Assert
    assert "Customer creation initiated" in caplog.text
    
    # Verify structured logging
    log_records = [r for r in caplog.records if r.levelno >= logging.INFO]
    assert len(log_records) >= 1
    
    creation_log = log_records[0]
    assert hasattr(creation_log, 'email_domain')
    assert creation_log.email_domain == "example.com"

def test_error_logging_on_failure(caplog):
    """Test error logging when customer creation fails."""
    
    # Arrange
    mock_repository = Mock()
    mock_repository.save.side_effect = Exception("Database error")
    
    service = CustomerService(mock_repository)
    
    # Act & Assert
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception):
            service.create_customer({"email": "test@example.com"})
    
    # Verify error was logged
    assert "Customer creation failed" in caplog.text
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) >= 1
    
    error_log = error_records[0]
    assert error_log.exc_info is not None  # Exception details included
```

### Integration Test with Log Analysis

```python
# tests/integration/test_api_logging.py
import pytest
from fastapi.testclient import TestClient
from src.presentation.main import app

def test_request_response_logging(caplog):
    """Test that HTTP requests are properly logged."""
    
    client = TestClient(app)
    
    with caplog.at_level(logging.INFO):
        response = client.get("/customers/123")
    
    # Find request logs
    request_logs = [
        r for r in caplog.records 
        if hasattr(r, 'event_type') and r.event_type == 'request_started'
    ]
    assert len(request_logs) == 1
    
    request_log = request_logs[0]
    assert request_log.method == "GET"
    assert request_log.path == "/customers/123"
    
    # Find response logs
    response_logs = [
        r for r in caplog.records 
        if hasattr(r, 'event_type') and r.event_type == 'request_completed'
    ]
    assert len(response_logs) == 1
    
    response_log = response_logs[0]
    assert hasattr(response_log, 'duration_ms')
    assert hasattr(response_log, 'status_code')
```

This comprehensive set of examples demonstrates how to effectively use the AWS-optimized logging infrastructure across all layers of your Clean Architecture application, from FastAPI endpoints to domain services and Lambda functions.