import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime
import zerto as z


def aggregate_data(data):
    zorg_aggregates = defaultdict(lambda: {
        "Total VMs": 0,
        "Total vCPU": 0,
        "Total CPU (MHz)": 0,
        "Total Active Memory (GB)": 0,
        "Total Consumed Memory (GB)": 0,
        "Total Provisioned Memory (GB)": 0,
        "Total Provisioned Storage (GB)": 0,
        "Total Used Storage (GB)": 0,
    })

    for item in data:
        zorg_name = item['zorgName']
        # if zorg_name != "FishBowl":
        #     continue
        # Check if the VPG or VM data exists and is not empty
        if 'VPG' in item and item['VPG'].get('VMs'):

            for vm in item['VPG']['VMs']:
                # Aggregate CPU, Memory, and Storage details
                zorg_aggregates[zorg_name]["Total VMs"] += 1
                zorg_aggregates[zorg_name]["Total vCPU"] += vm['Cpu'].get('NumberOfvCpus', 0)
                zorg_aggregates[zorg_name]["Total CPU (MHz)"] += vm['Cpu'].get('CpuUsedInMhz', 0)
                zorg_aggregates[zorg_name]["Total Active Memory (GB)"] += vm['Memory'].get('ActiveGuestMemoryInMB', 0)/1024
                zorg_aggregates[zorg_name]["Total Consumed Memory (GB)"] += vm['Memory'].get('ConsumedHostMemoryInMB', 0)/1024
                zorg_aggregates[zorg_name]["Total Provisioned Memory (GB)"] += vm['Memory'].get('MemoryInMB', 0)/1024
                zorg_aggregates[zorg_name]["Total Provisioned Storage (GB)"] += vm['Storage'].get('VolumesProvisionedStorageInGB', 0)
                zorg_aggregates[zorg_name]["Total Used Storage (GB)"] += vm['Storage'].get('VolumesUsedStorageInGB', 0)
    
    # Remove Zorgs that have no aggregated data
    zorg_aggregates = {zorg: totals for zorg, totals in zorg_aggregates.items() if any(totals.values())}
    
    return zorg_aggregates

def send_email(aggregates):
    month = datetime.now().strftime("%B")
    smtp_server = '10.200.201.15'
    smtp_port = 25
    sender = 'systems@tonaquint.com'
    receivers = 'tsully28@hotmail.com'
    subject = f'{month} Zerto Usage Report'
    email_body = f'Monthly Zerto Usage Report for {month}\n\n'
    for stuff in aggregates:
        for zorg, stats in stuff.items():
            email_body += f"Zorg Name: {zorg}\n"
            email_body += f"Total VMs: {stats['Total VMs']}\n"
            email_body += f"Total vCPU: {round(stats['Total vCPU'])}\n"
            # email_body += f"Total CPU (MHz): {stats['Total CPU (MHz)']}\n"
            # email_body += f"Total Active Memory (GB): {round(stats['Total Active Memory (GB)']/1024,2)}\n"
            # email_body += f"Total Consumed Memory (GB): {round(stats['Total Consumed Memory (GB)']/1024,2)}\n"
            if stats['Total Provisioned Memory (GB)'] > 2000:
                email_body += f"Total Provisioned Memory (TB): {round(stats['Total Provisioned Memory (GB)']/1024,3)}\n"
            else:
                email_body += f"Total Provisioned Memory (GB): {round(stats['Total Provisioned Memory (GB)'],2)}\n"
            if stats['Total Provisioned Storage (GB)'] > 2000:
                email_body += f"Total Provisioned Storage (TB): {round(stats['Total Provisioned Storage (GB)']/1024,3)}\n"
            else:
                email_body += f"Total Provisioned Storage (GB): {round(stats['Total Provisioned Storage (GB)'],2)}\n"
            if stats['Total Used Storage (GB)'] > 2000:
                email_body += f"Total Used Storage (TB): {round(stats['Total Used Storage (GB)']/1024,3)}\n"
            else:
                email_body += f"Total Used Storage (GB): {round(stats['Total Used Storage (GB)'],2)}\n"
            email_body += "\n----------------------------------\n\n"



    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receivers
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.sendmail(sender, receivers, msg.as_string())
        print("Successfully sent email")
    except smtplib.SMTPException:
        print("Error: unable to send email")




zerto = z.ZertoGet()

zorgs = zerto.get_zorgs_by_vpg()
full_data = []

for zorg in zorgs:
    vmcount = 0
    #print(zorg)
    resources = zerto.get_zorg_info_from_resources(zorg) #Dictionary
    for vms in resources:
        for vm in vms['VPG']['VMs']:
            vmcount += 1
        


    data = aggregate_data(resources)
    if data == {}:
        continue

    full_data.append(data)
    
    #print(f"Total VMs for {zorg}: {vmcount}")

#print(full_data)

  
send_email(full_data)

#print(zerto.zerto_auth.base_url)
