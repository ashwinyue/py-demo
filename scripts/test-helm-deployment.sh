#!/bin/bash

# Test script for Helm deployment
# This script tests the updated Helm configuration for the Python MiniBlog microservices

set -e

echo "=== Testing Helm Deployment for Python MiniBlog ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    print_error "helm is not installed or not in PATH"
    exit 1
fi

# Set namespace
NAMESPACE="python-miniblog"
RELEASE_NAME="python-miniblog"
CHART_PATH="./helm/python-miniblog"

print_status "Using namespace: $NAMESPACE"
print_status "Using release name: $RELEASE_NAME"
print_status "Using chart path: $CHART_PATH"

# Create namespace if it doesn't exist
print_status "Creating namespace if it doesn't exist..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Validate Helm chart
print_status "Validating Helm chart..."
if helm lint $CHART_PATH; then
    print_status "Helm chart validation passed"
else
    print_error "Helm chart validation failed"
    exit 1
fi

# Dry run the deployment
print_status "Performing dry run deployment..."
if helm upgrade --install $RELEASE_NAME $CHART_PATH --namespace $NAMESPACE --dry-run; then
    print_status "Dry run deployment successful"
else
    print_error "Dry run deployment failed"
    exit 1
fi

# Ask user if they want to proceed with actual deployment
read -p "Do you want to proceed with actual deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled by user"
    exit 0
fi

# Deploy the application
print_status "Deploying application..."
if helm upgrade --install $RELEASE_NAME $CHART_PATH --namespace $NAMESPACE --wait --timeout=10m; then
    print_status "Deployment successful"
else
    print_error "Deployment failed"
    exit 1
fi

# Wait for pods to be ready
print_status "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=$RELEASE_NAME -n $NAMESPACE --timeout=300s

# Check deployment status
print_status "Checking deployment status..."
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

# Check services
print_status "Checking services..."
kubectl get svc -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

# Test database connectivity
print_status "Testing database connectivity..."
MYSQL_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=mysql -o jsonpath='{.items[0].metadata.name}')
if [ -n "$MYSQL_POD" ]; then
    kubectl exec -n $NAMESPACE $MYSQL_POD -- mysql -u miniblog -pminiblog123 -e "SHOW DATABASES;" | grep miniblog
    if [ $? -eq 0 ]; then
        print_status "Database connectivity test passed"
    else
        print_error "Database connectivity test failed"
    fi
else
    print_warning "MySQL pod not found"
fi

# Test Redis connectivity
print_status "Testing Redis connectivity..."
REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=redis -o jsonpath='{.items[0].metadata.name}')
if [ -n "$REDIS_POD" ]; then
    kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli ping
    if [ $? -eq 0 ]; then
        print_status "Redis connectivity test passed"
    else
        print_error "Redis connectivity test failed"
    fi
else
    print_warning "Redis pod not found"
fi

# Test service endpoints
print_status "Testing service endpoints..."

# Get Tyk Gateway service
TYK_SERVICE=$(kubectl get svc -n $NAMESPACE -l app.kubernetes.io/component=tyk-gateway -o jsonpath='{.items[0].metadata.name}')
if [ -n "$TYK_SERVICE" ]; then
    print_status "Tyk Gateway service found: $TYK_SERVICE"
    
    # Port forward to test locally
    print_status "Setting up port forwarding for testing..."
    kubectl port-forward -n $NAMESPACE svc/$TYK_SERVICE 8080:8080 &
    PORT_FORWARD_PID=$!
    
    # Wait a moment for port forwarding to establish
    sleep 5
    
    # Test Tyk Gateway health
    print_status "Testing Tyk Gateway health endpoint..."
    if curl -f http://localhost:8080/hello; then
        print_status "Tyk Gateway health check passed"
    else
        print_warning "Tyk Gateway health check failed"
    fi
    
    # Test user service through gateway
    print_status "Testing user service through gateway..."
    if curl -f http://localhost:8080/user-service/health; then
        print_status "User service test passed"
    else
        print_warning "User service test failed"
    fi
    
    # Test blog service through gateway
    print_status "Testing blog service through gateway..."
    if curl -f http://localhost:8080/blog-service/health; then
        print_status "Blog service test passed"
    else
        print_warning "Blog service test failed"
    fi
    
    # Clean up port forwarding
    kill $PORT_FORWARD_PID 2>/dev/null || true
else
    print_warning "Tyk Gateway service not found"
fi

print_status "=== Deployment Test Complete ==="
print_status "To access the application:"
print_status "1. Port forward: kubectl port-forward -n $NAMESPACE svc/$TYK_SERVICE 8080:8080"
print_status "2. Access user service: http://localhost:8080/user-service/"
print_status "3. Access blog service: http://localhost:8080/blog-service/"
print_status "4. Tyk Gateway health: http://localhost:8080/hello"

print_status "To clean up:"
print_status "helm uninstall $RELEASE_NAME -n $NAMESPACE"
print_status "kubectl delete namespace $NAMESPACE"