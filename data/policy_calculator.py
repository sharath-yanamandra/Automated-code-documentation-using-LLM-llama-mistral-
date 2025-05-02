"""
Policy Premium Calculator for P&C Insurance

This module provides functions for calculating premiums for different types
of Property & Casualty insurance policies.
"""
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta

# Premium adjustment factors
PREMIUM_FACTORS = {
    "HOME": {
        "base_rate": 500.0,
        "age_factors": {
            "0-5": 1.0,
            "6-15": 1.1,
            "16-30": 1.2,
            "31+": 1.3
        },
        "construction_types": {
            "FRAME": 1.0,
            "MASONRY": 0.9,
            "FIRE_RESISTANT": 0.8
        },
        "location_factors": {
            "LOW_RISK": 0.8,
            "MEDIUM_RISK": 1.0,
            "HIGH_RISK": 1.5,
            "COASTAL": 1.7
        }
    },
    "AUTO": {
        "base_rate": 800.0,
        "vehicle_age_factors": {
            "0-2": 1.3,
            "3-5": 1.0,
            "6-10": 0.9,
            "11+": 0.8
        },
        "driver_age_factors": {
            "16-25": 1.8,
            "26-40": 1.0,
            "41-65": 0.9,
            "66+": 1.1
        },
        "safe_driver_discount": 0.15,
        "accident_surcharge": 0.25
    }
}

class PolicyHolder:
    """
    Represents a policy holder in a P&C insurance context.
    
    This class stores information about a policy holder, including
    personal details and risk factors that affect premium calculations.
    """
    
    def __init__(self, name: str, address: str, dob: datetime, 
                 credit_score: int, claim_history: List[Dict] = None):
        """
        Initialize a new policy holder.
        
        Args:
            name: Full name of the policy holder
            address: Current residence address
            dob: Date of birth
            credit_score: Credit score (300-850)
            claim_history: List of prior claims, each as a dictionary
        """
        self.name = name
        self.address = address
        self.dob = dob
        self.credit_score = max(300, min(850, credit_score))  # Ensure valid range
        self.claim_history = claim_history or []
        self.policies = []
    
    def get_age(self) -> int:
        """
        Calculate the current age of the policy holder.
        
        Returns:
            Age in years
        """
        today = datetime.now()
        age = today.year - self.dob.year
        
        # Adjust if birthday hasn't occurred yet this year
        if today.month < self.dob.month or (today.month == self.dob.month and today.day < self.dob.day):
            age -= 1
            
        return age
    
    def get_risk_factor(self) -> float:
        """
        Calculate a risk factor based on claim history and credit score.
        
        This is used as a multiplier in premium calculations.
        
        Returns:
            Risk factor as a float (higher means higher risk)
        """
        # Base risk starts at 1.0
        risk = 1.0
        
        # Adjust for credit score
        if self.credit_score >= 750:
            risk *= 0.85
        elif self.credit_score >= 650:
            risk *= 0.95
        elif self.credit_score < 600:
            risk *= 1.2
        
        # Adjust for claim history (last 3 years)
        three_years_ago = datetime.now() - timedelta(days=3*365)
        recent_claims = [claim for claim in self.claim_history 
                        if claim.get('date') >= three_years_ago]
        
        if len(recent_claims) > 0:
            risk *= (1.0 + (0.1 * len(recent_claims)))
        
        return risk
    
    def add_policy(self, policy_type: str, policy_details: Dict) -> str:
        """
        Add a new policy for this policy holder.
        
        Args:
            policy_type: Type of policy (e.g., 'HOME', 'AUTO')
            policy_details: Dictionary with policy-specific details
            
        Returns:
            Policy ID
        """
        import uuid
        
        policy_id = str(uuid.uuid4())
        policy = {
            'id': policy_id,
            'type': policy_type,
            'details': policy_details,
            'start_date': datetime.now(),
            'status': 'ACTIVE'
        }
        
        self.policies.append(policy)
        return policy_id


def calculate_home_premium(property_value: float, property_age: int, 
                         construction_type: str, location_risk: str,
                         policy_holder: PolicyHolder) -> float:
    """
    Calculate premium for a homeowner's insurance policy.
    
    Args:
        property_value: Current market value of the property
        property_age: Age of the property in years
        construction_type: Type of construction (FRAME, MASONRY, etc.)
        location_risk: Risk level of the location
        policy_holder: PolicyHolder object for the insured
        
    Returns:
        Annual premium amount
    """
    factors = PREMIUM_FACTORS["HOME"]
    
    # Start with base rate
    premium = factors["base_rate"]
    
    # Adjust for property value (per $100K)
    premium *= (property_value / 100000) * 0.9
    
    # Apply property age factor
    age_factor = 1.0
    if property_age <= 5:
        age_factor = factors["age_factors"]["0-5"]
    elif property_age <= 15:
        age_factor = factors["age_factors"]["6-15"]
    elif property_age <= 30:
        age_factor = factors["age_factors"]["16-30"]
    else:
        age_factor = factors["age_factors"]["31+"]
    
    premium *= age_factor
    
    # Apply construction type factor
    const_factor = factors["construction_types"].get(construction_type, 1.0)
    premium *= const_factor
    
    # Apply location risk factor
    loc_factor = factors["location_factors"].get(location_risk, 1.0)
    premium *= loc_factor
    
    # Apply policy holder's risk factor
    premium *= policy_holder.get_risk_factor()
    
    return round(premium, 2)


def calculate_auto_premium(vehicle_value: float, vehicle_age: int,
                         is_safe_driver: bool, has_accidents: bool,
                         policy_holder: PolicyHolder) -> float:
    """
    Calculate premium for an auto insurance policy.
    
    Args:
        vehicle_value: Current market value of the vehicle
        vehicle_age: Age of the vehicle in years
        is_safe_driver: Whether the driver has safe driver certification
        has_accidents: Whether the driver has had accidents in past 3 years
        policy_holder: PolicyHolder object for the insured
        
    Returns:
        Annual premium amount
    """
    factors = PREMIUM_FACTORS["AUTO"]
    
    # Start with base rate
    premium = factors["base_rate"]
    
    # Adjust for vehicle value
    premium *= (vehicle_value / 20000) * 0.8
    
    # Apply vehicle age factor
    v_age_factor = 1.0
    if vehicle_age <= 2:
        v_age_factor = factors["vehicle_age_factors"]["0-2"]
    elif vehicle_age <= 5:
        v_age_factor = factors["vehicle_age_factors"]["3-5"]
    elif vehicle_age <= 10:
        v_age_factor = factors["vehicle_age_factors"]["6-10"]
    else:
        v_age_factor = factors["vehicle_age_factors"]["11+"]
    
    premium *= v_age_factor
    
    # Apply driver age factor
    driver_age = policy_holder.get_age()
    d_age_factor = 1.0
    if driver_age <= 25:
        d_age_factor = factors["driver_age_factors"]["16-25"]
    elif driver_age <= 40:
        d_age_factor = factors["driver_age_factors"]["26-40"]
    elif driver_age <= 65:
        d_age_factor = factors["driver_age_factors"]["41-65"]
    else:
        d_age_factor = factors["driver_age_factors"]["66+"]
    
    premium *= d_age_factor
    
    # Apply safe driver discount
    if is_safe_driver:
        premium *= (1 - factors["safe_driver_discount"])
    
    # Apply accident surcharge
    if has_accidents:
        premium *= (1 + factors["accident_surcharge"])
    
    # Apply policy holder's risk factor
    premium *= policy_holder.get_risk_factor()
    
    return round(premium, 2)


def format_policy_quote(premium: float, coverage_type: str, 
                      deductible: float, policy_limits: Dict) -> Dict:
    """
    Format a policy quote for presentation to the customer.
    
    Args:
        premium: Calculated annual premium
        coverage_type: Type of coverage
        deductible: Deductible amount
        policy_limits: Dictionary of coverage limits by category
        
    Returns:
        Formatted quote as a dictionary
    """
    # Calculate monthly payment
    monthly_payment = premium / 12
    
    # Format quote dictionary
    quote = {
        'annual_premium': premium,
        'monthly_payment': round(monthly_payment, 2),
        'coverage_type': coverage_type,
        'deductible': deductible,
        'policy_limits': policy_limits,
        'quote_date': datetime.now().strftime('%Y-%m-%d'),
        'valid_until': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    }
    
    return quote


def get_location_risk(zip_code: str) -> str:
    """
    Determine location risk category based on ZIP code.
    
    Args:
        zip_code: US ZIP code
        
    Returns:
        Risk category (LOW_RISK, MEDIUM_RISK, HIGH_RISK, COASTAL)
    """
    # This is a simplified implementation
    # In a real system, this would query a database or API
    
    # Coastal ZIP codes (simplified example)
    coastal_zips = ['33109', '33139', '90210', '90265', '92007', '33480']
    
    # High-risk ZIP codes (simplified example)
    high_risk_zips = ['77001', '77002', '64101', '70112', '95833']
    
    # Low-risk ZIP codes (simplified example)
    low_risk_zips = ['10001', '60601', '75201', '80202', '98101']
    
    if zip_code in coastal_zips:
        return "COASTAL"
    elif zip_code in high_risk_zips:
        return "HIGH_RISK"
    elif zip_code in low_risk_zips:
        return "LOW_RISK"
    else:
        return "MEDIUM_RISK"


# Example usage
if __name__ == "__main__":
    # Create a policy holder
    john_doe = PolicyHolder(
        name="John Doe",
        address="123 Main St, Anytown, USA 12345",
        dob=datetime(1980, 5, 15),
        credit_score=720,
        claim_history=[
            {
                'date': datetime(2022, 3, 10),
                'type': 'AUTO',
                'amount': 2500.0,
                'status': 'PAID'
            }
        ]
    )
    
    # Calculate home insurance premium
    home_premium = calculate_home_premium(
        property_value=350000.0,
        property_age=12,
        construction_type="MASONRY",
        location_risk="MEDIUM_RISK",
        policy_holder=john_doe
    )
    
    # Calculate auto insurance premium
    auto_premium = calculate_auto_premium(
        vehicle_value=25000.0,
        vehicle_age=4,
        is_safe_driver=True,
        has_accidents=True,
        policy_holder=john_doe
    )
    
    # Format quotes
    home_quote = format_policy_quote(
        premium=home_premium,
        coverage_type="HO-3",
        deductible=1000.0,
        policy_limits={
            'dwelling': 350000.0,
            'personal_property': 175000.0,
            'liability': 300000.0,
            'medical': 5000.0
        }
    )
    
    auto_quote = format_policy_quote(
        premium=auto_premium,
        coverage_type="FULL",
        deductible=500.0,
        policy_limits={
            'bodily_injury': 250000.0,
            'property_damage': 100000.0,
            'collision': 25000.0,
            'comprehensive': 25000.0
        }
    )
    
    # Print quotes
    print(f"Home Insurance Quote: ${home_quote['annual_premium']} per year")
    print(f"Auto Insurance Quote: ${auto_quote['annual_premium']} per year")