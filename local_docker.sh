#!/bin/bash

# Define colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${YELLOW}Usage: $0 {start|stop|restart|status} [--rebuild] [--no-cache]${NC}"
    echo -e "Options:"
    echo -e "  --rebuild    Rebuild images"
    echo -e "  --no-cache   Build without using cache"
    exit 1
}

# Function to start containers
start_containers() {
    local rebuild=$1
    local no_cache=$2
    
    echo -e "${GREEN}Starting all containers...${NC}"
    if [ "$rebuild" = true ] && [ "$no_cache" = true ]; then
        docker-compose build --no-cache && docker-compose up -d
    elif [ "$rebuild" = true ]; then
        docker-compose up -d --build
    else
        docker-compose up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All containers started successfully.${NC}"
    else
        echo -e "${RED}Failed to start containers.${NC}"
    fi
}

# Function to stop containers
stop_containers() {
    echo -e "${RED}Stopping all containers...${NC}"
    docker-compose down
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All containers stopped successfully.${NC}"
    else
        echo -e "${RED}Failed to stop containers.${NC}"
    fi
}

# Function to restart containers
restart_containers() {
    local rebuild=$1
    local no_cache=$2
    
    echo -e "${YELLOW}Restarting all containers...${NC}"
    docker-compose down
    
    if [ "$rebuild" = true ] && [ "$no_cache" = true ]; then
        docker-compose build --no-cache && docker-compose up -d
    elif [ "$rebuild" = true ]; then
        docker-compose up -d --build
    else
        docker-compose up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All containers restarted successfully.${NC}"
    else
        echo -e "${RED}Failed to restart containers.${NC}"
    fi
}

# Function to check container status
check_status() {
    echo -e "${YELLOW}Checking container status...${NC}"
    docker-compose ps
}

# Parse command line arguments
COMMAND=$1
shift

REBUILD=false
NO_CACHE=false

while [ "$1" != "" ]; do
    case $1 in
        --rebuild )  REBUILD=true
                    ;;
        --no-cache ) NO_CACHE=true
                    ;;
        * )         usage
                    exit 1
    esac
    shift
done

# Main logic
case "$COMMAND" in
    start)
        start_containers $REBUILD $NO_CACHE
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers $REBUILD $NO_CACHE
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac