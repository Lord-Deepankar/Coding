row = int(input('enter number of rows for your matrix...'))
column = int(input('enter number of column for your matrix...'))

matrix = []
rows= []
for i in range(row):
    for  j in range(column):
        a = int(input(f"enter element for row {i+1} and column {j+1} : "))
        rows.append(a)  
    matrix.append(rows) 
    if i == (row-1):
        break
    else:
        rows.clear()
for i in matrix:
    print(i)
    


