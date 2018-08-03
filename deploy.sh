#!/bin/bash
set -ex

ssh root@hugosandelius.se "cat > .env" <<EOF
SLACK_API_TOKEN=$SLACK_API_TOKEN
SEARCH_API_KEY=$SEARCH_API_KEY
SEARCH_API_ENGINE_ID=$SEARCH_API_ENGINE_ID
EOF

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se "docker-compose pull && \
    docker-compose up -d && \
    docker-compose exec nginx nginx -s reload && \
    docker image prune -f"