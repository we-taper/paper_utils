#!/usr/bin/zsh
docker build --tag tapering/paperutil:latest .
dockerlogin-tapering
docker push tapering/paperutil:latest