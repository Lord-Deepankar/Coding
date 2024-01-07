dict1 = {}
print(dict1)
while True:
    a = str(input('enter the key...'))
    b = str(input('enter value for the key...'))
    update_dict = {a:b}
    dict1.update(update_dict)
    a = input('wawnna continue y/n...')
    if a=='y':
        continue
    else:
        break
print(dict1)
    