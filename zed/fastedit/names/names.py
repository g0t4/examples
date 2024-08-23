

def calculate_compound_interest(principal, rate, time, compounds_per_year):
    annual_rate = rate / 100
    total_compounds = compounds_per_year * time
    periodic_rate = annual_rate / compounds_per_year

    interest_factor = (1 + periodic_rate) ** total_compounds
    final_amount = principal * interest_factor
    interest_earned = final_amount - principal

    effective_annual_rate = (interest_factor ** (1 / time) - 1) * 100

    return {
        "final_amount": round(final_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_annual_rate": round(effective_annual_rate, 2)
    }

def calculate_loan_payment(loan_amount, annual_interest_rate, loan_term_years):
    monthly_rate = annual_interest_rate / 100 / 12
    total_payments = loan_term_years * 12

    monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate) ** total_payments) / ((1 + monthly_rate) ** total_payments - 1)
    total_payment_amount = monthly_payment * total_payments

    return round(monthly_payment, 2), round(total_payment_amount, 2)

print(calculate_loan_payment(200_000, 6, 15))
# (1687.71, 303788.46)
