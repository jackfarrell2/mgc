#!/bin/bash
set -e
# Backs up remote database and copies to local
if [[ -z "$SERVER" ]]
then
    echo "ERROR: No value set for SERVER."
    exit 1
fi
echo -e "\n>>> Backing up database on $SERVER"
TIME=$(date "+%s")
DBNAME="db.$TIME.sqlite3"
ssh root@$SERVER /bin/bash << EOF
set -e
mkdir -p /root/backups/
cp /app/db.sqlite3 /root/backups/$DBNAME
EOF
mkdir -p ~/backups/
scp root@mgc:/root/backups/* ~/backups
 