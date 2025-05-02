"""
Mini Insurance Calculator for P&C Insurance

A simplified module for basic P&C insurance calculations.
"""

class InsurancePolicy:
    """
    Represents a basic insurance policy for P&C insurance.
    """
    
    def __init__(self, policy_id, customer_name, premium, coverage_amount):
        """
        Initialize a new insurance policy.
        
        Args:
            policy_id: Unique identifier for the policy
            customer_name: Name of the insured customer
            premium: Annual premium amount
            coverage_amount: Maximum coverage amount
        """
        self.policy_id = policy_id
        self.customer_name = customer_name
        self.premium = premium
        self.coverage_amount = coverage_amount
        self.is_active = True
    
    def calculate_monthly_payment(self):
        """
        Calculate the monthly payment for this policy.
        
        Returns:
            Monthly payment amount
        """
        return self.premium / 12
    
    def cancel_policy(self):
        """
        Cancel this insurance policy.
        """
        self.is_active = False


def calculate_basic_premium(property_value, location_factor, age_factor):
    """
    Calculate a basic insurance premium.
    
    Args:
        property_value: Value of the insured property
        location_factor: Risk factor based on location (1.0 to 2.0)
        age_factor: Risk factor based on age (0.8 to 1.5)
        
    Returns:
        Calculated premium
    """
    base_rate = 500  # Base annual rate
    return base_rate * (property_value / 100000) * location_factor * age_factor


def get_location_factor(zip_code):
    """
    Get the location risk factor based on ZIP code.
    
    Args:
        zip_code: ZIP code of the property
        
    Returns:
        Location risk factor
    """
    # High-risk zip codes
    high_risk = ['33101', '90210', '77001']
    
    # Medium-risk zip codes
    medium_risk = ['60601', '75201', '20001']
    
    if zip_code in high_risk:
        return 1.5
    elif zip_code in medium_risk:
        return 1.2
    else:
        return 1.0


# Sample usage
if __name__ == "__main__":
    # Calculate a premium
    premium = calculate_basic_premium(
        property_value=250000,
        location_factor=get_location_factor("60601"),
        age_factor=1.1
    )
    
    # Create a policy
    policy = InsurancePolicy(
        policy_id="P12345",
        customer_name="Jane Smith",
        premium=premium,
        coverage_amount=250000
    )
    
    # Print information
    print(f"Policy created for {policy.customer_name}")
    print(f"Annual premium: ${policy.premium:.2f}")
    print(f"Monthly payment: ${policy.calculate_monthly_payment():.2f}")