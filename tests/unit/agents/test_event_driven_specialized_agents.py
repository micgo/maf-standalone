#!/usr/bin/env python3
"""
Tests for event-driven specialized agents
"""
import os
import json
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock, call

from multi_agent_framework.agents.event_driven_frontend_agent import EventDrivenFrontendAgent
from multi_agent_framework.agents.event_driven_backend_agent import EventDrivenBackendAgent
from multi_agent_framework.agents.event_driven_db_agent import EventDrivenDatabaseAgent
from multi_agent_framework.agents.event_driven_devops_agent import EventDrivenDevOpsAgent
from multi_agent_framework.agents.event_driven_qa_agent import EventDrivenQAAgent
from multi_agent_framework.agents.event_driven_docs_agent import EventDrivenDocsAgent
from multi_agent_framework.agents.event_driven_security_agent import EventDrivenSecurityAgent
from multi_agent_framework.agents.event_driven_ux_ui_agent import EventDrivenUXUIAgent
from multi_agent_framework.core.event_bus_interface import EventType


class TestEventDrivenSpecializedAgentsBase(TestCase):
    """Base test class with common setup for event-driven agents"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_event_specialized'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Mock event bus
        self.mock_event_bus = Mock()
        self.published_events = []
        
        def capture_publish(event):
            self.published_events.append(event)
        
        self.mock_event_bus.publish.side_effect = capture_publish
        self.mock_event_bus.subscribe = Mock()
        self.mock_event_bus.start = Mock()
        self.mock_event_bus.stop = Mock()
        
        # Mock event bus factory
        self.event_bus_patcher = patch('multi_agent_framework.core.event_bus_factory.get_event_bus')
        self.mock_get_event_bus = self.event_bus_patcher.start()
        self.mock_get_event_bus.return_value = self.mock_event_bus
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Mock message bus
        self.message_bus_patcher = patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
        self.mock_message_bus_class = self.message_bus_patcher.start()
        self.mock_message_bus = Mock()
        self.mock_message_bus_class.return_value = self.mock_message_bus
        self.mock_message_bus.receive_messages.return_value = []
        
    def tearDown(self):
        """Clean up"""
        self.event_bus_patcher.stop()
        self.llm_patcher.stop()
        self.message_bus_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def get_event_handler(self, event_type):
        """Helper to get the handler for a specific event type"""
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == event_type:
                return call[0][1]
        return None


class TestEventDrivenFrontendAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenFrontendAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven frontend agent initialization"""
        agent = EventDrivenFrontendAgent()
        
        self.assertEqual(agent.name, "frontend_agent")
        
        # Check event subscriptions
        expected_events = [EventType.TASK_CREATED]
        subscribed_events = [call[0][0] for call in self.mock_event_bus.subscribe.call_args_list]
        for event in expected_events:
            self.assertIn(event, subscribed_events)
    
    def test_handle_ui_task_event(self):
        """Test handling UI component task via event"""
        agent = EventDrivenFrontendAgent()
        
        # Mock LLM response
        self.mock_llm.generate_content.return_value.text = '''
```tsx
export const Header: React.FC = () => {
    return (
        <header className="bg-blue-600 p-4">
            <h1 className="text-white text-2xl">My App</h1>
        </header>
    );
};
```
'''
        
        # Create task event
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'ui-task-1',
            'assigned_agent': 'frontend_agent',
            'description': 'Create header component',
            'feature_id': 'feat-ui-1'
        }
        
        # Get handler and process event
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        # Check completion event published
        completion_events = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED]
        self.assertEqual(len(completion_events), 1)
        self.assertEqual(completion_events[0]['task_id'], 'ui-task-1')
        self.assertIn('header', completion_events[0]['result'].lower())
    
    def test_responsive_design_task(self):
        """Test handling responsive design requirements"""
        agent = EventDrivenFrontendAgent()
        
        # Mock responsive component
        self.mock_llm.generate_content.return_value.text = '''
```tsx
export const ResponsiveCard: React.FC = () => {
    return (
        <div className="w-full md:w-1/2 lg:w-1/3 p-4">
            <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-2">Card Title</h3>
                <p className="text-gray-600">Card content goes here</p>
            </div>
        </div>
    );
};
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'responsive-1',
            'assigned_agent': 'frontend_agent',
            'description': 'Create responsive card component with mobile, tablet, and desktop layouts'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        # Verify responsive classes in output
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('md:', completion['result'])
        self.assertIn('lg:', completion['result'])


class TestEventDrivenBackendAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenBackendAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven backend agent initialization"""
        agent = EventDrivenBackendAgent()
        
        self.assertEqual(agent.name, "backend_agent")
    
    def test_handle_api_task_event(self):
        """Test handling API endpoint task via event"""
        agent = EventDrivenBackendAgent()
        
        # Mock API implementation
        self.mock_llm.generate_content.return_value.text = '''
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Product(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool

@app.get("/api/products", response_model=List[Product])
async def get_products():
    """Get all products"""
    products = [
        Product(id=1, name="Laptop", price=999.99, in_stock=True),
        Product(id=2, name="Mouse", price=29.99, in_stock=True)
    ]
    return products

@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Get specific product by ID"""
    if product_id == 1:
        return Product(id=1, name="Laptop", price=999.99, in_stock=True)
    raise HTTPException(status_code=404, detail="Product not found")
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'api-task-1',
            'assigned_agent': 'backend_agent',
            'description': 'Create product catalog API with FastAPI'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        # Check API was implemented
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('product', completion['result'].lower())
        self.assertIn('api', completion['result'].lower())
    
    def test_authentication_middleware(self):
        """Test implementing authentication middleware"""
        agent = EventDrivenBackendAgent()
        
        # Mock auth implementation
        self.mock_llm.generate_content.return_value.text = '''
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/protected")
async def protected_route(user=Depends(verify_token)):
    """Protected endpoint requiring authentication"""
    return {"message": "Access granted", "user_id": user.get("sub")}
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'auth-task-1',
            'assigned_agent': 'backend_agent',
            'description': 'Implement JWT authentication middleware'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('auth', completion['result'].lower())
        self.assertIn('token', completion['result'].lower())


class TestEventDrivenDatabaseAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenDatabaseAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven DB agent initialization"""
        agent = EventDrivenDatabaseAgent()
        
        self.assertEqual(agent.name, "db_agent")
    
    def test_handle_schema_design_event(self):
        """Test handling database schema design via event"""
        agent = EventDrivenDatabaseAgent()
        
        # Mock schema design
        self.mock_llm.generate_content.return_value.text = '''
```sql
-- E-commerce database schema

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table  
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    sku VARCHAR(50) UNIQUE NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- Create indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'db-design-1',
            'assigned_agent': 'db_agent',
            'description': 'Design e-commerce database schema with products, orders, and categories'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('schema', completion['result'].lower())
        self.assertIn('products', completion['result'].lower())
    
    def test_migration_script(self):
        """Test creating database migration scripts"""
        agent = EventDrivenDatabaseAgent()
        
        # Mock migration
        self.mock_llm.generate_content.return_value.text = '''
```python
# migrations/001_add_user_roles.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add roles and permissions tables"""
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Add role_id to users table
    op.add_column('users', sa.Column('role_id', sa.Integer()))
    op.create_foreign_key(
        'fk_users_role',
        'users', 'roles',
        ['role_id'], ['id']
    )
    
    # Create default roles
    op.execute("INSERT INTO roles (name, description) VALUES ('admin', 'Administrator role')")
    op.execute("INSERT INTO roles (name, description) VALUES ('user', 'Regular user role')")

def downgrade():
    """Remove roles and permissions"""
    op.drop_constraint('fk_users_role', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_table('roles')
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'migration-1',
            'assigned_agent': 'db_agent',
            'description': 'Create migration to add user roles and permissions'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('migration', completion['result'].lower())
        self.assertIn('roles', completion['result'].lower())


class TestEventDrivenDevOpsAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenDevOpsAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven DevOps agent initialization"""
        agent = EventDrivenDevOpsAgent()
        
        self.assertEqual(agent.name, "devops_agent")
    
    def test_handle_cicd_task_event(self):
        """Test handling CI/CD pipeline task via event"""
        agent = EventDrivenDevOpsAgent()
        
        # Mock CI/CD pipeline
        self.mock_llm.generate_content.return_value.text = '''
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
      - run: npm run lint

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: build-artifacts
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: build-artifacts
      - name: Deploy to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 sync dist/ s3://${{ secrets.S3_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DISTRIBUTION }} --paths "/*"
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'cicd-task-1',
            'assigned_agent': 'devops_agent',
            'description': 'Setup GitHub Actions CI/CD pipeline for deployment'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('deploy', completion['result'].lower())
        self.assertIn('github', completion['result'].lower())
    
    def test_kubernetes_deployment(self):
        """Test creating Kubernetes deployment configs"""
        agent = EventDrivenDevOpsAgent()
        
        # Mock K8s config
        self.mock_llm.generate_content.return_value.text = '''
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myregistry/myapp:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 3000
  type: LoadBalancer
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'k8s-task-1',
            'assigned_agent': 'devops_agent',
            'description': 'Create Kubernetes deployment configuration'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('kubernetes', completion['result'].lower())


class TestEventDrivenQAAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenQAAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven QA agent initialization"""
        agent = EventDrivenQAAgent()
        
        self.assertEqual(agent.name, "qa_agent")
    
    def test_handle_test_creation_event(self):
        """Test handling test creation task via event"""
        agent = EventDrivenQAAgent()
        
        # Mock test suite
        self.mock_llm.generate_content.return_value.text = '''
```python
# test_user_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.models.user import User

class TestUserService:
    
    @pytest.fixture
    def user_service(self):
        """Create user service with mocked dependencies"""
        mock_db = Mock()
        mock_cache = Mock()
        return UserService(db=mock_db, cache=mock_cache)
    
    def test_create_user_success(self, user_service):
        """Test successful user creation"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123"
        }
        
        user_service.db.users.find_one.return_value = None  # No existing user
        
        # Act
        result = user_service.create_user(user_data)
        
        # Assert
        assert result.email == user_data["email"]
        assert result.username == user_data["username"]
        assert result.password != user_data["password"]  # Should be hashed
        user_service.db.users.insert_one.assert_called_once()
    
    def test_create_user_duplicate_email(self, user_service):
        """Test user creation with duplicate email"""
        # Arrange
        existing_user = {"email": "test@example.com"}
        user_service.db.users.find_one.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user({
                "email": "test@example.com",
                "username": "newuser"
            })
    
    def test_get_user_by_id_cached(self, user_service):
        """Test getting user from cache"""
        # Arrange
        user_id = "123"
        cached_user = User(id=user_id, email="cached@example.com")
        user_service.cache.get.return_value = cached_user
        
        # Act
        result = user_service.get_user_by_id(user_id)
        
        # Assert
        assert result == cached_user
        user_service.db.users.find_one.assert_not_called()
    
    @patch('app.services.user_service.send_welcome_email')
    def test_user_registration_flow(self, mock_send_email, user_service):
        """Test complete user registration flow"""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        }
        
        user_service.db.users.find_one.return_value = None
        
        # Act
        user = user_service.register_user(user_data)
        
        # Assert
        assert user.is_active is False  # Should be inactive until email verified
        mock_send_email.assert_called_once_with(user.email)
        user_service.cache.set.assert_called()  # Should cache the user
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'qa-task-1',
            'assigned_agent': 'qa_agent',
            'description': 'Write comprehensive unit tests for UserService'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('test', completion['result'].lower())
        self.assertIn('assert', completion['result'])
    
    def test_integration_test_creation(self):
        """Test creating integration tests"""
        agent = EventDrivenQAAgent()
        
        # Mock integration test
        self.mock_llm.generate_content.return_value.text = '''
```javascript
// e2e/checkout.spec.js
describe('E-commerce Checkout Flow', () => {
    beforeEach(() => {
        cy.visit('/');
        cy.login('testuser@example.com', 'password123');
    });

    it('should complete full checkout process', () => {
        // Add product to cart
        cy.get('[data-testid="product-card"]').first().click();
        cy.get('[data-testid="add-to-cart"]').click();
        cy.get('[data-testid="cart-count"]').should('contain', '1');
        
        // Go to checkout
        cy.get('[data-testid="cart-icon"]').click();
        cy.get('[data-testid="checkout-button"]').click();
        
        // Fill shipping info
        cy.get('#shipping-address').type('123 Test St');
        cy.get('#city').type('Test City');
        cy.get('#zip').type('12345');
        
        // Payment info
        cy.get('#card-number').type('4242424242424242');
        cy.get('#expiry').type('12/25');
        cy.get('#cvv').type('123');
        
        // Complete order
        cy.get('[data-testid="place-order"]').click();
        
        // Verify success
        cy.url().should('include', '/order-confirmation');
        cy.get('.confirmation-message').should('contain', 'Order successful');
    });
    
    it('should handle payment errors gracefully', () => {
        // Setup cart
        cy.addProductToCart('test-product-1');
        cy.visit('/checkout');
        
        // Use invalid card
        cy.fillCheckoutForm({
            cardNumber: '4000000000000002' // Card that triggers decline
        });
        
        cy.get('[data-testid="place-order"]').click();
        
        // Verify error handling
        cy.get('.error-message').should('be.visible');
        cy.get('.error-message').should('contain', 'Payment declined');
    });
});
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'e2e-task-1',
            'assigned_agent': 'qa_agent',
            'description': 'Create end-to-end tests for checkout flow'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('checkout', completion['result'].lower())
        self.assertIn('e2e', completion['result'].lower())


class TestEventDrivenDocsAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenDocsAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven docs agent initialization"""
        agent = EventDrivenDocsAgent()
        
        self.assertEqual(agent.name, "docs_agent")
    
    def test_handle_api_docs_event(self):
        """Test handling API documentation task via event"""
        agent = EventDrivenDocsAgent()
        
        # Mock API docs
        self.mock_llm.generate_content.return_value.text = '''
# Authentication API Documentation

## Overview
This API provides secure authentication and authorization for the application using JWT tokens.

## Base URL
```
https://api.example.com/v1
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "username": "johndoe",
    "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "created_at": "2024-01-14T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Email or username already exists

### POST /auth/login
Authenticate user and receive access token.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Response:** Same as login response

### GET /auth/me
Get current user information (requires authentication).

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "roles": ["user"],
    "created_at": "2024-01-14T10:30:00Z"
}
```

## Rate Limiting
- 5 requests per minute for registration/login endpoints
- 60 requests per minute for authenticated endpoints

## Security Notes
- Passwords must be at least 8 characters with uppercase, lowercase, number, and special character
- Tokens expire after 1 hour
- Refresh tokens expire after 30 days
- All endpoints use HTTPS
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'docs-task-1',
            'assigned_agent': 'docs_agent',
            'description': 'Create comprehensive API documentation for authentication endpoints'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('authentication', completion['result'].lower())
        self.assertIn('api', completion['result'].lower())
    
    def test_readme_generation(self):
        """Test generating project README"""
        agent = EventDrivenDocsAgent()
        
        # Mock README
        self.mock_llm.generate_content.return_value.text = '''
# MyApp - Modern E-commerce Platform

[![Build Status](https://img.shields.io/github/workflow/status/myorg/myapp/CI)](https://github.com/myorg/myapp/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview
MyApp is a modern, scalable e-commerce platform built with React, Node.js, and PostgreSQL.

## Features
- 🛒 Shopping cart with persistent storage
- 💳 Secure payment processing with Stripe
- 📦 Real-time order tracking
- 🔍 Advanced product search and filtering
- 📱 Mobile-responsive design
- 🔐 JWT-based authentication

## Quick Start

### Prerequisites
- Node.js 18+
- PostgreSQL 14+
- Redis (for caching)

### Installation
```bash
# Clone the repository
git clone https://github.com/myorg/myapp.git
cd myapp

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
npm run migrate

# Start development server
npm run dev
```

### Running Tests
```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

## Architecture
```
myapp/
├── frontend/          # React frontend
├── backend/           # Node.js API
├── database/          # SQL migrations and seeds
├── tests/             # Test suites
└── docs/              # Documentation
```

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'readme-task-1',
            'assigned_agent': 'docs_agent',
            'description': 'Generate comprehensive README for the project'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('readme', completion['result'].lower())


class TestEventDrivenSecurityAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenSecurityAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven security agent initialization"""
        agent = EventDrivenSecurityAgent()
        
        self.assertEqual(agent.name, "security_agent")
    
    def test_handle_security_audit_event(self):
        """Test handling security audit task via event"""
        agent = EventDrivenSecurityAgent()
        
        # Mock security audit
        self.mock_llm.generate_content.return_value.text = '''
# Security Audit Report

## Executive Summary
Conducted security audit of authentication system. Found 2 critical, 3 medium, and 5 low severity issues.

## Critical Issues

### 1. SQL Injection Vulnerability
**Location:** `/api/users/search`
**Issue:** User input directly concatenated into SQL query

**Vulnerable Code:**
```javascript
// INSECURE - DO NOT USE
const query = `SELECT * FROM users WHERE name LIKE '%${searchTerm}%'`;
```

**Fix:**
```javascript
// SECURE - Use parameterized queries
const query = 'SELECT * FROM users WHERE name LIKE ?';
const params = [`%${searchTerm}%`];
db.query(query, params);
```

### 2. Missing Rate Limiting
**Location:** `/api/auth/login`
**Issue:** No rate limiting on login attempts enables brute force attacks

**Fix:**
```javascript
import rateLimit from 'express-rate-limit';

const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // 5 attempts
    message: 'Too many login attempts, please try again later'
});

app.post('/api/auth/login', loginLimiter, loginHandler);
```

## Medium Issues

### 3. Weak Password Policy
**Current:** No password requirements
**Recommendation:** Implement strong password validation
```javascript
const passwordSchema = {
    minLength: 12,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true
};
```

### 4. Missing Security Headers
**Fix:** Add security middleware
```javascript
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
}));
```

## Recommendations
1. Implement input validation on all endpoints
2. Use prepared statements for all database queries
3. Enable audit logging for sensitive operations
4. Implement proper session management
5. Regular dependency updates and vulnerability scanning
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'security-audit-1',
            'assigned_agent': 'security_agent',
            'description': 'Perform security audit of authentication system'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('security', completion['result'].lower())
        self.assertIn('vulnerability', completion['result'].lower())
    
    def test_implement_security_feature(self):
        """Test implementing security features"""
        agent = EventDrivenSecurityAgent()
        
        # Mock security implementation
        self.mock_llm.generate_content.return_value.text = '''
```python
# security/csrf_protection.py
import secrets
from functools import wraps
from flask import session, request, abort

class CSRFProtection:
    """CSRF protection middleware for Flask applications"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.generate_csrf_token)
        app.jinja_env.globals['csrf_token'] = self.get_csrf_token
    
    def generate_csrf_token(self):
        """Generate CSRF token for session"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
    
    def get_csrf_token(self):
        """Get current CSRF token"""
        return session.get('csrf_token', '')
    
    def validate_csrf(self, f):
        """Decorator to validate CSRF token"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.form.get('csrf_token') or \
                        request.headers.get('X-CSRF-Token')
                
                if not token or token != session.get('csrf_token'):
                    abort(403, 'CSRF token validation failed')
            
            return f(*args, **kwargs)
        return decorated_function

# Usage example
csrf = CSRFProtection()

@app.route('/api/users', methods=['POST'])
@csrf.validate_csrf
def create_user():
    """Create user endpoint with CSRF protection"""
    # Implementation here
    pass
```
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'csrf-task-1',
            'assigned_agent': 'security_agent',
            'description': 'Implement CSRF protection middleware'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('csrf', completion['result'].lower())


class TestEventDrivenUXUIAgent(TestEventDrivenSpecializedAgentsBase):
    """Test EventDrivenUXUIAgent functionality"""
    
    def test_initialization(self):
        """Test event-driven UX/UI agent initialization"""
        agent = EventDrivenUXUIAgent()
        
        self.assertEqual(agent.name, "ux_ui_agent")
    
    def test_handle_design_system_event(self):
        """Test handling design system creation via event"""
        agent = EventDrivenUXUIAgent()
        
        # Mock design system
        self.mock_llm.generate_content.return_value.text = '''
# Design System Documentation

## Color System

### Brand Colors
```scss
$primary-blue: #0066CC;
$primary-blue-light: #3385D6;
$primary-blue-dark: #0052A3;

$secondary-green: #00AA55;
$secondary-green-light: #33BB77;
$secondary-green-dark: #008844;

$accent-orange: #FF6600;
$accent-purple: #6633CC;
```

### Semantic Colors
```scss
$success: #00AA55;
$warning: #FFB800;
$error: #DC3545;
$info: #17A2B8;

$text-primary: #212529;
$text-secondary: #6C757D;
$text-muted: #ADB5BD;

$background-primary: #FFFFFF;
$background-secondary: #F8F9FA;
$background-tertiary: #E9ECEF;
```

## Typography

### Font Stack
```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
             "Helvetica Neue", Arial, sans-serif;
--font-mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace;
```

### Type Scale
```scss
$font-size-xs: 0.75rem;    // 12px
$font-size-sm: 0.875rem;   // 14px
$font-size-base: 1rem;     // 16px
$font-size-lg: 1.125rem;   // 18px
$font-size-xl: 1.25rem;    // 20px
$font-size-2xl: 1.5rem;    // 24px
$font-size-3xl: 1.875rem;  // 30px
$font-size-4xl: 2.25rem;   // 36px
```

## Spacing System
Using 8px base unit for consistent spacing:
```scss
$space-1: 0.25rem;  // 4px
$space-2: 0.5rem;   // 8px
$space-3: 0.75rem;  // 12px
$space-4: 1rem;     // 16px
$space-5: 1.5rem;   // 24px
$space-6: 2rem;     // 32px
$space-8: 3rem;     // 48px
$space-10: 4rem;    // 64px
```

## Component Library

### Button Variants
```tsx
// Primary Button
<Button variant="primary" size="medium">
  Click me
</Button>

// Button styles
.btn-primary {
  background: var(--primary-blue);
  color: white;
  padding: var(--space-3) var(--space-5);
  border-radius: 6px;
  font-weight: 500;
  transition: all 150ms ease;
  
  &:hover {
    background: var(--primary-blue-dark);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2);
  }
  
  &:active {
    transform: translateY(0);
  }
}
```

### Form Components
```tsx
// Input field with floating label
<div className="form-field">
  <input 
    type="email" 
    id="email" 
    className="form-input" 
    placeholder=" "
  />
  <label htmlFor="email" className="form-label">
    Email address
  </label>
</div>
```

## Accessibility Guidelines
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- All interactive elements must have focus states
- Use semantic HTML elements
- Provide alt text for all images
- Support keyboard navigation
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'design-system-1',
            'assigned_agent': 'ux_ui_agent',
            'description': 'Create comprehensive design system with colors, typography, and components'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('design', completion['result'].lower())
        self.assertIn('color', completion['result'].lower())
    
    def test_wireframe_creation(self):
        """Test creating wireframes and mockups"""
        agent = EventDrivenUXUIAgent()
        
        # Mock wireframe description
        self.mock_llm.generate_content.return_value.text = '''
# Dashboard Wireframe Specification

## Layout Structure
```
+----------------------------------------------------------+
|  Header                                                  |
|  +----------------------------------------------------+  |
|  | Logo | Navigation (Dashboard|Products|Orders|User) |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|  Sidebar (200px)    |  Main Content Area               |
|  +----------------+ |  +-----------------------------+ |
|  | Quick Stats    | |  | Page Title & Actions        | |
|  | - Total Sales  | |  | Dashboard     [Export] [⚙]  | |
|  | - Orders       | |  +-----------------------------+ |
|  | - Customers    | |                                   |
|  |                | |  +-----------------------------+ |
|  | Navigation     | |  | Metrics Cards (Grid 4-col)  | |
|  | - Overview     | |  | +-------+ +-------+ +-----+ | |
|  | - Analytics    | |  | |Revenue| |Orders | |Users| | |
|  | - Products     | |  | |$125k  | | 1,234 | | 456 | | |
|  | - Inventory    | |  | |+12.5% | | +8.2% | |+15% | | |
|  | - Reports      | |  | +-------+ +-------+ +-----+ | |
|  +----------------+ |  +-----------------------------+ |
|                     |                                   |
|                     |  +-----------------------------+ |
|                     |  | Charts Section              | |
|                     |  | +----------+ +------------+ | |
|                     |  | |Sales     | |Top Products| | |
|                     |  | |Line Chart| |Bar Chart   | | |
|                     |  | +----------+ +------------+ | |
|                     |  +-----------------------------+ |
+----------------------------------------------------------+
```

## Interactive Elements

### Metric Cards
- Hover: Slight elevation and shadow
- Click: Opens detailed view modal
- Loading: Skeleton placeholder

### Charts
- Interactive tooltips on hover
- Click-and-drag to zoom
- Export options (PNG, CSV)

### Responsive Behavior
- Desktop (>1200px): Full layout as shown
- Tablet (768-1200px): Sidebar collapses to icons
- Mobile (<768px): 
  - Sidebar becomes bottom navigation
  - Cards stack vertically
  - Charts take full width
'''
        
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'wireframe-1',
            'assigned_agent': 'ux_ui_agent',
            'description': 'Create wireframe for admin dashboard'
        }
        
        handler = self.get_event_handler(EventType.TASK_CREATED)
        handler(task_event)
        
        completion = [e for e in self.published_events if e['type'] == EventType.TASK_COMPLETED][0]
        self.assertIn('wireframe', completion['result'].lower())
        self.assertIn('dashboard', completion['result'].lower())


if __name__ == '__main__':
    import unittest
    unittest.main()