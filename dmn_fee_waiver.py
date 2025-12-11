"""
DMN Rule Engine for Credit Card Fee Waiver Calculation

Implements decision rules for determining credit card fee waivers based on:
- Account balance
- Transaction count
- Account tenure
- Account status
- Special conditions
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


class WaiverType(Enum):
    """Types of fee waivers available"""
    FULL_WAIVER = "FULL_WAIVER"
    PARTIAL_WAIVER = "PARTIAL_WAIVER"
    PREMIUM_WAIVER = "PREMIUM_WAIVER"
    NO_WAIVER = "NO_WAIVER"


@dataclass
class FeeWaiverRequest:
    """Request for fee waiver evaluation"""
    account_id: str
    account_balance: float
    monthly_transaction_count: int
    account_tenure_months: int
    account_status: str  # ACTIVE, FROZEN, CLOSED
    is_premium_customer: bool = False
    is_new_customer: bool = False  # First 3 months
    annual_fee: float = 0.0
    monthly_maintenance_fee: float = 0.0


@dataclass
class FeeWaiverDecision:
    """Decision output"""
    account_id: str
    waiver_type: str
    annual_fee_waived: float
    monthly_fee_waived: float
    total_waived: float
    reason: str
    rule_applied: str
    eligible: bool


class FeeWaiverDMN:
    """DMN Rule Engine for Fee Waivers"""
    
    # Decision rules configuration
    RULES = {
        "new_customer_rule": {
            "description": "New customers (first 3 months) get full annual fee waiver",
            "condition": lambda req: req.is_new_customer,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.FULL_WAIVER.value,
                annual_fee_waived=req.annual_fee,
                monthly_fee_waived=0,
                total_waived=req.annual_fee,
                reason="New customer promotion",
                rule_applied="new_customer_rule",
                eligible=True
            )
        },
        "premium_customer_rule": {
            "description": "Premium customers with 100k+ balance get full fee waiver",
            "condition": lambda req: req.is_premium_customer and req.account_balance >= 100000,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.FULL_WAIVER.value,
                annual_fee_waived=req.annual_fee,
                monthly_fee_waived=req.monthly_maintenance_fee,
                total_waived=req.annual_fee + (req.monthly_maintenance_fee * 12),
                reason="Premium customer status with high balance",
                rule_applied="premium_customer_rule",
                eligible=True
            )
        },
        "premium_waiver_rule": {
            "description": "Premium waiver: Premium customers with 50k-100k balance get 75% annual fee waiver + free extra services",
            "condition": lambda req: req.is_premium_customer and req.account_balance >= 50000 and req.account_balance < 100000,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.PREMIUM_WAIVER.value,
                annual_fee_waived=req.annual_fee * 0.75,
                monthly_fee_waived=req.monthly_maintenance_fee,
                total_waived=req.annual_fee * 0.75 + (req.monthly_maintenance_fee * 12),
                reason="Premium waiver: 75% annual fee + free monthly maintenance for premium customer",
                rule_applied="premium_waiver_rule",
                eligible=True
            )
        },
        "high_balance_rule": {
            "description": "Accounts with 50k-100k balance get 50% annual fee waiver",
            "condition": lambda req: req.account_balance >= 50000 and req.account_balance < 100000,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.PARTIAL_WAIVER.value,
                annual_fee_waived=req.annual_fee * 0.5,
                monthly_fee_waived=0,
                total_waived=req.annual_fee * 0.5,
                reason="High balance threshold met (50k-100k)",
                rule_applied="high_balance_rule",
                eligible=True
            )
        },
        "active_user_rule": {
            "description": "Accounts with 20+ monthly transactions get 25% annual fee waiver",
            "condition": lambda req: req.monthly_transaction_count >= 20 and req.account_balance >= 10000,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.PARTIAL_WAIVER.value,
                annual_fee_waived=req.annual_fee * 0.25,
                monthly_fee_waived=0,
                total_waived=req.annual_fee * 0.25,
                reason="High transaction activity (20+ monthly transactions)",
                rule_applied="active_user_rule",
                eligible=True
            )
        },
        "long_tenure_rule": {
            "description": "Accounts with 5+ years tenure get 20% annual fee waiver",
            "condition": lambda req: req.account_tenure_months >= 60 and req.account_status == "ACTIVE",
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.PARTIAL_WAIVER.value,
                annual_fee_waived=req.annual_fee * 0.20,
                monthly_fee_waived=0,
                total_waived=req.annual_fee * 0.20,
                reason="Long account tenure (5+ years)",
                rule_applied="long_tenure_rule",
                eligible=True
            )
        },
        "inactive_account_rule": {
            "description": "Inactive/frozen accounts are not eligible for waivers",
            "condition": lambda req: req.account_status in ["FROZEN", "CLOSED"],
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.NO_WAIVER.value,
                annual_fee_waived=0,
                monthly_fee_waived=0,
                total_waived=0,
                reason="Account not in active status",
                rule_applied="inactive_account_rule",
                eligible=False
            )
        },
        "default_rule": {
            "description": "Default: no waiver",
            "condition": lambda req: True,
            "decision": lambda req: FeeWaiverDecision(
                account_id=req.account_id,
                waiver_type=WaiverType.NO_WAIVER.value,
                annual_fee_waived=0,
                monthly_fee_waived=0,
                total_waived=0,
                reason="No eligibility criteria met",
                rule_applied="default_rule",
                eligible=False
            )
        }
    }
    
    @classmethod
    def evaluate(cls, request: FeeWaiverRequest) -> FeeWaiverDecision:
        """
        Evaluate fee waiver eligibility using DMN rules (hit policy: first match)
        Rules are evaluated in order; first match wins.
        """
        # Priority order matters: evaluate specific rules first
        rule_order = [
            "inactive_account_rule",  # Check status first
            "new_customer_rule",      # New customer promo
            "premium_customer_rule",  # Premium with 100k+
            "premium_waiver_rule",    # Premium with 50k-100k (new rule)
            "high_balance_rule",      # Balance thresholds
            "active_user_rule",       # Transaction activity
            "long_tenure_rule",       # Account tenure
            "default_rule"            # Default (no waiver)
        ]
        
        for rule_name in rule_order:
            rule = cls.RULES[rule_name]
            if rule["condition"](request):
                return rule["decision"](request)
        
        # Should never reach here due to default_rule
        return cls.RULES["default_rule"]["decision"](request)
    
    @classmethod
    def evaluate_batch(cls, requests: List[FeeWaiverRequest]) -> List[Dict[str, Any]]:
        """Evaluate multiple accounts"""
        results = []
        for req in requests:
            decision = cls.evaluate(req)
            results.append(asdict(decision))
        return results


def demo_dmn_rules():
    """Demonstrate DMN rule engine with sample accounts"""
    
    print("\n" + "="*80)
    print("CREDIT CARD FEE WAIVER DMN RULE ENGINE - DEMO")
    print("="*80)
    
    # Sample test cases
    test_cases = [
        FeeWaiverRequest(
            account_id="A00001",
            account_balance=150000,
            monthly_transaction_count=35,
            account_tenure_months=24,
            account_status="ACTIVE",
            is_premium_customer=True,
            is_new_customer=False,
            annual_fee=299.0,
            monthly_maintenance_fee=5.0
        ),
        FeeWaiverRequest(
            account_id="A00002",
            account_balance=15000,
            monthly_transaction_count=8,
            account_tenure_months=2,
            account_status="ACTIVE",
            is_premium_customer=False,
            is_new_customer=True,
            annual_fee=99.0,
            monthly_maintenance_fee=0.0
        ),
        FeeWaiverRequest(
            account_id="A00003",
            account_balance=75000,
            monthly_transaction_count=25,
            account_tenure_months=72,
            account_status="ACTIVE",
            is_premium_customer=True,  # Premium with 50k-100k balance for premium_waiver_rule
            is_new_customer=False,
            annual_fee=199.0,
            monthly_maintenance_fee=10.0
        ),
        FeeWaiverRequest(
            account_id="A00004",
            account_balance=5000,
            monthly_transaction_count=3,
            account_tenure_months=6,
            account_status="FROZEN",
            is_premium_customer=False,
            is_new_customer=False,
            annual_fee=0.0,
            monthly_maintenance_fee=0.0
        ),
        FeeWaiverRequest(
            account_id="A00005",
            account_balance=30000,
            monthly_transaction_count=22,
            account_tenure_months=18,
            account_status="ACTIVE",
            is_premium_customer=False,
            is_new_customer=False,
            annual_fee=99.0,
            monthly_maintenance_fee=0.0
        ),
    ]
    
    print("\n📋 TESTING 5 ACCOUNTS:\n")
    
    for i, req in enumerate(test_cases, 1):
        decision = FeeWaiverDMN.evaluate(req)
        
        print(f"\n--- Account {i}: {decision.account_id} ---")
        print(f"Balance:              ${req.account_balance:,.2f}")
        print(f"Monthly Transactions: {req.monthly_transaction_count}")
        print(f"Tenure (months):      {req.account_tenure_months}")
        print(f"Status:               {req.account_status}")
        print(f"Premium Customer:     {req.is_premium_customer}")
        print(f"New Customer:         {req.is_new_customer}")
        print(f"\n✓ Decision:")
        print(f"  Waiver Type:        {decision.waiver_type}")
        print(f"  Annual Fee Waived:  ${decision.annual_fee_waived:.2f}")
        print(f"  Monthly Fee Waived: ${decision.monthly_fee_waived:.2f}")
        print(f"  Total Waived:       ${decision.total_waived:.2f}")
        print(f"  Reason:             {decision.reason}")
        print(f"  Rule Applied:       {decision.rule_applied}")
        print(f"  Eligible:           {decision.eligible}")
    
    print("\n" + "="*80)
    print("DMN RULE EVALUATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    demo_dmn_rules()
