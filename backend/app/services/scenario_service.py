from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Policy, PolicyClause, PolicyField
from app.services.retrieval_service import retrieval_service

class ScenarioService:
    @staticmethod
    def analyze_disease_scenario(
        db: Session,
        policy_id: str,
        policy_start_date: Optional[str],
        first_diagnosis_date: Optional[str],
        disease_name: Optional[str] = "",
        continuous_renewals: str = "yes",
        pre_existing_or_treated_prior: str = "no",
        treatment_state: Optional[str] = None,
        hospital_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes a disease scenario according to Indian insurance jurisprudence:
        A disease first diagnosed AFTER purchase is NOT a Pre-Existing Disease (PED),
        but is NOT automatically covered. Checks initial wait, specific ailment wait,
        exclusions, and continuity.
        """
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")

        # 1. Retrieve relevant clauses from database
        search_terms = f"waiting period pre-existing exclusion {disease_name or ''}"
        relevant_matches = retrieval_service.search_policy_clauses(
            db=db,
            query=search_terms,
            policy_ids=[policy_id],
            limit=4
        )

        # 2. Analyze timeline if dates provided
        timeline_analysis = ""
        days_between = None
        months_between = None
        
        if policy_start_date and first_diagnosis_date:
            try:
                start_dt = datetime.strptime(policy_start_date.strip()[:10], "%Y-%m-%d")
                diag_dt = datetime.strptime(first_diagnosis_date.strip()[:10], "%Y-%m-%d")
                delta = diag_dt - start_dt
                days_between = delta.days
                months_between = round(days_between / 30.4, 1)

                if days_between < 0:
                    timeline_analysis = (
                        f"**Inception Chronology:** The diagnosis date ({first_diagnosis_date}) occurred {abs(days_between)} days "
                        f"BEFORE the policy start date ({policy_start_date}). By contract definition, this condition is classified as a "
                        f"**Pre-Existing Disease (PED)** and will be subject to the policy's PED waiting period (typically 24 to 48 months), "
                        f"provided it was truthfully disclosed in the proposal form."
                    )
                elif days_between <= 30:
                    timeline_analysis = (
                        f"**Initial Waiting Period Conflict:** The condition was first diagnosed within {days_between} days of policy start. "
                        f"Standard Indian health insurance policies apply a mandatory 30-day initial waiting period for all illnesses "
                        f"(except accidental bodily injury). Treatments diagnosed or commenced during the first 30 days are generally excluded."
                    )
                else:
                    timeline_analysis = (
                        f"**Post-Purchase Diagnosis:** The condition was first diagnosed {days_between} days (~{months_between} months) "
                        f"AFTER policy inception. Because the diagnosis and medical advice arose after the policy commencement date, "
                        f"it does **NOT** meet the legal definition of a Pre-Existing Disease (PED) as defined by IRDAI regulations. "
                        f"However, it is not automatically covered without verifying specific waiting periods and general exclusions."
                    )
            except Exception:
                timeline_analysis = "Dates provided could not be parsed into a calendar timeline. Please check format (YYYY-MM-DD)."
        else:
            timeline_analysis = (
                "Exact policy commencement or first diagnosis date was not entered. "
                "Timeline calculation requires both dates to calculate elapsed months against waiting periods."
            )

        # 3. Assessment of PED status
        if pre_existing_or_treated_prior.lower() == "yes" or (days_between is not None and days_between < 0):
            ped_status = "Condition is or may be classified as Pre-Existing (Subject to PED Waiting Period)"
        else:
            ped_status = "Condition was first diagnosed post-purchase; NOT a Pre-Existing Disease (PED)"

        # 4. Formulate plain English explanation
        plain_explanation = (
            f"### Crucial Legal and Contractual Principles:\n"
            f"1. **Pre-Existing Disease (PED) Distinction:** Under IRDAI guidelines, a condition is considered pre-existing only if signs, symptoms, diagnosis, or medical treatment occurred within the 36/48 months *prior* to the effective date of the first policy.\n"
            f"2. **Not Automatically Covered:** Even if an illness is diagnosed 2 or 3 years after purchase, coverage is NOT unconditional. The insurer will inspect:\n"
            f"   - **Continuous Renewals:** Has the policy been renewed continuously without any break in cover? (User indicated: `{continuous_renewals.upper()}`).\n"
            f"   - **Specific Ailment Waiting Periods:** Many policies impose a 24-month waiting period for specific ailments (e.g. hernia, hydrocele, cataract, benign prostatic hypertrophy, joint replacements, ENT disorders, stones) irrespective of whether they were pre-existing.\n"
            f"   - **Initial Disclosure Integrity:** Did the insured answer all medical history questions in the proposal form accurately under the doctrine of *Uberrima Fides* (Utmost Good Faith)?\n"
            f"   - **Permanent Exclusions:** Does the condition fall under standard policy exclusions (e.g. experimental treatments, cosmetic surgery, non-allopathic unapproved procedures)?\n"
        )

        missing_facts = [
            "Exact wording of the Specific Ailments Waiting Period clause in your policy schedule",
            "Discharge summary and first consultation doctor's notes (to prove exact date of onset)",
            "Continuity certificate / renewal receipts confirming no break in coverage",
            "Proposal form disclosure copy submitted at initial purchase"
        ]

        suggested_questions = [
            f"Is '{disease_name or 'this condition'}' listed under Section 4 ('Specific Waiting Periods') or Section 5 ('Permanent Exclusions')?",
            "What documentation does the TPA require to establish the exact first onset date of this condition?",
            "Are there sub-limits, room-rent capping, or mandatory co-payments applicable to this surgical procedure?",
            "If planned in advance, what is the exact pre-authorisation turnaround time for cashless admission?"
        ]

        clauses_summary = []
        for m in relevant_matches:
            clauses_summary.append({
                "policy_name": m.get("policy_name"),
                "page_number": m.get("page_number"),
                "snippet": m.get("snippet")
            })

        return {
            "policy_id": policy_id,
            "disease_name": disease_name or "Unspecified condition",
            "plain_explanation": plain_explanation,
            "is_ped_assessment": ped_status,
            "waiting_period_analysis": timeline_analysis,
            "missing_facts_to_verify": missing_facts,
            "suggested_questions": suggested_questions,
            "relevant_clauses": clauses_summary,
            "disclaimer": (
                "IMPORTANT: PolicyLens provides educational decision support and clause explanation only. "
                "This is NOT a formal claim approval or rejection. Claim admissibility is subject to hospital records, "
                "policy schedule terms, and adjudication by the underwriter and licensed TPA."
            )
        }

    @staticmethod
    def check_geographical_scope(
        db: Session,
        policy_id: str,
        policy_state: str = "Karnataka",
        treatment_state: str = "Maharashtra",
        hospital_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explains territorial/geographical scope vs cashless network empanelment:
        Treatment in another Indian state and cashless hospital access are separate questions.
        """
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")

        # Retrieve geographical and claim clauses
        geo_matches = retrieval_service.search_policy_clauses(
            db=db,
            query="geographical territorial scope cashless reimbursement network hospital",
            policy_ids=[policy_id],
            limit=4
        )

        analysis = (
            f"### Geographical Scope vs Cashless Network Availability:\n"
            f"You bought this policy in **{policy_state}** and are seeking medical treatment in **{treatment_state}**.\n\n"
            f"**1. Territorial / Geographical Coverage (Contractual Validity):**\n"
            f"- Standard retail health insurance policies in India provide **Pan-India (India-wide)** geographical coverage unless explicitly endorsed with a zonal co-payment or state restriction.\n"
            f"- If the policy covers treatment anywhere in India, medically necessary hospitalization in {treatment_state} is legally eligible under the contract.\n\n"
            f"**2. Cashless vs Reimbursement Claim Procedure (Hospital Network):**\n"
            f"- **Two Separate Checks:** Whether your policy is valid in {treatment_state} and whether a specific hospital ({hospital_name or 'the treating facility'}) offers **Cashless Access** are two entirely different questions.\n"
            f"- **Network Hospital:** If the hospital is empanelled with your insurer/TPA in {treatment_state}, cashless admission is possible via pre-authorisation.\n"
            f"- **Non-Network Hospital:** If the hospital is NOT in the network, **treatment is still covered under the reimbursement route**, provided it is an IRDAI-registered hospital (minimum 10-15 beds, qualified medical staff, OT, etc.). The patient pays the hospital directly upon discharge and submits claims for reimbursement."
        )

        cashless_vs_reimbursement = (
            "**Cashless Pathway:**\n"
            "- Submit pre-authorisation request at the hospital's TPA/Insurance desk 48-72 hours prior to planned admission (or within 24 hours for emergency).\n"
            "- Insurer issues initial approval letter specifying sanctioned amount.\n\n"
            "**Reimbursement Pathway (if hospital is non-network):**\n"
            "- Intimate insurer/TPA within 24 hours of emergency admission or prior to planned hospitalization.\n"
            "- Collect original discharge card, itemized pharmacy bills, diagnostic reports, and payment receipts.\n"
            "- Submit claim packet within 15–30 days of discharge."
        )

        action_checklist = [
            f"Check if your policy schedule contains a 'Zonal Premium / Co-pay' clause (e.g. Zone A vs Zone B/C co-pay).",
            f"Verify if {hospital_name or 'the hospital'} is currently empanelled on the active TPA network list.",
            "If visiting a non-network hospital, ensure the hospital meets policy definition (registered, bed count, licensed doctors).",
            "Send formal claim intimation notice to the insurer via email or toll-free before or within 24 hours of admission."
        ]

        clauses_summary = []
        for m in geo_matches:
            clauses_summary.append({
                "policy_name": m.get("policy_name"),
                "page_number": m.get("page_number"),
                "snippet": m.get("snippet")
            })

        return {
            "policy_id": policy_id,
            "policy_state": policy_state,
            "treatment_state": treatment_state,
            "territorial_scope_analysis": analysis,
            "cashless_vs_reimbursement": cashless_vs_reimbursement,
            "clauses_found": clauses_summary,
            "action_checklist": action_checklist,
            "disclaimer": (
                "NOTE: Static policy PDFs do not guarantee real-time hospital network empanelment. "
                "Always verify cashless status directly with the hospital's TPA desk prior to admission."
            )
        }

scenario_service = ScenarioService()
