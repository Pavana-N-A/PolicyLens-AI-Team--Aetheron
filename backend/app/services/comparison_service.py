from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Policy, PolicyField

NORMALIZED_FIELD_DEFINITIONS = [
    ("insurer_name", "Actual Underwriter (Risk Carrier)", "Underwriting / Legal Entity"),
    ("distributor_name", "Seller / Distribution Channel", "Bank, Hospital, Employer, Broker, Direct"),
    ("sum_insured", "Sum Insured Coverage", "Coverage schedule or limit"),
    ("premium", "Policy Premium", "Indicated schedule premium"),
    ("room_rent_icu_limit", "Room Rent & ICU Limits", "Per day cap or no capping"),
    ("copay", "Co-payment Requirement", "Mandatory out-of-pocket percentage"),
    ("deductible", "Deductible Amount", "Threshold before insurer pays"),
    ("initial_waiting_period", "Initial Waiting Period", "Standard 30 days exclusion"),
    ("ped_waiting_period", "Pre-Existing Disease (PED) Wait", "24, 36, or 48 continuous months"),
    ("specific_waiting_period", "Specific Ailments Waiting Period", "24 months for hernia, cataract, etc."),
    ("restoration_recharge", "Restoration / Recharge", "Refill of sum insured upon exhaustion"),
    ("no_claim_bonus", "No Claim Bonus (NCB)", "Cumulative bonus per claim-free year"),
    ("maternity_daycare", "Maternity & Day-Care", "Delivery cover, outpatient surgery limits"),
    ("geographical_scope", "Geographical / Territorial Scope", "India-wide, regional, or international"),
    ("cashless_reimbursement", "Cashless & Reimbursement Rules", "Network TPA pre-auth vs non-network direct pay"),
    ("claim_notification_deadline", "Claim Deadlines & Intimation", "Hours for emergency, days for planned intimation")
]

class ComparisonService:
    @staticmethod
    def compare_policies(
        db: Session,
        policy_ids: List[str],
        priority_focus: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Normalizes and compares at least two policies side by side.
        Strictly preserves 'Found in policy' vs 'Not found in uploaded document' states.
        Separates underwriter from distributor.
        """
        policies = db.query(Policy).filter(Policy.id.in_(policy_ids)).all()
        if len(policies) < 2:
            raise ValueError("Select at least two policies for side-by-side comparison.")

        columns: List[Dict[str, Any]] = []

        for pol in policies:
            # Map existing saved policy fields
            fields_by_key = {f.field_key: f for f in pol.fields}
            
            column_fields: Dict[str, Dict[str, Any]] = {}
            for key, label, desc in NORMALIZED_FIELD_DEFINITIONS:
                # Top-level entity fields
                if key == "insurer_name":
                    column_fields[key] = {
                        "label": label,
                        "value": pol.insurer_name or "Unknown Underwriter",
                        "status": "Found in policy" if pol.insurer_name else "Not found in uploaded document",
                        "source_page": 1,
                        "evidence": f"Underwriting insurer: {pol.insurer_name}"
                    }
                elif key == "distributor_name":
                    column_fields[key] = {
                        "label": label,
                        "value": pol.distributor_name or "Direct Insurer",
                        "status": "Found in policy" if pol.distributor_name else "Not found in uploaded document",
                        "source_page": 1,
                        "evidence": f"Distribution channel: {pol.distributor_name}"
                    }
                elif key == "sum_insured":
                    val = pol.sum_insured
                    status = "Found in policy" if val else "Not found in uploaded document"
                    column_fields[key] = {
                        "label": label,
                        "value": val or "Not found in uploaded document",
                        "status": status,
                        "source_page": 1 if val else None,
                        "evidence": f"Sum Insured: {val}" if val else "Document wording does not specify individual schedule sum insured."
                    }
                elif key == "premium":
                    val = pol.premium
                    status = "Found in policy" if val else "Not found in uploaded document"
                    column_fields[key] = {
                        "label": label,
                        "value": val or "Not found in uploaded document",
                        "status": status,
                        "source_page": 1 if val else None,
                        "evidence": f"Premium: {val}" if val else "Document is standard wording terms; schedule premium not attached."
                    }
                elif key in fields_by_key:
                    pf = fields_by_key[key]
                    column_fields[key] = {
                        "label": label,
                        "value": pf.normalized_value or "Not found in uploaded document",
                        "status": pf.status,
                        "source_page": pf.source_page,
                        "evidence": pf.evidence_snippet
                    }
                else:
                    column_fields[key] = {
                        "label": label,
                        "value": "Not found in uploaded document",
                        "status": "Not found in uploaded document",
                        "source_page": None,
                        "evidence": "Clause was not found in the uploaded policy pages."
                    }

            columns.append({
                "policy_id": pol.id,
                "product_name": pol.product_name,
                "insurer_name": pol.insurer_name,
                "distributor_name": pol.distributor_name,
                "fields": column_fields
            })

        # Generate comparative trade-off insights
        tradeoff_summary = ComparisonService._generate_tradeoff_summary(columns, priority_focus)

        return {
            "title": f"Comparison: {' vs '.join([p.product_name for p in policies])}",
            "priority_focus": priority_focus,
            "tradeoff_summary": tradeoff_summary,
            "columns": columns
        }

    @staticmethod
    def _generate_tradeoff_summary(columns: List[Dict[str, Any]], priority_focus: str) -> str:
        """Generates an honest, non-judgmental comparative trade-off explanation"""
        pol1 = columns[0]
        pol2 = columns[1]

        p1_name = pol1["product_name"]
        p2_name = pol2["product_name"]

        p1_ped = pol1["fields"].get("ped_waiting_period", {}).get("value", "Not found")
        p2_ped = pol2["fields"].get("ped_waiting_period", {}).get("value", "Not found")

        p1_room = pol1["fields"].get("room_rent_icu_limit", {}).get("value", "Not found")
        p2_room = pol2["fields"].get("room_rent_icu_limit", {}).get("value", "Not found")

        p1_copay = pol1["fields"].get("copay", {}).get("value", "Not found")
        p2_copay = pol2["fields"].get("copay", {}).get("value", "Not found")

        insights = [
            f"**Distribution Architecture:**\n"
            f"- **{p1_name}**: Underwritten by *{pol1['insurer_name']}* (Distributed via *{pol1['distributor_name']}*).\n"
            f"- **{p2_name}**: Underwritten by *{pol2['insurer_name']}* (Distributed via *{pol2['distributor_name']}*).\n"
            f"*(Notice: The marketing brand may differ from the risk-bearing insurance company).*\n",

            f"**Key Contractual Trade-offs:**\n"
            f"- **PED Waiting Period:** {p1_name} specifies `{p1_ped}`, whereas {p2_name} specifies `{p2_ped}`. A shorter waiting period offers earlier eligibility for conditions diagnosed prior to inception.\n"
            f"- **Room-Rent & ICU Limits:** {p1_name} states `{p1_room}`, while {p2_name} states `{p2_room}`. Room rent caps can trigger proportionate deductions across the entire hospital bill if exceeded.\n"
            f"- **Co-payment:** {p1_name} has `{p1_copay}` vs {p2_name} with `{p2_copay}`. Mandatory co-payments require the insured to bear that percentage of every claim.\n"
        ]

        if priority_focus == "shorter_waiting_period":
            insights.append(
                f"**Based on your priority (Shorter Waiting Periods):** Review the PED and specific disease clauses closely. "
                f"If one policy has a 24-month or 36-month clause versus 48-month, it provides earlier relief for declared conditions."
            )
        elif priority_focus == "lower_copay":
            insights.append(
                f"**Based on your priority (Lowest Out-of-Pocket / Co-pay):** Look at the Co-pay and Deductible rows. "
                f"Policies without mandatory co-pay ensure the insurer covers 100% of approved eligible expenses up to the sum insured."
            )
        elif priority_focus == "higher_coverage":
            insights.append(
                f"**Based on your priority (Comprehensive Coverage):** Check the Restoration/Recharge, Room-Rent limits, and ICU capping. "
                f"No capping on room category avoids proportionate deduction penalties on doctor fees, surgery, and nursing."
            )
        else:
            insights.append(
                f"**Balanced Overview:** Neither policy is universally superior. Your optimal choice depends on whether you value "
                f"shorter waiting periods, unrestricted hospital room categories, or lower annual out-of-pocket deductibles."
            )

        return "\n".join(insights)

comparison_service = ComparisonService()
