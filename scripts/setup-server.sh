#!/bin/bash
set -e
# Sets up new server to host Django app
export SERVER=
DJANGO_SETTINGS_MODULE="mgc.settings.prod"

# Take secret key as 1st argument
if [[ -z "$1" ]]
then
    echo "ERROR: No value set for DJANGO_SECRET_KEY, argument required."
    exit 1
else
    DJANGO_SECRET_KEY="$1"
fi
echo -e "\n>>> Setting up $SERVER"
ssh root@$SERVER /bin/bash << EOF
    set -e

    echo -e  "\n>>> Updating apt source"
    apt-get -qq update

    echo -e  "\n>>> Upgrading apt packages"
    apt-get -qq upgrade

    echo -e  "\n>>> Installing apt packages"
    apt-get -qq install python3-pip dos2unix tree

    echo -e  "\n>>> Installing virtualenv"
    pip3 install virtualenv

    echo -e  "\n>>> Setting up project folder"
    mkdir -p /app/logs

    echo -e  "\n>>> Creating our virtual environment"
    if [[ ! -d "/app/mgcenv" ]]
    then
        virtualenv -p python3 /app/mgcenv
    else
        echo ">>> Skipping virtualenv creation - already present"
    fi

    echo -e  "\n>>> Setting system environment variables"

    if [[ "\$DJANGO_SETTINGS_MODULE" != "$DJANGO_SETTINGS_MODULE" ]]
    then
        echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE" >> /etc/environment
    else
        echo ">>> Skipping DJANGO_SETTINGS_MODULE - already present"
    fi
    if [[ "\$DJANGO_SECRET_KEY" != "$DJANGO_SECRET_KEY" ]]
    then
        echo "DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY" >> /etc/environment
    else
        echo ">>> Skipping DJANGO_SECRET_KEY - already present"
    fi
EOF

./scripts/upload-code.sh

ssh root@$SERVER /bin/bash << EOF
    set-e

    echo -e "\n>>> Deleting old files"
    rm -rf /app/mgc
    rm -rf /app/config
    rm -rf /app/scripts
    rm -f /app/requirements.txt

    echo -e "\n>>> Copying new files"
    cp -r /root/deploy/mgc /app/
    cp -r /root/deploy/config /app/
    cp -r /root/deploy/scripts /app/
    cp /root/deploy/requirements.txt /app/

    echo -e "\n>>> Installing python packages"
    cd /app/
    . mgcenv/bin/activate
    pip install -r /app/requirements.txt

    echo -e "\n>>> Runnin django migrations"
    pushd mgc
    ./manage.py migrate

    echo -e "\n>>> Collecting static files"
    ./manage.py collectstatic
    popd
    

    echo -e "\n>>> Starting Supervisord"
    supervisord -c config/supervisord.conf

EOF

echo -e"\n>>> Swapping database"
ssh root@$SERVER "find /app -name *.sqlite3 -delete"
scp db.sqlite3 root@$SERVER:/app/

echo -e "\n>>> Done setting up $SERVER"