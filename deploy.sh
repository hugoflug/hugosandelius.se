#!/bin/bash
set -ex

scp docker-compose.yml root@hugosandelius.se:~
ssh root@hugosandelius.se "docker login -u hugosandelius -p $DOCKERHUB_PASSWD && docker-compose pull && docker-compose up -d"