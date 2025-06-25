from decimal import Decimal, getcontext

def calculate_quotient(dividend, divisor, precision):
    getcontext().prec = precision

    dividend = Decimal(dividend)
    divisor = Decimal(divisor)

    quotient = dividend / divisor

    return quotient

dividend = input("Enter the dividend: ")
divisor = input("Enter the divisor: ")
precision = 500  

quotient = calculate_quotient(dividend, divisor, precision)
print("Quotient:", quotient)
