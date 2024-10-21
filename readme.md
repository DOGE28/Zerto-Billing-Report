# Zerto Billing Report
A very simple script that scrapes the following information from each Zorg in the Boise and St George ZVMs:

* Zorg Name
* Total VMs
* Total vCPU
* Total Provisioned Memory
* Total Provisioned Storage
* Total Used Storage



## Installation

Run the following command to create the directory and download the necessary files:

```
mkdir ~/Zerto-Alerts/Zerto-Billing
cd ~/Zerto-Alerts/Zerto-Billing
curl -LO https://github.com/DOGE28/Zerto-Billing-Report/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
cd Zerto-Billing-Report
chmod +x install.sh
```

If this runs without error, run the install script:

```
./install.sh
```

Finally, edit the .env file that was created and fill in the neccessary information.

