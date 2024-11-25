#Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] 
# such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0

list1 = [-4, 7, 0, -2, 5, -8, 3, 1, -6, 9]
list2 = []
for i in list1:
    for j  in list1:
        if j==i:
            continue
        else:
            for k in list1:
                if k==i or k==j:
                    continue
                else:
                    if i+j+k==0:
                        L = sorted([i,j,k])
                        if L not in list2:
                            list2.append(L)
                        else:
                            continue
print(list2)