def calculate_mortgage(loan_amount, annual_interest_rate, loan_years):
    monthly_interest_rate = annual_interest_rate / 100 / 12
    total_payments = loan_years * 12

    monthly_payment = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** total_payments) / ((1 + monthly_interest_rate) ** total_payments - 1)
    total_amount = monthly_payment * total_payments

    return round(monthly_payment, 2), round(total_amount, 2)

print(calculate_mortgage(200_000, 6, 15))
