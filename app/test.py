import zerto as z

zerto = z.ZertoGet()

# zorgs = zerto.get_zorgs_by_vpg()
# print(zorgs)

resources = zerto.get_zorg_info_from_resources('Allstar-Healthcare')
count = 0
for resource in resources:
    print(resource)
    print()
    count += 1
print(count)


    