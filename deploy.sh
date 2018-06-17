#!/bin/bash
set -ex

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se "echo SLACK_API_TOKEN=$SLACK_API_TOKEN > .env && docker-compose pull && docker-compose up -d"