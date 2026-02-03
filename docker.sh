#!/bin/bash

# ClarityMentor Docker Helper Script
# Provides convenient commands for Docker operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

show_help() {
    cat << EOF
${BLUE}ClarityMentor Docker Helper${NC}

Usage: ./docker.sh [COMMAND]

Commands:
  build           Build Docker images
  up              Start all services
  down            Stop all services
  restart         Restart all services
  logs            View service logs
  logs-backend    View backend logs
  logs-frontend   View frontend logs
  logs-cache      View cache logs
  status          Show service status
  health          Check service health
  clean           Remove containers and volumes
  clean-all       Remove containers, volumes, and images
  exec-backend    Open bash in backend container
  exec-frontend   Open bash in frontend container
  exec-cache      Open redis-cli in cache container
  ps              List running containers
  dev             Start in development mode with hot-reload
  prod            Start in production mode
  help            Show this help message

Examples:
  ./docker.sh build
  ./docker.sh up
  ./docker.sh logs -f
  ./docker.sh logs-backend
  ./docker.sh exec-backend

EOF
}

build() {
    print_header "Building Docker Images"
    docker-compose build
    print_success "Images built successfully"
}

up() {
    print_header "Starting Services"
    docker-compose up -d

    echo ""
    print_warning "Waiting for services to be ready..."
    sleep 5

    docker-compose ps

    echo ""
    print_success "Services are starting"
    echo ""
    echo "Access points:"
    echo "  - Frontend: http://localhost:2000"
    echo "  - Backend: http://localhost:2323"
    echo "  - Backend API Docs: http://localhost:2323/docs"
    echo "  - Redis: localhost:2999"
    echo ""
    echo "View logs: ./docker.sh logs"
}

down() {
    print_header "Stopping Services"
    docker-compose down
    print_success "Services stopped"
}

restart() {
    print_header "Restarting Services"
    docker-compose restart
    print_success "Services restarted"
}

logs() {
    docker-compose logs -f "$@"
}

logs_backend() {
    docker-compose logs -f backend
}

logs_frontend() {
    docker-compose logs -f frontend
}

logs_cache() {
    docker-compose logs -f cache
}

status() {
    print_header "Service Status"
    docker-compose ps
}

health() {
    print_header "Service Health Check"

    echo "Checking Backend..."
    if curl -s http://localhost:2323/api/health > /dev/null; then
        print_success "Backend is healthy"
    else
        print_error "Backend is not responding"
    fi

    echo ""
    echo "Checking Frontend..."
    if curl -s http://localhost:2000 > /dev/null; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
    fi

    echo ""
    echo "Checking Cache..."
    if docker exec claritymentor-cache redis-cli ping > /dev/null 2>&1; then
        print_success "Cache is responding"
    else
        print_error "Cache is not responding"
    fi
}

clean() {
    print_header "Cleaning Up"
    print_warning "Stopping and removing containers and volumes..."
    docker-compose down -v
    print_success "Cleanup complete"
}

clean_all() {
    print_header "Deep Cleaning"
    print_warning "This will remove containers, volumes, and images..."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker-compose rmi -f
        print_success "Deep cleanup complete"
    else
        print_warning "Cleanup cancelled"
    fi
}

exec_backend() {
    docker exec -it claritymentor-backend bash
}

exec_frontend() {
    docker exec -it claritymentor-frontend bash
}

exec_cache() {
    docker exec -it claritymentor-cache redis-cli
}

ps_containers() {
    docker-compose ps
}

dev() {
    print_header "Starting in Development Mode"
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    print_success "Development mode started with hot-reload enabled"
    echo ""
    ./docker.sh logs
}

prod() {
    print_header "Starting in Production Mode"
    docker-compose up -d
    print_success "Production mode started"
    docker-compose ps
}

# Main command handling
case "${1:-}" in
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    restart)
        restart
        ;;
    logs)
        shift || true
        logs "$@"
        ;;
    logs-backend)
        logs_backend
        ;;
    logs-frontend)
        logs_frontend
        ;;
    logs-cache)
        logs_cache
        ;;
    status|ps)
        status
        ;;
    health)
        health
        ;;
    clean)
        clean
        ;;
    clean-all)
        clean_all
        ;;
    exec-backend)
        exec_backend
        ;;
    exec-frontend)
        exec_frontend
        ;;
    exec-cache)
        exec_cache
        ;;
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "Unknown command: ${1:-}"
        echo ""
        show_help
        exit 1
        ;;
esac
