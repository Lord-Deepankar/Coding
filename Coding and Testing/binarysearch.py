def search(x):
    list1  = []
    list1 = x
    target = y
    count  = 0
    for i in list1 :
        if target == i :            
            break
        else:
            count = count + 1
    return count

x = []
for i in range (10):
    x.append(int(input("enter number to make the search list..")))
print(x)
y = int(input("enter the number you want to search..."))
print("the index of our target is...", search(x))
