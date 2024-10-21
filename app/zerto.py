import requests
from config import settings
from datetime import datetime
import pytz

requests.packages.urllib3.disable_warnings()


def utc_to_mountain_time(utc_time):
    utc_time = datetime.strptime(utc_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    utc_time = pytz.utc.localize(utc_time)
    mountain_time = utc_time.astimezone(pytz.timezone('US/Mountain'))
    return mountain_time.strftime('%Y-%m-%d %H:%M:%S')

class _ZertoAuth():
    def __init__(self, location):
        if location == 'sgu':
            self.base_url = settings.sgu_prod_url
            self.secret = settings.sgu_prod_secret
        elif location == 'boi':
            self.base_url = settings.boi_prod_url
            self.secret = settings.boi_prod_secret
        else:
            print("Invalid location... Please choose either 'sgu' or 'boi'")
            return
    def auth(self):
        auth_url = f'https://{self.base_url}/auth/realms/zerto/protocol/openid-connect/token'
        print("Attempting to authenticate...")

        response = requests.post(auth_url, 
                                data={"grant_type": "client_credentials", 
                                        "client_id": "zerto-api", 
                                        "client_secret": self.secret}, 
                                timeout=10, 
                                verify=False)

        if response.status_code == 200:
            print(f"Authentication successful!")
            return response.json()['access_token']
        else:
            print(f'Failed to authenticate: {response.status_code} - {response.text}')
            print('Please check your credentials and try again...')
            return None
        

class ZertoGet():
    def __init__(self, location):
        self.zerto_auth = _ZertoAuth(location)
        self.auth_token = self.zerto_auth.auth()
        self.subs_naughty_list = [8, 24, 27, 30, 31, 32, 33] # List of substatuses that are not good and will cause a VPG to be considered down
        self.base_url = self.zerto_auth.base_url
        if not self.auth_token:
            print("There was a problem getting the auth token...")
            return None

    def get_vpgs(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = f'https://{self.base_url}/v1/vpgs'
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            list_of_vpgs = response.json()
            return list_of_vpgs
        else:
            print("Failed to get VPGs...")
            print(f'Error: {response.status_code} - {response.text} for endpoint')
            return None
    
    def get_sites(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = f'https://{self.base_url}/v1/peersites'
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            list_of_sites = response.json()
            return list_of_sites
        else:
            print("Failed to get sites...")
            print(f'Error: {response.status_code} - {response.text} for endpoint')
            return None

    def get_vras(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = f'https://{self.base_url}/v1/vras'
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            list_of_vras = response.json()
            return list_of_vras
        else:
            print("Failed to get VRAs...")
            print(f'Error: {response.status_code} - {response.text} for endpoint')
            return None
        
    def get_status(self, status=None) -> str:
        '''
        Returns the status of a VPG if a status number is provided. If no status number is provided, it returns a list of all possible statuses.
        '''
        headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.auth_token}'
            }
        url = f'https://{self.base_url}/v1/vpgs/statuses'
        if status == None:
            response = requests.get(url, headers=headers, verify=False)
            list_of_statuses = response.json()
            print(list_of_statuses)
        else:
            response = requests.get(url, headers=headers, verify=False)
            list_of_statuses = response.json()
            if status > 2:
                print("This status is not good... VPG Considered DOWN...")
            return list_of_statuses[status]
    
    def get_substatus(self, substatus=None):
        '''
        Returns the substatus of a VPG if a substatus number is provided. If no substatus number is provided, it returns a list of all possible substatuses.
        '''
        headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {self.auth_token}'
            }
        url = f'https://{self.base_url}/v1/vpgs/substatuses'
        if substatus == None:
            response = requests.get(url, headers=headers, verify=False)
            list_of_substatuses = response.json()
            return list_of_substatuses
        else:
            response = requests.get(url, headers=headers, verify=False)
            list_of_substatuses = response.json()
            return list_of_substatuses[substatus]

    
    def get_throughput_zvm(self) -> int:
        '''
        Returns the total throughput of all VPGs on a ZVM
        '''
        list_of_vpgs = self.get_vpgs()
        throughput = 0
        for vpg in list_of_vpgs:
            throughput += vpg['ThroughputInMB']
        return throughput
    
    def get_throughput_sites(self) -> list:
        '''
        Returns a list with the total throughput of all VPGs on each site

        [{'site1': 'throughput1'}, ...]
        '''
        list_of_sites = []
        vpgs = self.get_vpgs()
        for vpg in vpgs:
            site = vpg['ProtectedSiteName']
            if site not in list_of_sites:
                list_of_sites.append(site)
        all_sites_with_throughput = []
        for site in list_of_sites:
            throughput = 0
            for vpg in vpgs:
                if vpg['ProtectedSiteName'] == site:
                    throughput += vpg['ThroughputInMB']
                one_site_with_throughput = {site: throughput}
                
            all_sites_with_throughput.append(one_site_with_throughput)
        return all_sites_with_throughput
    
    def get_percent_vpgs_up(self):
        vpg_list = self.get_vpgs()
        list_of_sites = []
        percent_vpgs_per_site = []
        for vpg in vpg_list:
            site = vpg['ProtectedSiteName']
            if site not in list_of_sites:
                list_of_sites.append(site)
        for site in list_of_sites:
            total_vpgs = 0
            up_vpgs = 0
            for vpg in vpg_list:
                if vpg['ProtectedSiteName'] == site:
                    total_vpgs += 1
                    if vpg['Status'] == 0 or 1:
                        up_vpgs += 1
            percent = (up_vpgs / total_vpgs) * 100
            percent_vpgs_per_site.append({site: percent})
        return percent_vpgs_per_site
    
    def get_server_date_time(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = f'https://{self.base_url}/v1/serverDateTime/ServerDateTimeUTC'
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            date_time = response.json()
            #Turn response into mountain time
            mountain_time = utc_to_mountain_time(date_time)
            class MountainTime():
                def __init__(self, mountain_time):
                    self.mountain_time = mountain_time
                    self.year = mountain_time[0:4]
                    self.month = mountain_time[5:7]
                    self.day = mountain_time[8:10]
                    self.hour = mountain_time[11:13]
                    self.minute = mountain_time[14:16]
                    self.second = mountain_time[17:19]
                    self.date = f'{self.year}-{self.month}-{self.day}'
            return MountainTime(mountain_time)
        else:
            print("Failed to get date and time...")
            print(f'Error: {response.status_code} - {response.text} for endpoint')
            return None
        
    def get_resources(self, zorg_name):
        ###EXAMPLE URL: https://sgu-zvm.tonaquint.local/v1/reports/resources?startTime=2024-10-08&endTime=2024-10-09&pageNumber=1&zorgName=3FORM
        m_time = self.get_server_date_time()
        date = m_time.date
        page_number = 1
        all_resources = []
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        stop = True
        while stop:
            
            url = f'https://{self.base_url}/v1/reports/resources?startTime={date}&pageNumber={page_number}&zorgName={zorg_name}&pageSize=1000'
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                resources = response.json()
                all_resources.extend(resources)
                page_number += 1
            else:
                print("Failed to get resources...")
                print(f'Error: {response.status_code} - {response.text} for endpoint')
                return None
            if resources == []:
                stop = False
        return all_resources

    def get_zorgs_by_vpg(self) -> list:
        list_of_vpgs = self.get_vpgs()
        list_of_zorgs = []
        for vpg in list_of_vpgs:
            if vpg['OrganizationName'] not in list_of_zorgs:
                list_of_zorgs.append(vpg['OrganizationName'])
        return list_of_zorgs

    def get_zorg_info_from_resources(self, zorg_name):
        resources = self.get_resources(zorg_name)
        all_zorg_info = []
        for resource in resources:
            
            zorg_info = {'zorgName': zorg_name,
                         'VPG': {
                             'VpgName': resource['Vpg']['VpgName'],
                             'VMs': []
                         }}

            if zorg_info['VPG']['VpgName'] == resource['Vpg']['VpgName']:
    
                    vm_info = {'VmName': resource['ProtectedSite']['VmInfo']['VmName'],
                            'Cpu': {
                                'NumberOfvCpus': resource['ProtectedSite']['VmInfo']['Cpu']['NumberOfvCpus'],
                                'CpuUsedInMhz': resource['ProtectedSite']['VmInfo']['Cpu']['CpuUsedInMhz']},
                                'Memory': {
                                    'ActiveGuestMemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['ActiveGuestMemoryInMB'],
                                    'ConsumedHostMemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['ConsumedHostMemoryInMB'],
                                    'MemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['MemoryInMB']},
                                'Storage': {
                                    'VolumesProvisionedStorageInGB': resource['ProtectedSite']['Storage']['VolumesProvisionedStorageInGB'],
                                    'VolumesUsedStorageInGB': resource['ProtectedSite']['Storage']['VolumesUsedStorageInGB'],
                                }
                    }
                    zorg_info['VPG']['VMs'].append(vm_info)
                    all_zorg_info.append(zorg_info)
            else:
                if zorg_info['zorgName'] == zorg_name:
                    for vpg in zorg_info['VPG']:
                        if vpg['VpgName'] == resource['Vpg']['VpgName']:
                            vm_info = {'VmName': resource['ProtectedSite']['VmInfo']['VmName'],
                                'Cpu': {
                                    'NumberOfvCpus': resource['ProtectedSite']['VmInfo']['Cpu']['NumberOfvCpus'],
                                    'CpuUsedInMhz': resource['ProtectedSite']['VmInfo']['Cpu']['CpuUsedInMhz']},
                                    'Memory': {
                                        'ActiveGuestMemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['ActiveGuestMemoryInMB'],
                                        'ConsumedHostMemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['ConsumedHostMemoryInMB'],
                                        'MemoryInMB': resource['ProtectedSite']['VmInfo']['Memory']['MemoryInMB']},
                                    'Storage': {
                                        'VolumesProvisionedStorageInGB': resource['ProtectedSite']['Storage']['VolumesProvisionedStorageInGB'],
                                        'VolumesUsedStorageInGB': resource['ProtectedSite']['Storage']['VolumesUsedStorageInGB'],
                                    }
                        }
                        zorg_info['VPG']['VMs'].append(vm_info)
                        all_zorg_info.append(zorg_info)
        #zorg_info['VPG']['VMs'] = set(zorg_info['VPG']['VMs'])
        
        return all_zorg_info
    
    def get_vms_of_zorg(self, zorg):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = f'https://{self.base_url}/v1/vms?organizationName={zorg}&includeBackupedVms=false'
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            resources = response.json()
            return resources
        else:
            print("Failed to get Zorg VMs...")
            print(f'Error: {response.status_code} - {response.text} for endpoint')
            return None