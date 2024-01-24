def split_list(lst):
    if len(lst) == 1:
        return [lst]
    
    mid = len(lst) // 2
    left = lst[:mid]
    right = lst[mid:]
    
    return split_list(right)

list1 = [1, 2, 3, 4, 5, 6] 

print(split_list(list1))

def merge_list(lst):
    if len(lst) == 1:
        return lst

    mid = len(lst) // 2
    left = lst[:mid]
    right = lst[mid:]

    return merge_list(left) + merge_list(right)

import pytest
from test import merge_list

def test_merge_list_single_element():
    assert merge_list([1]) == [1]

def test_merge_list_two_elements():
    assert merge_list([1, 2]) == [1, 2] 

def test_merge_list_multiple_elements():
    assert merge_list([1, 2, 3, 4]) == [1, 2, 3, 4]

def test_merge_list_empty_list():
    assert merge_list([]) == []

def test_merge_list_nested_lists():
    assert merge_list([[1, 2], [3, 4]]) == [1, 2, 3, 4]

def test_merge_list_odd_length():
    assert merge_list([1, 2, 3]) == [1, 2, 3]

def test_merge_list_even_length():
    assert merge_list([1, 2, 3, 4]) == [1, 2, 3, 4]
