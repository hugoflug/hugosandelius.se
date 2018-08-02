#!/bin/bash
set -ex

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se "export SLACK_API_TOKEN=${SLACK_API_TOKEN} && docker-compose pull && docker-compose up -d"