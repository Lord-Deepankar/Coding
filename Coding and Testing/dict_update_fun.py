dict1 = {}
print(dict1)
while True:
    a = str(input('enter the key...'))
    b = str(input('enter value for the key...'))
    dict1[a]=b
    a = input('wawnna continue y/n...')
    if a=='y':
        continue
    else:
        break
print(dict1)
update_dict = {'6':45}
dict1['6'] = 89
print(dict1)