#!/bin/bash
set -ex

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se \ "echo SLACK_API_TOKEN=$SLACK_API_TOKEN > .env \
    && echo SEARCH_API_KEY=$SEARCH_API_KEY >> .env \
    && echo SEARCH_API_ENGINE_ID=$SEARCH_API_ENGINE_ID >> .env \
    && docker-compose pull && docker-compose up -d"