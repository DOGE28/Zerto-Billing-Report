import zerto as z

zerto = z.ZertoGet()

# zorgs = zerto.get_zorgs_by_vpg()
# print(zorgs)

# vms = zerto.get_resources('FishBowl')
# count = 0
# for vm in vms:
#     count += 1
# print(f'Total Fishbowl VMs (Reports API): {count}')

# all_vms = zerto.get_vms_of_zorg('FishBowl')
# count1 = 0

# for vm in all_vms:
#     count1 += 1

# print(f'Total Fishbowl VMs (VMs API): {count1}')

# zorgs = zerto.get_resources('FishBowl')

# #print(zorgs)

# count2 = 0

# for zorg in zorgs:
#     if zorg['ProtectedSite']['VmInfo']:
#         count2 += 1

# print(f'Total Fishbowl VMs (ProtectedSite API): {count2}')


resources = zerto.get_zorg_info_from_resources('FishBowl')
print(resources)



# resources = zerto.get_zorg_info_from_resources('FishBowl')
# count = 0
# for resource in resources:
#     print(resource)
#     print()
#     count += 1
# print(count)


    