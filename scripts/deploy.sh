#!/bin/bash
set -e
# Deploy Django project
export SERVER=mgc
./scripts/backup-database.sh
./scripts/upload-code.sh
./scripts/install-code.sh