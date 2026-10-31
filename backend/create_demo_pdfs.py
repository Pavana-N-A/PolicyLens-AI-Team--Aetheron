import os
import fitz # PyMuPDF

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(BACKEND_DIR, "data", "demo_policies")
os.makedirs(DEMO_DIR, exist_ok=True)

def create_pdf(filename: str, title: str, underwriter: str, distributor: str, pages_content: list):
    filepath = os.path.join(DEMO_DIR, filename)
    doc = fitz.open()

    for p_num, content in enumerate(pages_content, start=1):
        # A4 Page: 595 x 842 points
        page = doc.new_page(width=595, height=842)
        
        # Header banner - MANDATORY SYNTHETIC DEMO DATA
        page.draw_rect(fitz.Rect(0, 0, 595, 36), fill=(0.95, 0.90, 0.85), color=None)
        page.insert_text(
            fitz.Point(130, 22),
            "SYNTHETIC DEMO DATA – NOT A REAL POLICY",
            fontsize=12,
            fontname="helv",
            color=(0.8, 0.1, 0.1)
        )

        # Title and entities banner
        page.insert_text(fitz.Point(50, 60), title, fontsize=16, fontname="hebo", color=(0.1, 0.2, 0.4))
        page.insert_text(
            fitz.Point(50, 78),
            f"Risk Underwriter: {underwriter}  |  Distribution Channel: {distributor}",
            fontsize=9,
            fontname="helv",
            color=(0.3, 0.3, 0.3)
        )
        page.draw_line(fitz.Point(50, 88), fitz.Point(545, 88), color=(0.8, 0.8, 0.8), width=1)

        # Body text with comfortable margin
        rect = fitz.Rect(50, 100, 545, 780)
        page.insert_textbox(rect, content, fontsize=10, fontname="helv", color=(0.15, 0.15, 0.15))

        # Footer
        page.draw_line(fitz.Point(50, 790), fitz.Point(545, 790), color=(0.85, 0.85, 0.85), width=1)
        page.insert_text(
            fitz.Point(50, 808),
            f"Page {p_num} of {len(pages_content)}  |  PolicyLens Student Prototype Demo Document",
            fontsize=8,
            fontname="helv",
            color=(0.5, 0.5, 0.5)
        )

    doc.save(filepath)
    doc.close()
    print(f"Generated synthetic policy: {filepath}")
    return filepath

# Policy 1 Content (Direct Product: CareSecure Direct)
p1_pages = [
    """SECTION 1: POLICY SCHEDULE & UNDERWRITING PARTICULARS
Product Name: CareSecure Direct Comprehensive Health Plan
Actual Risk-Bearing Underwriter: Care Health Insurance Limited (IRDAI Reg. 148)
Distribution Channel: Direct Digital Portal (Care Direct Online)
Sum Insured Option: INR 10,00,000 (Ten Lakhs)
Policy Period: 12 Months Continuous
Policy Jurisdiction & Territorial Scope: Pan-India (All 28 States and 8 Union Territories)

SECTION 2: IN-PATIENT HOSPITALIZATION BENEFITS
2.1 Room Rent & ICU Limits:
Medically necessary hospitalization expenses incurred for Room Rent, Boarding and Nursing are payable up to Single Private A/C Room category without any proportionate deduction penalty. ICU/ICCU charges are covered up to actuals without capping.

2.2 Pre & Post Hospitalization:
Medical expenses incurred 60 days immediately before hospitalization and 90 days immediately following hospital discharge are covered, subject to an admissible hospitalization claim.

2.3 Day Care Treatments:
All day-care procedures and modern surgeries requiring less than 24 hours of hospitalization due to advanced technological advancements are fully covered up to the Sum Insured.

2.4 Road Ambulance Charges:
Emergency road ambulance service up to INR 3,000 per hospitalization event is covered for transferring the patient to the nearest hospital.""",

    """SECTION 3: WAITING PERIODS & TIMELINES
3.1 Initial Waiting Period (Clause 3.1):
A mandatory waiting period of 30 days from the policy inception date shall apply to all medical conditions and illnesses, except in the case of accidental bodily injury requiring emergency hospitalization.

3.2 Pre-Existing Disease (PED) Waiting Period (Clause 3.2):
A waiting period of 36 continuous months of insurance shall apply for any Pre-Existing Disease (PED) as defined by IRDAI. A condition diagnosed or treated prior to inception is covered only after completion of 36 months of continuous renewals with the Company.

3.3 Specific Ailments & Surgical Procedures (Clause 3.3):
A waiting period of 24 continuous months shall apply to the treatment of following conditions, whether pre-existing or not:
- Benign prostatic hypertrophy (BPH)
- Cataract surgery (subject to sub-limit of INR 40,000 per eye)
- Hernia of all types and hydrocele
- Calculus / Stones in urinary and biliary systems
- Joint replacement surgery (unless necessitated by accidental injury)
- Piles, fistula, and fissure-in-ano

3.4 Note on Post-Purchase Diagnosis:
A condition first contracted or diagnosed after the 30-day initial waiting period and not falling under Section 3.3 or General Exclusions is payable subject to policy terms and disclosure integrity.""",

    """SECTION 4: CO-PAYMENT, SUB-LIMITS & RESTORATION
4.1 Co-payment:
NIL mandatory co-payment applies for all insured members across all age brackets. An optional 20% co-pay can be chosen to reduce premium.

4.2 Automatic Restoration of Sum Insured:
The policy provides 100% automatic recharge of Sum Insured once in a policy year, immediately upon exhaustion of the base Sum Insured.

4.3 Cumulative Bonus (No Claim Bonus):
For each claim-free year, the base Sum Insured increases by 10% up to a maximum accumulation of 50%, without any increase in premium.

SECTION 5: CLAIMS PROCEDURE & HOSPITAL NETWORK
5.1 Cashless Facility:
Cashless hospitalization is available exclusively at network hospitals empanelled with the insurer or its Third-Party Administrator (TPA). Pre-authorisation request must be submitted:
- Planned Admission: At least 48 hours prior to admission.
- Emergency Admission: Within 24 hours of admission.

5.2 Non-Network Reimbursement Facility:
In case of hospitalization in a non-network hospital, treatment is covered on a reimbursement basis. The insured must intimate the Company within 24 hours of admission and submit all original discharge cards, bills, and pharmacy invoices within 30 days of discharge.

5.3 Territorial Scope Clarification:
The geographical scope covers all recognized hospitals within India. A non-network hospital in another state does not void coverage; it merely requires the reimbursement claim procedure."""
]

# Policy 2 Content (Bank Bundled Product: HealthProtect Canara Bank)
p2_pages = [
    """SECTION 1: MASTER POLICY & DISTRIBUTION ARCHITECTURE
Product Name: Canara HealthProtect Bancassurance Group Medical Scheme
Actual Risk-Bearing Underwriter: Star Health and Allied Insurance Co. Ltd. (IRDAI Reg. 129)
Distribution Channel / Corporate Agent: Canara Bank (Bancassurance Channel)
Important Notice: Canara Bank is the corporate distributor/intermediary. The risk carrier and claim settlement authority is Star Health and Allied Insurance Co. Ltd.
Base Sum Insured: INR 5,00,000 (Five Lakhs)
Territorial Scope: Pan-India (All States & Union Territories of India)

SECTION 2: IN-PATIENT & ICU EXPENSES
2.1 Room Rent & ICU Capping (Important Condition):
Room Rent, boarding, and nursing charges are strictly capped at 1% of the Sum Insured per day (INR 5,000 per day for INR 5 Lakh SI).
ICU charges are capped at 2% of the Sum Insured per day (INR 10,000 per day).
CRITICAL: If the insured opts for a room category higher than the eligible limit, proportionate deduction shall apply to all associated medical charges (doctor fees, surgeon fees, operation theater expenses).

2.2 Road Ambulance:
Payable up to INR 1,500 per hospitalization.""",

    """SECTION 3: WAITING PERIODS & CLAUSE DETAILS
3.1 Initial Waiting Period:
A 30-day waiting period from commencement date applies to all illnesses except accidents.

3.2 Pre-Existing Diseases (PED):
A 24-month waiting period applies for pre-existing diseases declared at the time of proposal and accepted by the Company. Continuous renewal with Canara Bank scheme is mandatory.

3.3 Specific Diseases / Ailments (24 Months Waiting Period):
The following conditions are excluded from coverage until 24 months of continuous insurance have elapsed:
- Cataract surgery
- Hernia, hydrocele, congenital internal diseases
- Stones in gall bladder and kidney
- Hysterectomy for menorrhagia
- Knee and hip joint replacements

3.4 Chronology Rule:
Illnesses first diagnosed 24 months after policy inception are eligible for claims provided they are not permanent exclusions, were not concealed at enrollment, and all policy renewals were paid on time without break.""",

    """SECTION 4: CO-PAYMENT & DEDUCTIBLE CONDITIONS
4.1 Mandatory Co-Payment:
A mandatory 20% co-payment applies to each and every admissible claim if the insured person resides in Zone B (non-metro) but undergoes planned medical treatment in a Zone A metro city (such as Mumbai, Delhi NCR, or Bengaluru).
Treatment taken in network hospitals within the home state is exempt from zonal co-pay.

4.2 Deductibles:
No deductible on base sum insured.

SECTION 5: CLAIM INTIMATION & CASHLESS PROTOCOL
5.1 Cashless Pre-authorisation:
Must be submitted 72 hours prior to planned admission. In case of emergency, notice must be given within 24 hours of hospital admission.

5.2 Non-Network Reimbursement Protocol:
If treatment is taken in a non-network hospital in Karnataka, Maharashtra, or any other Indian state:
- Hospital must have at least 15 in-patient beds (10 in Class C towns)
- Fully equipped operation theatre and round-the-clock qualified medical practitioners
- Submit claim packet within 15 days of discharge with doctor prescriptions and forensic test reports.

5.3 Verification Warning:
Empanelment of network hospitals changes periodically. Empanelment on a policy PDF does not guarantee active cashless status on the date of admission."""
]

if __name__ == "__main__":
    create_pdf(
        "PolicyLens_CareSecure_Direct.pdf",
        "PolicyLens – CareSecure Direct Health Insurance",
        "Care Health Insurance Limited",
        "Care Direct Web Portal (Direct Insurer)",
        p1_pages
    )
    create_pdf(
        "PolicyLens_HealthProtect_CanaraBank.pdf",
        "PolicyLens – Canara HealthProtect Bancassurance Scheme",
        "Star Health and Allied Insurance Co. Ltd.",
        "Canara Bank (Bancassurance Distribution Channel)",
        p2_pages
    )
