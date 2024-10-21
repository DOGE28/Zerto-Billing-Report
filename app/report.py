import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime
import zerto as z
from config import settings


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

def send_email(aggregates, location):
    if location == 'boi':
        zvm = "Boise"
    elif location == 'sgu':
        zvm = "St. George"
    month = datetime.now().strftime("%B")
    smtp_server = settings.smtp_server
    smtp_port = 25
    sender = settings.sender
    test = settings.receiver
    receiver = test
    cc = settings.cc
    subject = f'{month} {zvm} Zerto Usage Report'
    email_body = f'Monthly {zvm} Zerto Usage Report for {month}\n\n'
    all_total_prov_mem = 0
    all_total_prov_storage = 0
    all_total_used_storage = 0
    all_total_vms = 0
    all_total_vcpu = 0

    for stuff in aggregates:
        for zorg, stats in stuff.items():
            all_total_prov_mem += stats['Total Provisioned Memory (GB)']
            all_total_prov_storage += stats['Total Provisioned Storage (GB)']
            all_total_used_storage += stats['Total Used Storage (GB)']
            all_total_vms += stats['Total VMs']
            all_total_vcpu += stats['Total vCPU']
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

    email_body += 'TOTAL USAGE'
    email_body += f"Total VMs: {all_total_vms}\n"
    email_body += f"Total vCPU: {round(all_total_vcpu)}\n"
    if all_total_prov_mem > 2000:
        email_body += f"Total Provisioned Memory (TB): {round(all_total_prov_mem/1024,3)}\n"
    else:
        email_body += f"Total Provisioned Memory (GB): {round(all_total_prov_mem,2)}\n"
    if all_total_prov_storage > 2000:
        email_body += f"Total Provisioned Storage (TB): {round(all_total_prov_storage/1024,3)}\n"
    else:
        email_body += f"Total Provisioned Storage (GB): {round(all_total_prov_storage,2)}\n"
    if all_total_used_storage > 2000:
        email_body += f"Total Used Storage (TB): {round(all_total_used_storage/1024,3)}\n"
    else:
        email_body += f"Total Used Storage (GB): {round(all_total_used_storage,2)}\n"
    email_body += "\n----------------------------------\n\n"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg['Cc'] = cc
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.sendmail(sender, receiver, msg.as_string())
        print(f"Successfully sent email from {zvm}")
    except smtplib.SMTPException:
        print("Error: unable to send email")



def gather_data(location):
    zerto = z.ZertoGet(location)
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
    return full_data

def gather_data_one_zorg(location):
    zerto = z.ZertoGet(location)
    zorgs = zerto.get_zorgs_by_vpg()
    full_data = []
    for zorg in zorgs:
        if zorg != 'CREngland':
            continue
        resources = zerto.get_zorg_info_from_resources(zorg)
        data = aggregate_data(resources)
    if data == {}:
        return
    full_data.append(data)
    return full_data
    
def main():
    for location in ['boi', 'sgu']:
        data = gather_data(location)
        send_email(data, location)

if __name__ == '__main__':
    main()