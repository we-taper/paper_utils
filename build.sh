#!/usr/bin/zsh
# Use date-based versioning.
VERSION=$(date +%Y%m%d)
docker build --tag tapering/paperutil:"$VERSION" --tag tapering/paperutil:latest .
dockerlogin-tapering
#docker push tapering/paperutil:"$VERSION"
#docker push tapering/paperutil:latest
