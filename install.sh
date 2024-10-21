#!/bin/bash

function echo_message() {
    echo
    echo "----------------------------------------"
    echo $1
    echo "----------------------------------------"
    echo
}

# Install the required python packages

echo_message "Installing the required python packages"


cd ~/Zerto-Alerts/Zerto-Billing
source venv/bin/activate
pip install -r requirements.txt

# Create .env file

echo_message "Creating the .env file"
cat <<EOL > .env
sgu_prod_url=
sgu_prod_secret=
boi_prod_url=
boi_prod_secret=
fb_prod_url=
fb_prod_secret=
sender=
receiver=
cc=
smtp_server=
EOL

echo_message "Installation completed successfully"



