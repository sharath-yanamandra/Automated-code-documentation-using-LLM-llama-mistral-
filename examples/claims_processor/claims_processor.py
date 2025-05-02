"""
Claims Processing Module for P&C Insurance

This module handles the core claims processing functionality for P&C insurance,
including validation, assignment, and settlement calculations.
"""
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
import re
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for claim processing
CLAIM_STATUS_CODES = {
    'NEW': 'Newly reported claim',
    'ASSIGNED': 'Assigned to adjuster',
    'INVESTIGATING': 'Under investigation',
    'PENDING_INFO': 'Pending additional information',
    'APPROVED': 'Claim approved for payment',
    'PARTIAL_APPROVED': 'Claim partially approved',
    'DENIED': 'Claim denied',
    'CLOSED': 'Claim closed',
    'REOPENED': 'Previously closed claim reopened'
}

# Regulatory compliance codes by state
STATE_COMPLIANCE_REQUIREMENTS = {
    'CA': {'time_to_acknowledge': 15, 'time_to_decision': 40, 'documentation_level': 'high'},
    'NY': {'time_to_acknowledge': 7, 'time_to_decision': 30, 'documentation_level': 'high'},
    'TX': {'time_to_acknowledge': 15, 'time_to_decision': 45, 'documentation_level': 'medium'},
    'FL': {'time_to_acknowledge': 14, 'time_to_decision': 90, 'documentation_level': 'high'},
    # Default for other states
    'DEFAULT': {'time_to_acknowledge': 15, 'time_to_decision': 45, 'documentation_level': 'medium'}
}

class Claim:
    """
    Represents a P&C insurance claim with all relevant information
    
    This class stores all data related to a property and casualty insurance claim,
    including policy details, claimant information, damage descriptions, and
    financial calculations.
    """
    
    def __init__(self, policy_number: str, claim_type: str, incident_date: datetime, 
                 reported_date: datetime, description: str, claimant_info: Dict[str, str],
                 estimated_value: float = 0.0):
        """
        Initialize a new claim
        
        Args:
            policy_number: The insurance policy identifier
            claim_type: Type of claim (e.g., 'AUTO', 'HOME', 'COMMERCIAL')
            incident_date: Date and time when the incident occurred
            reported_date: Date and time when the claim was reported
            description: Detailed description of the incident
            claimant_info: Dictionary containing claimant details
            estimated_value: Initial estimate of the claim value
        """
        self.claim_id = str(uuid.uuid4())
        self.policy_number = policy_number
        self.claim_type = claim_type
        self.incident_date = incident_date
        self.reported_date = reported_date
        self.description = description
        self.claimant_info = claimant_info
        self.estimated_value = estimated_value
        self.actual_value = 0.0
        self.status = 'NEW'
        self.assigned_adjuster = None
        self.coverage_verified = False
        self.documents = []
        self.notes = []
        self.state_code = claimant_info.get('state', 'DEFAULT')
        self.last_updated = reported_date
        
        # Add initial note
        self.add_note("Claim created", "SYSTEM")
        
        logger.info(f"New claim created with ID: {self.claim_id}")
    
    def update_status(self, new_status: str, updated_by: str) -> bool:
        """
        Update the claim status
        
        Args:
            new_status: New status code (must be in CLAIM_STATUS_CODES)
            updated_by: ID or name of the user making the change
            
        Returns:
            bool: True if status was updated successfully, False otherwise
        """
        if new_status not in CLAIM_STATUS_CODES:
            logger.error(f"Invalid status code: {new_status}")
            return False
        
        old_status = self.status
        self.status = new_status
        self.last_updated = datetime.now()
        
        # Add status change note
        self.add_note(f"Status changed from {old_status} to {new_status}", updated_by)
        
        logger.info(f"Claim {self.claim_id} status updated to {new_status}")
        return True
    
    def assign_adjuster(self, adjuster_id: str, updated_by: str) -> None:
        """
        Assign an adjuster to the claim
        
        Args:
            adjuster_id: ID of the adjuster
            updated_by: ID or name of the user making the change
        """
        old_adjuster = self.assigned_adjuster
        self.assigned_adjuster = adjuster_id
        self.last_updated = datetime.now()
        
        if old_adjuster:
            note = f"Reassigned from adjuster {old_adjuster} to {adjuster_id}"
        else:
            note = f"Assigned to adjuster {adjuster_id}"
            self.update_status('ASSIGNED', updated_by)
            
        self.add_note(note, updated_by)
        logger.info(f"Claim {self.claim_id} {note}")
    
    def add_document(self, document_name: str, document_type: str, 
                     content_ref: str, uploaded_by: str) -> str:
        """
        Add a document to the claim
        
        Args:
            document_name: Name of the document
            document_type: Type of document (e.g., 'PHOTO', 'REPORT', 'INVOICE')
            content_ref: Reference to document content (e.g., file path, URL)
            uploaded_by: ID or name of the user uploading the document
            
        Returns:
            str: Document ID
        """
        document_id = str(uuid.uuid4())
        document = {
            'id': document_id,
            'name': document_name,
            'type': document_type,
            'content_ref': content_ref,
            'uploaded_by': uploaded_by,
            'upload_date': datetime.now()
        }
        
        self.documents.append(document)
        self.last_updated = document['upload_date']
        
        self.add_note(f"Document added: {document_name} ({document_type})", uploaded_by)
        logger.info(f"Document {document_id} added to claim {self.claim_id}")
        
        return document_id
    
    def add_note(self, content: str, created_by: str) -> str:
        """
        Add a note to the claim
        
        Args:
            content: Note content
            created_by: ID or name of the user creating the note
            
        Returns:
            str: Note ID
        """
        note_id = str(uuid.uuid4())
        note = {
            'id': note_id,
            'content': content,
            'created_by': created_by,
            'timestamp': datetime.now()
        }
        
        self.notes.append(note)
        self.last_updated = note['timestamp']
        
        logger.debug(f"Note added to claim {self.claim_id}: {content[:50]}...")
        return note_id
    
    def update_value(self, new_value: float, is_estimate: bool, updated_by: str) -> None:
        """
        Update the claim value
        
        Args:
            new_value: New claim value
            is_estimate: True if this is an estimate, False if actual
            updated_by: ID or name of the user making the change
        """
        if is_estimate:
            old_value = self.estimated_value
            self.estimated_value = new_value
            value_type = "estimated"
        else:
            old_value = self.actual_value
            self.actual_value = new_value
            value_type = "actual"
        
        self.last_updated = datetime.now()
        
        note = f"{value_type.capitalize()} value updated from ${old_value:.2f} to ${new_value:.2f}"
        self.add_note(note, updated_by)
        logger.info(f"Claim {self.claim_id} {note}")
    
    def verify_coverage(self, is_covered: bool, reason: str, verified_by: str) -> None:
        """
        Verify if the claim is covered by the policy
        
        Args:
            is_covered: True if covered, False if not
            reason: Reason for the coverage decision
            verified_by: ID or name of the user verifying coverage
        """
        self.coverage_verified = True
        self.last_updated = datetime.now()
        
        if is_covered:
            note = f"Coverage verified: {reason}"
        else:
            note = f"Coverage denied: {reason}"
            self.update_status('DENIED', verified_by)
        
        self.add_note(note, verified_by)
        logger.info(f"Claim {self.claim_id} {note}")
    
    def get_time_since_reported(self) -> timedelta:
        """
        Calculate the time elapsed since the claim was reported
        
        Returns:
            timedelta: Time elapsed
        """
        return datetime.now() - self.reported_date
    
    def check_compliance_status(self) -> Dict[str, Union[bool, int, str]]:
        """
        Check if the claim is compliant with state regulations
        
        Returns:
            dict: Compliance status information
        """
        # Get state requirements or default if state not found
        requirements = STATE_COMPLIANCE_REQUIREMENTS.get(
            self.state_code, STATE_COMPLIANCE_REQUIREMENTS['DEFAULT']
        )
        
        time_to_acknowledge = requirements['time_to_acknowledge']
        time_to_decision = requirements['time_to_decision']
        
        # Calculate days since reported
        days_since_reported = (datetime.now() - self.reported_date).days
        
        # Check acknowledgment compliance
        acknowledgment_compliant = self.status != 'NEW' or days_since_reported <= time_to_acknowledge
        
        # Check decision compliance
        decision_statuses = ['APPROVED', 'PARTIAL_APPROVED', 'DENIED', 'CLOSED']
        decision_made = self.status in decision_statuses
        decision_compliant = decision_made or days_since_reported <= time_to_decision
        
        # Check documentation compliance
        doc_level = requirements['documentation_level']
        if doc_level == 'high':
            min_documents = 3
        elif doc_level == 'medium':
            min_documents = 2
        else:
            min_documents = 1
            
        documentation_compliant = len(self.documents) >= min_documents
        
        # Overall compliance
        is_compliant = acknowledgment_compliant and decision_compliant and documentation_compliant
        
        return {
            'is_compliant': is_compliant,
            'acknowledgment_compliant': acknowledgment_compliant,
            'decision_compliant': decision_compliant,
            'documentation_compliant': documentation_compliant,
            'days_since_reported': days_since_reported,
            'required_acknowledgment_days': time_to_acknowledge,
            'required_decision_days': time_to_decision,
            'required_documents': min_documents,
            'actual_documents': len(self.documents),
            'state': self.state_code
        }
    
    def to_dict(self) -> Dict:
        """
        Convert claim to dictionary for serialization
        
        Returns:
            dict: Claim data as dictionary
        """
        return {
            'claim_id': self.claim_id,
            'policy_number': self.policy_number,
            'claim_type': self.claim_type,
            'incident_date': self.incident_date.isoformat(),
            'reported_date': self.reported_date.isoformat(),
            'description': self.description,
            'claimant_info': self.claimant_info,
            'estimated_value': self.estimated_value,
            'actual_value': self.actual_value,
            'status': self.status,
            'status_description': CLAIM_STATUS_CODES.get(self.status, ''),
            'assigned_adjuster': self.assigned_adjuster,
            'coverage_verified': self.coverage_verified,
            'documents': self.documents,
            'notes': self.notes,
            'state_code': self.state_code,
            'last_updated': self.last_updated.isoformat()
        }


class ClaimsProcessor:
    """
    Core claims processing engine for P&C insurance
    
    This class manages claim workflows, calculations, and assignments across
    different lines of insurance business, including auto, property, and
    commercial claims.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the claims processor
        
        Args:
            config: Optional configuration dictionary
        """
        self.claims = {}  # Dictionary to store claims by ID
        self.config = config or {}
        self.auto_assignment = self.config.get('auto_assignment', True)
        self.adjusters = self.config.get('adjusters', {})
        
        # Fraud detection thresholds
        self.fraud_thresholds = self.config.get('fraud_thresholds', {
            'time_to_report': 30,  # Days
            'value_threshold': 50000.0,
            'multiple_claims': 3  # Number of claims in past year
        })
        
        logger.info("Claims processor initialized")
    
    def create_claim(self, policy_number: str, claim_type: str, incident_date: datetime, 
                   reported_date: datetime, description: str, claimant_info: Dict[str, str],
                   estimated_value: float = 0.0) -> Claim:
        """
        Create a new claim in the system
        
        Args:
            policy_number: The insurance policy identifier
            claim_type: Type of claim (e.g., 'AUTO', 'HOME', 'COMMERCIAL')
            incident_date: Date and time when the incident occurred
            reported_date: Date and time when the claim was reported
            description: Detailed description of the incident
            claimant_info: Dictionary containing claimant details
            estimated_value: Initial estimate of the claim value
            
        Returns:
            Claim: The newly created claim object
        """
        # Create new claim
        claim = Claim(
            policy_number=policy_number,
            claim_type=claim_type,
            incident_date=incident_date,
            reported_date=reported_date,
            description=description,
            claimant_info=claimant_info,
            estimated_value=estimated_value
        )
        
        # Store claim
        self.claims[claim.claim_id] = claim
        
        # Automatic assignment if enabled
        if self.auto_assignment:
            self._auto_assign_adjuster(claim)
        
        # Run initial validation
        self._validate_claim(claim)
        
        return claim
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """
        Retrieve a claim by ID
        
        Args:
            claim_id: Unique claim identifier
            
        Returns:
            Claim or None: The claim object if found, None otherwise
        """
        return self.claims.get(claim_id)
    
    def update_claim_status(self, claim_id: str, new_status: str, updated_by: str) -> bool:
        """
        Update the status of a claim
        
        Args:
            claim_id: Unique claim identifier
            new_status: New status code
            updated_by: ID or name of the user making the change
            
        Returns:
            bool: True if successful, False otherwise
        """
        claim = self.get_claim(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return False
        
        return claim.update_status(new_status, updated_by)
    
    def assign_claim(self, claim_id: str, adjuster_id: str, updated_by: str) -> bool:
        """
        Assign a claim to an adjuster
        
        Args:
            claim_id: Unique claim identifier
            adjuster_id: ID of the adjuster
            updated_by: ID or name of the user making the change
            
        Returns:
            bool: True if successful, False otherwise
        """
        claim = self.get_claim(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return False
        
        # Check if adjuster exists
        if adjuster_id not in self.adjusters and adjuster_id != "SYSTEM":
            logger.error(f"Adjuster not found: {adjuster_id}")
            return False
        
        claim.assign_adjuster(adjuster_id, updated_by)
        return True
    
    def calculate_settlement(self, claim_id: str, 
                           damages: Dict[str, float], 
                           deductible: float,
                           coverage_limit: float) -> Dict[str, Union[float, bool, str]]:
        """
        Calculate claim settlement amount
        
        Args:
            claim_id: Unique claim identifier
            damages: Dictionary of damage categories and amounts
            deductible: Policy deductible amount
            coverage_limit: Maximum coverage amount
            
        Returns:
            dict: Settlement calculation results
        """
        claim = self.get_claim(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return {
                'success': False,
                'error': 'Claim not found'
            }
        
        # Calculate total damages
        total_damages = sum(damages.values())
        
        # Apply deductible
        settlement_amount = max(0, total_damages - deductible)
        
        # Apply coverage limit
        settlement_amount = min(settlement_amount, coverage_limit)
        
        # Check if claim is covered
        if not claim.coverage_verified:
            return {
                'success': False,
                'error': 'Coverage not verified',
                'total_damages': total_damages,
                'settlement_amount': 0.0
            }
        
        # Update claim with actual value
        claim.update_value(settlement_amount, False, "SYSTEM")
        
        return {
            'success': True,
            'total_damages': total_damages,
            'deductible_applied': deductible,
            'coverage_limit': coverage_limit,
            'settlement_amount': settlement_amount,
            'fully_covered': total_damages <= (settlement_amount + deductible)
        }
    
    def flag_for_investigation(self, claim_id: str, reason: str, flagged_by: str) -> bool:
        """
        Flag a claim for investigation due to suspected fraud or other issues
        
        Args:
            claim_id: Unique claim identifier
            reason: Reason for investigation
            flagged_by: ID or name of the user flagging the claim
            
        Returns:
            bool: True if successful, False otherwise
        """
        claim = self.get_claim(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return False
        
        claim.update_status('INVESTIGATING', flagged_by)
        claim.add_note(f"Flagged for investigation: {reason}", flagged_by)
        
        # Reassign to specialized fraud investigator if available
        fraud_investigators = [adj_id for adj_id, adj in self.adjusters.items() 
                              if adj.get('specialization') == 'fraud']
        
        if fraud_investigators:
            investigator_id = fraud_investigators[0]
            claim.assign_adjuster(investigator_id, "SYSTEM")
            
        logger.warning(f"Claim {claim_id} flagged for investigation: {reason}")
        return True
    
    def close_claim(self, claim_id: str, resolution: str, closed_by: str) -> bool:
        """
        Close a claim with resolution details
        
        Args:
            claim_id: Unique claim identifier
            resolution: Resolution details
            closed_by: ID or name of the user closing the claim
            
        Returns:
            bool: True if successful, False otherwise
        """
        claim = self.get_claim(claim_id)
        if not claim:
            logger.error(f"Claim not found: {claim_id}")
            return False
        
        claim.update_status('CLOSED', closed_by)
        claim.add_note(f"Claim closed: {resolution}", closed_by)
        
        logger.info(f"Claim {claim_id} closed: {resolution}")
        return True
    
    def get_claims_by_status(self, status: str) -> List[Claim]:
        """
        Get all claims with a specific status
        
        Args:
            status: Status code to filter by
            
        Returns:
            list: List of matching claims
        """
        return [claim for claim in self.claims.values() if claim.status == status]
    
    def get_claims_by_adjuster(self, adjuster_id: str) -> List[Claim]:
        """
        Get all claims assigned to a specific adjuster
        
        Args:
            adjuster_id: ID of the adjuster
            
        Returns:
            list: List of matching claims
        """
        return [claim for claim in self.claims.values() 
                if claim.assigned_adjuster == adjuster_id]
    
    def get_claims_by_policy(self, policy_number: str) -> List[Claim]:
        """
        Get all claims for a specific policy
        
        Args:
            policy_number: Policy identifier
            
        Returns:
            list: List of matching claims
        """
        return [claim for claim in self.claims.values() 
                if claim.policy_number == policy_number]
    
    def get_compliance_report(self) -> Dict[str, Dict]:
        """
        Generate a compliance report for all claims
        
        Returns:
            dict: Compliance report with statistics by state
        """
        report = {}
        
        for claim in self.claims.values():
            state = claim.state_code
            if state not in report:
                report[state] = {
                    'total_claims': 0,
                    'compliant_claims': 0,
                    'non_compliant_claims': 0,
                    'compliance_rate': 0.0
                }
            
            compliance_status = claim.check_compliance_status()
            report[state]['total_claims'] += 1
            
            if compliance_status['is_compliant']:
                report[state]['compliant_claims'] += 1
            else:
                report[state]['non_compliant_claims'] += 1
        
        # Calculate compliance rates
        for state, data in report.items():
            if data['total_claims'] > 0:
                data['compliance_rate'] = (data['compliant_claims'] / data['total_claims']) * 100
        
        return report
    
    def _auto_assign_adjuster(self, claim: Claim) -> None:
        """
        Automatically assign an adjuster to a claim based on specialization and workload
        
        Args:
            claim: Claim object to assign
        """
        if not self.adjusters:
            logger.warning("No adjusters available for assignment")
            return
        
        # Filter adjusters by claim type specialization
        specialized_adjusters = {adj_id: adj for adj_id, adj in self.adjusters.items()
                               if claim.claim_type in adj.get('specializations', [])}
        
        if not specialized_adjusters:
            # Fallback to any adjuster if no specialists found
            logger.warning(f"No specialized adjusters found for {claim.claim_type}")
            specialized_adjusters = self.adjusters
        
        # Find adjuster with lowest workload
        adjuster_workloads = {}
        for adj_id in specialized_adjusters:
            adjuster_claims = self.get_claims_by_adjuster(adj_id)
            workload = len(adjuster_claims)
            adjuster_workloads[adj_id] = workload
        
        if not adjuster_workloads:
            logger.warning("No adjusters available for assignment")
            return
        
        # Get adjuster with lowest workload
        assigned_adjuster = min(adjuster_workloads, key=adjuster_workloads.get)
        claim.assign_adjuster(assigned_adjuster, "SYSTEM")
        
        logger.info(f"Claim {claim.claim_id} auto-assigned to adjuster {assigned_adjuster}")
    
    def _validate_claim(self, claim: Claim) -> None:
        """
        Perform initial validation checks on a claim
        
        Args:
            claim: Claim object to validate
        """
        # Check reporting time
        days_to_report = (claim.reported_date - claim.incident_date).days
        if days_to_report > self.fraud_thresholds['time_to_report']:
            note = f"Late reporting detected: {days_to_report} days after incident"
            claim.add_note(note, "SYSTEM")
            logger.warning(f"Claim {claim.claim_id}: {note}")
        
        # Check for high value
        if claim.estimated_value > self.fraud_thresholds['value_threshold']:
            note = f"High value claim detected: ${claim.estimated_value:.2f}"
            claim.add_note(note, "SYSTEM")
            logger.warning(f"Claim {claim.claim_id}: {note}")
        
        # Check for multiple claims on same policy
        policy_claims = self.get_claims_by_policy(claim.policy_number)
        if len(policy_claims) >= self.fraud_thresholds['multiple_claims']:
            note = f"Multiple claims detected for policy: {len(policy_claims)} claims"
            claim.add_note(note, "SYSTEM")
            logger.warning(f"Claim {claim.claim_id}: {note}")
            
            # Flag for investigation if too many claims
            if len(policy_claims) > self.fraud_thresholds['multiple_claims']:
                self.flag_for_investigation(
                    claim.claim_id,
                    f"Excessive claims on policy: {len(policy_claims)} in the past year",
                    "SYSTEM"
                )


def validate_policy_number(policy_number: str) -> bool:
    """
    Validate a policy number format
    
    Standard P&C policy numbers follow the format: 
    [2 letter state code]-[2 digit year]-[6 digit policy id]-[1 letter type]
    Example: CA-22-123456-H for a California homeowners policy from 2022
    
    Args:
        policy_number: Policy number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[A-Z]{2}-\d{2}-\d{6}-[AHCFM]'
                
    return bool(re.match(pattern, policy_number))


def calculate_depreciation(item_value: float, age_years: float, category: str) -> float:
    """
    Calculate depreciation for a claim item based on age and category
    
    Args:
        item_value: Original value of the item
        age_years: Age of the item in years
        category: Item category (e.g., 'ELECTRONICS', 'FURNITURE', 'VEHICLE')
        
    Returns:
        float: Depreciated value
    """
    # Annual depreciation rates by category
    depreciation_rates = {
        'ELECTRONICS': 0.2,   # 20% per year
        'FURNITURE': 0.1,     # 10% per year
        'VEHICLE': 0.15,      # 15% per year
        'CLOTHING': 0.25,     # 25% per year
        'JEWELRY': 0.05,      # 5% per year
        'BUILDING': 0.02,     # 2% per year
        'TOOLS': 0.1,         # 10% per year
        'APPLIANCES': 0.12,   # 12% per year
        'DEFAULT': 0.1        # 10% per year default
    }
    
    # Get rate for category or use default
    rate = depreciation_rates.get(category, depreciation_rates['DEFAULT'])
    
    # Calculate depreciation
    depreciation = item_value * rate * age_years
    
    # Ensure value doesn't go below salvage value (20% of original for most items)
    min_value = item_value * 0.2
    return max(item_value - depreciation, min_value)


def calculate_flood_risk_score(property_data: Dict) -> Tuple[int, str]:
    """
    Calculate flood risk score for a property based on location and characteristics
    
    Used in underwriting and claims assessment for flood-prone properties.
    
    Args:
        property_data: Dictionary containing property information
            Required keys:
            - elevation: Elevation above sea level in feet
            - distance_to_water: Distance to nearest body of water in miles
            - flood_zone: FEMA flood zone code (A, AE, X, etc.)
            - prior_claims: Number of prior flood claims
            
    Returns:
        tuple: (risk_score, risk_category)
            risk_score: 0-100 numeric score (higher = higher risk)
            risk_category: 'LOW', 'MODERATE', 'HIGH', or 'EXTREME'
    """
    score = 0
    
    # Elevation factor (lower elevation = higher risk)
    elevation = property_data.get('elevation', 100)
    if elevation < 10:
        score += 40
    elif elevation < 50:
        score += 20
    elif elevation < 100:
        score += 10
    
    # Distance to water factor
    distance = property_data.get('distance_to_water', 10)
    if distance < 0.1:
        score += 30
    elif distance < 0.5:
        score += 20
    elif distance < 1:
        score += 10
    
    # Flood zone factor
    flood_zone = property_data.get('flood_zone', 'X')
    if flood_zone in ['A', 'AE', 'AH', 'AO']:
        score += 25
    elif flood_zone in ['B', 'X500']:
        score += 10
    
    # Prior claims factor
    prior_claims = property_data.get('prior_claims', 0)
    score += min(prior_claims * 5, 20)  # Cap at 20 points
    
    # Determine risk category
    if score >= 70:
        category = 'EXTREME'
    elif score >= 40:
        category = 'HIGH'
    elif score >= 20:
        category = 'MODERATE'
    else:
        category = 'LOW'
    
    return score, category


def estimate_business_interruption(monthly_revenue: float, 
                                 expected_downtime_days: int,
                                 fixed_expenses_pct: float = 0.3) -> float:
    """
    Calculate estimated business interruption loss for commercial claims
    
    Args:
        monthly_revenue: Average monthly revenue of the business
        expected_downtime_days: Expected number of days of business interruption
        fixed_expenses_pct: Percentage of revenue that goes to fixed expenses
        
    Returns:
        float: Estimated business interruption loss
    """
    # Calculate daily revenue
    daily_revenue = monthly_revenue / 30
    
    # Calculate loss based on revenue and fixed expenses
    total_revenue_loss = daily_revenue * expected_downtime_days
    fixed_expenses = total_revenue_loss * fixed_expenses_pct
    
    # Business interruption covers lost profit plus fixed expenses
    # Assuming profit margin is consistent, profit would be:
    profit_margin = 0.15  # Assumed 15% profit margin
    lost_profit = total_revenue_loss * profit_margin
    
    # Total business interruption loss
    total_loss = lost_profit + fixed_expenses
    
    return total_loss


# Example usage of the module
if __name__ == "__main__":
    # Initialize claims processor
    processor = ClaimsProcessor({
        'auto_assignment': True,
        'adjusters': {
            'ADJ001': {
                'name': 'John Smith',
                'specializations': ['AUTO', 'HOME'],
                'states': ['CA', 'NV', 'AZ']
            },
            'ADJ002': {
                'name': 'Sarah Johnson',
                'specializations': ['COMMERCIAL', 'LIABILITY'],
                'states': ['CA', 'OR', 'WA']
            },
            'ADJ003': {
                'name': 'Michael Brown',
                'specializations': ['HOME', 'FLOOD'],
                'states': ['FL', 'GA', 'SC']
            }
        },
        'fraud_thresholds': {
            'time_to_report': 30,
            'value_threshold': 50000.0,
            'multiple_claims': 3
        }
    })
    
    # Create a sample claim
    claim = processor.create_claim(
        policy_number="CA-23-123456-H",
        claim_type="HOME",
        incident_date=datetime(2023, 6, 15, 8, 30),
        reported_date=datetime(2023, 6, 16, 9, 15),
        description="Water damage due to broken pipe in upstairs bathroom. Affected ceiling, walls, and flooring in downstairs living room.",
        claimant_info={
            'name': 'Robert Johnson',
            'phone': '555-123-4567',
            'email': 'robert.johnson@example.com',
            'address': '123 Main St, Sacramento, CA 95814',
            'state': 'CA'
        },
        estimated_value=12500.00
    )
    
    # Print claim information
    print(f"Created claim: {claim.claim_id}")
    print(f"Status: {claim.status} - {CLAIM_STATUS_CODES[claim.status]}")
    print(f"Assigned to: {claim.assigned_adjuster}")
    
    # Add some documents
    claim.add_document(
        "Water_Damage_Photo_1.jpg", 
        "PHOTO", 
        "/storage/photos/water_damage_1.jpg",
        "CLAIMANT"
    )
    
    claim.add_document(
        "Plumber_Invoice.pdf", 
        "INVOICE", 
        "/storage/documents/plumber_invoice.pdf",
        "CLAIMANT"
    )
    
    # Verify coverage
    claim.verify_coverage(
        True,
        "Policy covers water damage from internal plumbing issues",
        "ADJ001"
    )
    
    # Calculate settlement
    damages = {
        'structural': 8000.00,
        'personal_property': 2500.00,
        'additional_living_expenses': 1500.00
    }
    
    settlement = processor.calculate_settlement(
        claim.claim_id,
        damages,
        deductible=1000.00,
        coverage_limit=50000.00
    )
    
    # Print settlement information
    print("\nSettlement Calculation:")
    print(f"Total Damages: ${settlement['total_damages']:.2f}")
    print(f"Deductible Applied: ${settlement['deductible_applied']:.2f}")
    print(f"Coverage Limit: ${settlement['coverage_limit']:.2f}")
    print(f"Settlement Amount: ${settlement['settlement_amount']:.2f}")
    print(f"Fully Covered: {'Yes' if settlement['fully_covered'] else 'No'}")
    
    # Close the claim
    processor.close_claim(
        claim.claim_id,
        "Claim settled and payment issued to policyholder",
        "ADJ001"
    )
    
    # Check compliance
    compliance = claim.check_compliance_status()
    print("\nCompliance Status:")
    print(f"Compliant: {'Yes' if compliance['is_compliant'] else 'No'}")
    print(f"State: {compliance['state']}")
    print(f"Days Since Reported: {compliance['days_since_reported']}")