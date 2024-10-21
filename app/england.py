# Description: This script will gather all VPGs and their VMs for CREngland and send an email with the data in a CSV attachment.
import zerto as z
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import settings
import csv
from datetime import datetime

#get all VPGs and their VMs for CREngland

zerto = z.ZertoGet('boi')
all_vms = zerto.get_vms_of_zorg('CREngland')

full_data = []


#data1 = [{'vpg1': ['vm1', 'vm2', 'vm3']}, {'vpg2': ['vm4', 'vm5', 'vm6']}]

list_of_vpgs = []
for vm in all_vms:
    if vm['VpgName'] not in list_of_vpgs:
        list_of_vpgs.append(vm['VpgName'])

for vpg in list_of_vpgs:
    vms = []
    for vm in all_vms:
        if vm['VpgName'] == vpg:
            vms.append(vm['VmName'])
    data = {vpg: vms}
    full_data.append(data)

def write_to_csv(data):
    with open('../data.csv', 'w') as file:
        writer = csv.writer(file)
        for vpg in data:
            for key, value in vpg.items():
                writer.writerow([key, value])

write_to_csv(full_data)

def send_email():


    # email_body = ''
    # email_body += "\n----------------------------------\n\n"
    # for vpg in data:
    #     #email_body += f'{vpg}\n'
    #     for key, value in vpg.items():
    #         email_body += f'\n{key}\n'
    #         for vm in value:
    #             email_body += f'\t{vm}\n'
    # email_body += "\n----------------------------------\n\n"
    # print(email_body)

    email_body = 'If you see any inaccuracies in this report, please contact the Tonaquint Cloud team.\n\n'


    sender = settings.sender
    receiver = settings.receiver
    date = datetime.now().strftime('%m-%d-%Y')
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = "tonaquintreports@crengland.com"
    msg['Subject'] = 'CREngland Zerto Report for Week of ' + date
    msg.attach(MIMEText(email_body, 'plain'))
    attachment = open('data.csv', 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= data.csv")
    msg.attach(part)

    try:
        smtpObj = smtplib.SMTP(settings.smtp_server, 25)
        smtpObj.sendmail(sender, receiver, msg.as_string())
        print(f"Successfully sent email")
    except smtplib.SMTPException:
        print("Error: unable to send email")



if __name__ == '__main__':
    send_email()