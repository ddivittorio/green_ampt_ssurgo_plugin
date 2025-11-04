#!/bin/bash

# Docker run script for Green-Ampt Estimation Toolkit

set -e

IMAGE_NAME="green-ampt-app"
CONTAINER_NAME="green-ampt-container"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    print_warning "docker-compose not found. Using docker directly."
    DOCKER_COMPOSE_CMD=""
fi

# Function to build the Docker image
build_image() {
    print_info "Building Docker image..."
    if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD build
    else
        docker build -t $IMAGE_NAME .
    fi
    print_info "Docker image built successfully!"
}

# Function to run CLI command
run_cli() {
    print_info "Running Green-Ampt CLI..."

    # Build image if it doesn't exist
    if ! docker images $IMAGE_NAME | grep -q $IMAGE_NAME; then
        build_image
    fi

    # Run the CLI command
    if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD run --rm green-ampt "$@"
    else
        docker run --rm -v "$(pwd)/outputs:/app/outputs" -v "$(pwd)/test_aoi:/app/test_aoi:ro" $IMAGE_NAME "$@"
    fi
}

# Function to run Jupyter notebook
run_notebook() {
    print_info "Starting Jupyter notebook server..."

    # Build image if it doesn't exist
    if ! docker images $IMAGE_NAME | grep -q $IMAGE_NAME; then
        build_image
    fi

    print_info "Jupyter notebook will be available at: http://localhost:8891"
    print_info "Press Ctrl+C to stop the server"

    if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD --profile notebook up notebook
    else
    docker run --rm -p 8891:8888 -v "$(pwd)/outputs:/app/outputs" -v "$(pwd)/test_aoi:/app/test_aoi:ro" -v "$(pwd):/app" $IMAGE_NAME conda run -n green-ampt jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token='' --ServerApp.password=''
    fi
}

# Function to show usage
show_usage() {
    echo "Green-Ampt Estimation Toolkit - Docker Runner"
    echo ""
    echo "Usage:"
    echo "  $0 build          - Build the Docker image"
    echo "  $0 cli [args...]  - Run CLI command with arguments"
    echo "  $0 notebook       - Start Jupyter notebook server"
    echo "  $0 help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 cli --aoi test_aoi/test_aoi.shp --output-dir outputs --data-source pysda"
    echo "  $0 notebook"
    echo ""
    echo "For CLI help: $0 cli --help"
}

# Main script logic
case "${1:-help}" in
    build)
        build_image
        ;;
    cli)
        shift
        run_cli "$@"
        ;;
    notebook)
        run_notebook
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac