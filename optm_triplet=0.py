#Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] 
# such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0

list1 = [-4, 7, 0, -2, 5, -8, 3, 1, -6, 9]
sorted_list = sorted(list1)
list2 = []

for i in range(len(sorted_list)-2):
    # First optimization: skip duplicate i values
    if i > 0 and sorted_list[i] == sorted_list[i-1]:
        continue
        
    left = i+1
    right = len(sorted_list)-1
   
    while left < right:
        current_sum = sorted_list[i] + sorted_list[left] + sorted_list[right]
        
        if current_sum == 0:
            # Your readable duplicate check
            if [sorted_list[i], sorted_list[left], sorted_list[right]] not in list2:
                list2.append([sorted_list[i], sorted_list[left], sorted_list[right]])
            left += 1
            right -= 1
        elif current_sum < 0:
            left += 1
        else:
            right -= 1

print(list2)
