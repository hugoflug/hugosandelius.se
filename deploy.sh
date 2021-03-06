#!/bin/bash
set -ex

ssh root@hugosandelius.se "cat > .env" <<EOF
SLACK_API_TOKEN=$SLACK_API_TOKEN
SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
SEARCH_API_KEY=$SEARCH_API_KEY
SEARCH_API_ENGINE_ID=$SEARCH_API_ENGINE_ID
SLACK_API_EMOJIFY_TOKEN=$SLACK_API_EMOJIFY_TOKEN
EOF

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se "set -x && \
    docker-compose pull && \
    docker-compose up -d && \
    docker-compose exec -T nginx nginx -s reload && \
    docker image prune -f"