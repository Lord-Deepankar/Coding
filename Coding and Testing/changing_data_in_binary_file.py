import pickle
fon  = open('test.dat' , 'wb')
try :
    while True:
        roll = int(input('enter roll no...'))
        name = input('enter name..')
        marks = int(input('enter marks'))
        dat = [roll,name,marks]
        pickle.dump(dat,fon)
except Exception:
    fon.close()
    
font = open('test.dat','rb')
try :
    while True:
        con = pickle.load(font)
        print(con)
except Exception:
    font.close()
    
t = open('test.dat' , 'rb')
rol = int(input('enter roll...'))
new_name = input('enter name...')
try:
    while True:
        data = pickle.load(t)
        if data[0]==rol :
            data[1]=new_name
        print(data)
except Exception :
    t.close()
