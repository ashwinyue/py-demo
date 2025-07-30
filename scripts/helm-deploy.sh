#!/bin/bash

# Helm deployment script for python-miniblog
# Usage: ./deploy.sh [environment] [action]
# Environment: development, testing, production
# Action: install, upgrade, uninstall, status

set -e

# Default values
ENVIRONMENT="development"
ACTION="install"
CHART_PATH="./python-miniblog"
RELEASE_NAME="python-miniblog"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [action]"
    echo ""
    echo "Environment:"
    echo "  development  - Deploy to development environment (default)"
    echo "  testing      - Deploy to testing environment"
    echo "  production   - Deploy to production environment"
    echo ""
    echo "Action:"
    echo "  install      - Install the helm chart (default)"
    echo "  upgrade      - Upgrade the existing deployment"
    echo "  uninstall    - Uninstall the deployment"
    echo "  status       - Show deployment status"
    echo "  dry-run      - Perform a dry run of the deployment"
    echo ""
    echo "Examples:"
    echo "  $0 development install"
    echo "  $0 production upgrade"
    echo "  $0 testing uninstall"
    echo "  $0 production status"
}

# Parse command line arguments
if [ $# -ge 1 ]; then
    ENVIRONMENT=$1
fi

if [ $# -ge 2 ]; then
    ACTION=$2
fi

# Validate environment
case $ENVIRONMENT in
    development|testing|production)
        print_info "Environment: $ENVIRONMENT"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        show_usage
        exit 1
        ;;
esac

# Set environment-specific values
VALUES_FILE="values-${ENVIRONMENT}.yaml"
NAMESPACE="miniblog"

case $ENVIRONMENT in
    development)
        NAMESPACE="miniblog-dev"
        RELEASE_NAME="python-miniblog-dev"
        ;;
    testing)
        NAMESPACE="miniblog-test"
        RELEASE_NAME="python-miniblog-test"
        ;;
    production)
        NAMESPACE="miniblog"
        RELEASE_NAME="python-miniblog"
        ;;
esac

# Check if values file exists
if [ ! -f "$CHART_PATH/$VALUES_FILE" ]; then
    print_error "Values file not found: $CHART_PATH/$VALUES_FILE"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed. Please install Helm first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Function to create namespace if it doesn't exist
create_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    else
        print_info "Namespace $NAMESPACE already exists"
    fi
}

# Function to install/upgrade helm chart
install_chart() {
    create_namespace
    
    print_info "Installing/Upgrading $RELEASE_NAME in namespace $NAMESPACE"
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --values "$CHART_PATH/$VALUES_FILE" \
        --wait \
        --timeout 10m
    
    print_success "Deployment completed successfully!"
}

# Function to uninstall helm chart
uninstall_chart() {
    print_info "Uninstalling $RELEASE_NAME from namespace $NAMESPACE"
    helm uninstall "$RELEASE_NAME" --namespace "$NAMESPACE"
    
    print_warning "Do you want to delete the namespace $NAMESPACE? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        kubectl delete namespace "$NAMESPACE"
        print_success "Namespace $NAMESPACE deleted"
    fi
    
    print_success "Uninstallation completed!"
}

# Function to show status
show_status() {
    print_info "Showing status for $RELEASE_NAME in namespace $NAMESPACE"
    helm status "$RELEASE_NAME" --namespace "$NAMESPACE"
    
    print_info "Showing pods in namespace $NAMESPACE"
    kubectl get pods --namespace "$NAMESPACE"
    
    print_info "Showing services in namespace $NAMESPACE"
    kubectl get services --namespace "$NAMESPACE"
}

# Function to perform dry run
dry_run() {
    print_info "Performing dry run for $RELEASE_NAME"
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --values "$CHART_PATH/$VALUES_FILE" \
        --dry-run \
        --debug
}

# Execute action
case $ACTION in
    install)
        install_chart
        ;;
    upgrade)
        install_chart
        ;;
    uninstall)
        uninstall_chart
        ;;
    status)
        show_status
        ;;
    dry-run)
        dry_run
        ;;
    *)
        print_error "Invalid action: $ACTION"
        show_usage
        exit 1
        ;;
esac

print_success "Operation completed successfully!"