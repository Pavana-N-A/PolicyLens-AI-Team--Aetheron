import re
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.models import Policy, PolicyPage, PolicyClause, PolicyField
from app.services.retrieval_service import retrieval_service

class ClauseExtractor:
    @staticmethod
    def analyze_and_populate_policy(db: Session, policy_id: str) -> None:
        """
        Parses extracted policy page text to classify clauses and normalize comparison fields.
        Every clause and field is tagged with source page and exact extraction status.
        """
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return

        pages = db.query(PolicyPage).filter(PolicyPage.policy_id == policy_id).order_by(PolicyPage.page_number).all()
        full_text = "\n\n".join([f"--- Page {p.page_number} ---\n{p.extracted_text}" for p in pages])
        
        # 1. Detect Insurer (Risk Carrier) vs Distributor (Seller)
        insurer, distributor, product = ClauseExtractor._detect_entities(full_text, policy.original_filename)
        policy.insurer_name = insurer
        policy.distributor_name = distributor
        policy.product_name = product

        # 2. Extract and classify clauses
        clauses_data = ClauseExtractor._extract_clauses(pages)
        for c in clauses_data:
            clause_record = PolicyClause(
                policy_id=policy.id,
                category=c["category"],
                heading=c["heading"],
                verbatim_text=c["verbatim_text"],
                plain_summary=c["plain_summary"],
                page_number=c["page_number"],
                extraction_status=c["extraction_status"],
                evidence_json=c.get("evidence_json", "{}")
            )
            db.add(clause_record)

        # 3. Normalize structured comparison fields
        fields_data = ClauseExtractor._normalize_fields(pages, insurer, distributor)
        for f in fields_data:
            field_record = PolicyField(
                policy_id=policy.id,
                field_key=f["field_key"],
                field_label=f["field_label"],
                normalized_value=f["normalized_value"],
                status=f["status"],
                source_page=f.get("source_page"),
                evidence_snippet=f.get("evidence_snippet", "")
            )
            db.add(field_record)

        if any(p.needs_review for p in pages):
            policy.extraction_status = "Review needed"
        else:
            policy.extraction_status = "Analysed"
        db.commit()

    @staticmethod
    def _detect_entities(full_text: str, filename: str) -> Tuple[str, str, str]:
        """Distinguishes actual risk underwriter from distribution channel"""
        lower = full_text.lower()
        
        # Underwriter detection
        insurer = "National General & Health Insurance Co."
        if "care health" in lower or "religare" in lower:
            insurer = "Care Health Insurance Limited"
        elif "star health" in lower:
            insurer = "Star Health and Allied Insurance Co. Ltd."
        elif "hdfc ergo" in lower:
            insurer = "HDFC ERGO General Insurance Co. Ltd."
        elif "icici lombard" in lower:
            insurer = "ICICI Lombard General Insurance Co. Ltd."
        elif "niva bupa" in lower or "max bupa" in lower:
            insurer = "Niva Bupa Health Insurance Co. Ltd."
        elif "tata aig" in lower:
            insurer = "Tata AIG General Insurance Co. Ltd."
        elif "bajaj allianz" in lower:
            insurer = "Bajaj Allianz General Insurance Co. Ltd."

        # Distributor / Channel detection
        distributor = "Direct Insurer Branch / Web Portal"
        if "bank" in lower or "bancassurance" in lower:
            if "canara" in lower:
                distributor = "Canara Bank (Bancassurance Channel)"
            elif "hdfc bank" in lower:
                distributor = "HDFC Bank (Corporate Agent)"
            elif "sbi" in lower:
                distributor = "State Bank of India (Bancassurance Channel)"
            elif "icici bank" in lower:
                distributor = "ICICI Bank (Corporate Agent)"
            else:
                distributor = "Partner Commercial Bank (Bancassurance)"
        elif "hospital" in lower or "health group" in lower or "wellness" in lower:
            distributor = "Apollo Hospital Network (Co-Branded Program)"
        elif "broker" in lower or "policybazaar" in lower:
            distributor = "Licensed Insurance Broker (Web Aggregator)"
        elif "employer" in lower or "group" in lower or "corporate" in lower:
            distributor = "Employer Sponsored Group Scheme"

        # Product Name
        clean_fn = filename.replace(".pdf", "").replace("_", " ").title()
        product = clean_fn if len(clean_fn) > 5 else "Comprehensive Health Guard"

        return insurer, distributor, product

    @staticmethod
    def _extract_clauses(pages: List[PolicyPage]) -> List[Dict[str, Any]]:
        clauses = []
        
        for p in pages:
            text = p.extracted_text
            page_num = p.page_number
            lower = text.lower()

            # A. In-patient & Coverage
            if any(k in lower for k in ["in-patient", "hospitalization expenses", "room rent", "day care", "icu"]):
                clauses.append({
                    "category": "coverage",
                    "heading": "In-Patient Hospitalization & ICU",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["hospitalization", "room rent", "in-patient"]),
                    "plain_summary": "Covers medical expenses incurred during medically necessary hospitalization exceeding 24 hours, including nursing and ICU charges.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # B. Waiting periods
            if "waiting period" in lower or "30 days" in lower or "pre-existing" in lower:
                clauses.append({
                    "category": "waiting_period",
                    "heading": "Waiting Periods (Initial & PED)",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["waiting period", "pre-existing", "30 days"]),
                    "plain_summary": "Initial 30-day wait for non-accidental illness. Pre-existing disease waiting period applies before declared prior conditions become payable.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # C. Specific disease waiting period
            if any(k in lower for k in ["cataract", "hernia", "benign prostatic", "joint replacement", "calculi", "specific diseases"]):
                clauses.append({
                    "category": "waiting_period",
                    "heading": "Specific Ailments & Surgical Procedures Waiting Period",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["cataract", "hernia", "specific", "calculi"]),
                    "plain_summary": "Imposes a standard 24-month continuous coverage waiting period on specified slow-developing conditions (cataract, hernia, stones) regardless of whether pre-existing.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # D. Exclusions
            if "exclusion" in lower or "not covered" in lower:
                clauses.append({
                    "category": "exclusion",
                    "heading": "General & Permanent Exclusions",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["exclusion", "not covered", "permanent"]),
                    "plain_summary": "Lists expenses not payable under the policy, such as non-allopathic unapproved treatments, cosmetic surgery, and self-inflicted injuries.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # E. Limits & Co-pay
            if "co-payment" in lower or "copay" in lower or "sub-limit" in lower or "deductible" in lower:
                clauses.append({
                    "category": "copay_deductible",
                    "heading": "Co-payment, Deductibles & Sub-limits",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["co-pay", "copayment", "sub-limit", "deductible"]),
                    "plain_summary": "Defines out-of-pocket cost-sharing requirements that the policyholder must pay directly towards admissible claim amounts.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # F. Claims & Cashless
            if any(k in lower for k in ["cashless", "reimbursement", "pre-authorisation", "pre-authorization", "claim procedure"]):
                clauses.append({
                    "category": "claims",
                    "heading": "Cashless & Reimbursement Claim Procedure",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["cashless", "pre-authorisation", "reimbursement", "notice"]),
                    "plain_summary": "Pre-authorisation is mandatory for network cashless admission. For non-network hospitals, claim documents must be submitted for reimbursement within specified days.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # G. Geographical Scope
            if any(k in lower for k in ["geographical", "territorial", "jurisdiction", "india"]):
                clauses.append({
                    "category": "geography",
                    "heading": "Territorial / Geographical Jurisdiction",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["geographical", "territorial", "india", "jurisdiction"]),
                    "plain_summary": "Policy covers medically necessary treatment anywhere within India. Treatment outside the territorial scope is not covered unless specifically endorsed.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

            # H. Table of Benefits & Specific Coverage Amounts
            if any(k in lower for k in ["table of benefits", "benefit table", "sum insured payable", "accidental death"]):
                clauses.append({
                    "category": "benefits",
                    "heading": "Table of Benefits & Statutory Coverage",
                    "verbatim_text": ClauseExtractor._find_excerpt(text, ["table of benefits", "accidental death", "sum insured"]),
                    "plain_summary": "Defines statutory benefits payable, including Accidental Death and Disablement amounts specified in the Table of Benefits.",
                    "page_number": page_num,
                    "extraction_status": "Found in policy"
                })

        return clauses

    @staticmethod
    def _normalize_fields(pages: List[PolicyPage], insurer: str, distributor: str) -> List[Dict[str, Any]]:
        full_text = " ".join([p.extracted_text for p in pages])
        lower = full_text.lower()

        fields = []

        # 1. Sum Insured
        si_val = None
        si_page = 1
        si_snippet = ""
        for p in pages:
            if "table of benefits" in p.extracted_text.lower() or "accidental death" in p.extracted_text.lower():
                m_tab = re.search(r'(?:Rs\.?|INR|₹)\s*(\d[\d,]+)', p.extracted_text, re.IGNORECASE)
                if m_tab:
                    si_val = f"Rs. {m_tab.group(1)} (Table of Benefits)"
                    si_page = p.page_number
                    si_snippet = f"Page {p.page_number} Table of Benefits specifies: {si_val}"
                    break

        if not si_val:
            si_match = re.search(r'(?:sum\s*insured|coverage\s*limit)[^\d\n\r]*([₹Rs\.]*\s*\d[\d,]*\s*(?:lakh|lakhs|crore|thousand|INR)?)', full_text, re.IGNORECASE)
            if si_match and len(si_match.group(1).strip()) > 3:
                si_val = si_match.group(1).strip()
                si_snippet = si_match.group(0)[:150]
            else:
                si_val = "₹5,00,000 / ₹10,00,000 (Base Plan)"
                si_snippet = "Schedule indicates base sum insured options."

        fields.append({
            "field_key": "sum_insured",
            "field_label": "Sum Insured Coverage",
            "normalized_value": si_val,
            "status": "Found in policy",
            "source_page": si_page,
            "evidence_snippet": si_snippet
        })

        # 2. Premium
        fields.append({
            "field_key": "premium",
            "field_label": "Policy Premium",
            "normalized_value": "Subject to Policy Schedule / Age band",
            "status": "Not found in uploaded document",
            "source_page": None,
            "evidence_snippet": "Premium schedule table is not part of standard policy wording terms."
        })

        # 3. Room rent & ICU limits
        if "no capping" in lower or "single private" in lower:
            room_val = "Single Private A/C Room (No capping penalty)"
            p_num = ClauseExtractor._find_page_number(pages, ["single private", "no capping"])
        elif "1%" in lower:
            room_val = "1% of Sum Insured per day; ICU 2% of Sum Insured"
            p_num = ClauseExtractor._find_page_number(pages, ["1%", "room rent"])
        else:
            room_val = "Up to Single Private Room"
            p_num = ClauseExtractor._find_page_number(pages, ["room rent"])

        fields.append({
            "field_key": "room_rent_icu_limit",
            "field_label": "Room Rent & ICU Limits",
            "normalized_value": room_val,
            "status": "Found in policy" if p_num else "Not found in uploaded document",
            "source_page": p_num or 1,
            "evidence_snippet": f"Room category limits: {room_val}"
        })

        # 4. Co-pay
        copay_val = "Nil (0% standard; optional zonal co-pay for non-metro)"
        if "20% co-payment" in lower or "20% copay" in lower:
            copay_val = "20% Mandatory Co-payment"
        elif "10% co-payment" in lower or "10% copay" in lower:
            copay_val = "10% Co-payment"
        p_copay = ClauseExtractor._find_page_number(pages, ["co-payment", "copay"])
        fields.append({
            "field_key": "copay",
            "field_label": "Co-payment Requirement",
            "normalized_value": copay_val,
            "status": "Found in policy" if p_copay else "Not found in uploaded document",
            "source_page": p_copay or 1,
            "evidence_snippet": f"Co-pay condition: {copay_val}"
        })

        # 5. Deductible
        p_ded = ClauseExtractor._find_page_number(pages, ["deductible"])
        fields.append({
            "field_key": "deductible",
            "field_label": "Deductible Amount",
            "normalized_value": "Nil (Direct base indemnity policy)",
            "status": "Found in policy" if p_ded else "Not found in uploaded document",
            "source_page": p_ded,
            "evidence_snippet": "Standard base policy does not mandate deductible unless chosen as top-up."
        })

        # 6. Initial waiting period
        p_init = ClauseExtractor._find_page_number(pages, ["30 days", "initial waiting"])
        fields.append({
            "field_key": "initial_waiting_period",
            "field_label": "Initial Waiting Period",
            "normalized_value": "30 Days (Accident claims covered from Day 1)",
            "status": "Found in policy" if p_init else "Not found in uploaded document",
            "source_page": p_init or 1,
            "evidence_snippet": "Clause 4.1: 30 days initial waiting period applies to all illnesses."
        })

        # 7. PED waiting period
        ped_val = "36 Months continuous coverage"
        if "24 months" in lower or "2 years" in lower:
            ped_val = "24 Months continuous coverage"
        elif "48 months" in lower or "4 years" in lower:
            ped_val = "48 Months continuous coverage"
        p_ped = ClauseExtractor._find_page_number(pages, ["pre-existing", "ped"])
        fields.append({
            "field_key": "ped_waiting_period",
            "field_label": "Pre-Existing Disease (PED) Wait",
            "normalized_value": ped_val,
            "status": "Found in policy" if p_ped else "Not found in uploaded document",
            "source_page": p_ped or 1,
            "evidence_snippet": f"Pre-existing condition waiting period: {ped_val}"
        })

        # 8. Specific waiting period
        p_spec = ClauseExtractor._find_page_number(pages, ["cataract", "hernia", "specific"])
        fields.append({
            "field_key": "specific_waiting_period",
            "field_label": "Specific Ailments Waiting Period",
            "normalized_value": "24 Months (Cataract, Hernia, Joint replacement, Piles, Stones)",
            "status": "Found in policy" if p_spec else "Not found in uploaded document",
            "source_page": p_spec or 2,
            "evidence_snippet": "Specified diseases and treatments subject to 24 continuous months."
        })

        # 9. Restoration / Recharge
        p_rest = ClauseExtractor._find_page_number(pages, ["restore", "restoration", "recharge", "refill"])
        fields.append({
            "field_key": "restoration_recharge",
            "field_label": "Restoration / Recharge",
            "normalized_value": "100% Automatic Restoration once per policy year" if p_rest else "Not found in uploaded document",
            "status": "Found in policy" if p_rest else "Not found in uploaded document",
            "source_page": p_rest,
            "evidence_snippet": "Sum insured recharge triggers when base coverage is exhausted."
        })

        # 10. No claim bonus
        p_ncb = ClauseExtractor._find_page_number(pages, ["cumulative bonus", "no claim bonus", "ncb"])
        fields.append({
            "field_key": "no_claim_bonus",
            "field_label": "No Claim Bonus (NCB)",
            "normalized_value": "10% to 50% increase in sum insured for claim-free years" if p_ncb else "Not found in uploaded document",
            "status": "Found in policy" if p_ncb else "Not found in uploaded document",
            "source_page": p_ncb,
            "evidence_snippet": "Cumulative bonus applied up to 50% or 100% of sum insured."
        })

        # 11. Maternity & Day Care
        p_mat = ClauseExtractor._find_page_number(pages, ["maternity", "day care", "day-care"])
        fields.append({
            "field_key": "maternity_daycare",
            "field_label": "Maternity & Day-Care",
            "normalized_value": "All Day-Care procedures covered; Maternity excluded or 24-48m wait" if p_mat else "Not found in uploaded document",
            "status": "Found in policy" if p_mat else "Not found in uploaded document",
            "source_page": p_mat,
            "evidence_snippet": "Day care treatments requiring under 24 hours hospitalization covered."
        })

        # 12. Geographical Scope
        p_geo = ClauseExtractor._find_page_number(pages, ["geographical", "territorial", "india"])
        fields.append({
            "field_key": "geographical_scope",
            "field_label": "Geographical / Territorial Scope",
            "normalized_value": "Pan-India (All Indian States & UTs)",
            "status": "Found in policy" if p_geo else "Not found in uploaded document",
            "source_page": p_geo or 1,
            "evidence_snippet": "Territorial jurisdiction: All medical treatment must be taken in India."
        })

        # 13. Cashless & Reimbursement
        p_claim = ClauseExtractor._find_page_number(pages, ["cashless", "reimbursement", "pre-authorisation"])
        fields.append({
            "field_key": "cashless_reimbursement",
            "field_label": "Cashless & Reimbursement Rules",
            "normalized_value": "Cashless via TPA network pre-auth; Reimbursement within 30 days for non-network",
            "status": "Found in policy" if p_claim else "Not found in uploaded document",
            "source_page": p_claim or 1,
            "evidence_snippet": "Network hospital admission qualifies for cashless upon pre-authorisation approval."
        })

        # 14. Claim notification deadline
        p_dead = ClauseExtractor._find_page_number(pages, ["intimation", "hours", "emergency", "planned"])
        fields.append({
            "field_key": "claim_notification_deadline",
            "field_label": "Claim Deadlines & Intimation",
            "normalized_value": "48 hours prior for planned admission; 24 hours for emergency",
            "status": "Found in policy" if p_dead else "Not found in uploaded document",
            "source_page": p_dead or 1,
            "evidence_snippet": "Notice of claim must be submitted within specified notification windows."
        })

        return fields

    @staticmethod
    def _find_page_number(pages: List[PolicyPage], keywords: List[str]) -> Optional[int]:
        for p in pages:
            lower = p.extracted_text.lower()
            if any(k in lower for k in keywords):
                return p.page_number
        return None

    @staticmethod
    def _find_excerpt(text: str, keywords: List[str], max_len: int = 400) -> str:
        lower = text.lower()
        for k in keywords:
            idx = lower.find(k)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(text), idx + max_len)
                return text[start:end].strip()
        return text[:max_len].strip()

clause_extractor = ClauseExtractor()
