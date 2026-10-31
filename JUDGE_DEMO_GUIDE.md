# PolicyLens – Hackathon Judge Demonstration & Technical Audit Guide

**Project:** PolicyLens – Intelligent Insurance Policy Understanding & Risk Navigator  
**Track / Domain:** InsurTech / Document AI / Decision Support  
**Target Environment:** Local-First Windows Laptop (No paid cloud infrastructure)  
**Document Purpose:** Complete technical audit, architecture explanation, and feature-by-feature testing guide for hackathon evaluators and live stage demonstrations.

---

## 1. 30-Second Elevator Pitch & Architecture for Judges

> **The Problem:** Health insurance policy wordings in India are 30–60 pages of impenetrable legalese. Policyholders struggle with 4 critical real-world ambiguities:
> 1. *Post-purchase diagnoses:* When an illness is diagnosed 2–3 years after buying a policy, insurers or TPAs frequently deny claims citing "Pre-Existing Diseases" (PED), even though legally under IRDAI regulations, conditions diagnosed after inception are **not** PEDs.
> 2. *Inter-state treatment:* A consumer buys a policy in Karnataka and needs hospitalization in Maharashtra. They assume treatment is not covered, confusing **Pan-India contractual coverage** with **cashless network hospital empanelment**.
> 3. *Distributor vs. Risk Carrier confusion:* Policies marketed by trusted brands like Canara Bank or Apollo Hospitals are actually underwritten by third-party risk carriers (Star Health, Care Health). Consumers sue or blame the bank, unaware of the actual underwriter's terms.
> 4. *Room rent capping traps:* Choosing a room rent 1% above the limit triggers proportionate deduction penalties across doctor fees, surgery, and ICU.
>
> **The PolicyLens Solution:** A privacy-first, local web prototype running entirely on the laptop. It extracts contract wording using PyMuPDF and local OCR fallback, normalizes 16 contractual fields into SQLite, indexes clauses via SQLite FTS5, compares policies side-by-side, evaluates guided legal scenarios, and answers consumer questions citing exact contract pages without sending original PDFs to the cloud.

### High-Level Architecture Diagram
```
┌────────────────────────────────────────────────────────────────────────┐
│                        Vite + React 19 Frontend                        │
│                 http://localhost:5173  (TypeScript)                     │
│    [Dashboard]   [My Policies]   [Compare]   [Scenarios]   [AI Chat]   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API (Bearer Token / Cookie)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend Service                          │
│               http://127.0.0.1:8001  (Python 3.13)                     │
├───────────────────┬────────────────────────────┬───────────────────────┤
│ Document Pipeline │ Decision Support Engine    │ Grounded Assistant    │
│ • PyMuPDF (fitz)  │ • Underwriter vs Channel   │ • SQLite FTS5 Search  │
│ • OCR Service     │ • 16-Field Normalizer      │ • 4-Section Synthesis │
│ • Table Detector  │ • Timeline & PED Evaluator │ • Page Citation Engine│
└─────────┬─────────┴─────────────┬──────────────┴───────────┬───────────┘
          │                       │                          │
┌─────────▼───────────────────────▼──────────────────────────▼───────────┐
│                      Local Laptop Storage Layer                        │
│  • SQLite DB: prototype/backend/data/db/policylens.db                 │
│  • Original PDFs: prototype/backend/data/uploads/<user_id>/            │
│  • SQLite FTS5 Virtual Table: policy_fts (BM25 keyword search)         │
│  • Optional Gemini API: Server-side via prototype/backend/.env         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Deep Technical Audit of the 6 Core Features

### Feature 1: Login & Authentication

| Aspect | Technical Reality in Code |
|---|---|
| **Backend Implementation** | [`prototype/backend/app/api/auth.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/api/auth.py) and [`prototype/backend/app/api/deps.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/api/deps.py) |
| **Frontend Implementation** | [`prototype/frontend/src/components/LoginModal.tsx`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/frontend/src/components/LoginModal.tsx) |
| **Storage Location** | `users` table inside `prototype/backend/data/db/policylens.db` |
| **Password Security** | Passwords are **never stored in plain text**. Uses PBKDF2 HMAC SHA-256 with 100,000 iterations and a 16-byte cryptographically secure per-user salt (`secrets.token_hex(16)`). Format: `<salt>:<hex_hash>`. Verified via `secrets.compare_digest`. |
| **Session Architecture** | When a user logs in, the backend creates a 32-byte secure random token (`secrets.token_urlsafe(32)`), stores it in `ACTIVE_SESSIONS`, and sets an HTTP-only cookie `policylens_session`. Frontend also stores token in `localStorage` for `Authorization: Bearer <token>` headers. |
| **Demo Login vs Real Auth** | **Real Auth:** `POST /api/auth/register` creates a user account; `POST /api/auth/login` checks the password hash.<br>**Demo Login:** `POST /api/auth/demo-login` automatically fetches or creates the evaluator account `judge.demo@policylens.local` (pre-hashed password `DemoJudge2026!`) with `is_demo=True` and issues an instant session token. |
| **Judge Lockout Protection** | In `deps.py`, if an active session is cleared after a backend reload, `get_current_user` falls back to the seeded demo user so evaluators are never unexpectedly locked out during live judging. |

#### Exact Test Steps:
1. **Valid Demo Login:** Open `http://localhost:5173/`, click **"Instant Demo Login"**. Result: Instantly opens the dashboard; badge displays `DEMO` and user `Hackathon Evaluator`.
2. **Account Registration:** Click Sign Out. In modal, click *"Register"*, enter `arjun@example.com`, password `Password123!`, click *"Create Local Account"*. Result: User account created in SQLite `users` table.
3. **Invalid Password:** Sign out. Enter `arjun@example.com` with password `WrongPassword`. Result: Returns HTTP 401 with `"Invalid email or password."`.
4. **Logout:** Click **"Sign Out"** in sidebar footer. Result: Clears token, removes cookie, returns to login screen.

---

### Feature 2: PDF Upload and OCR Pipeline

| Aspect | Technical Reality in Code |
|---|---|
| **Backend Implementation** | [`prototype/backend/app/api/policies.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/api/policies.py), [`app/services/pdf_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/pdf_service.py), [`app/services/ocr_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/ocr_service.py) |
| **Frontend Implementation** | [`prototype/frontend/src/components/PoliciesView.tsx`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/frontend/src/components/PoliciesView.tsx), [`PolicyDetailModal.tsx`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/frontend/src/components/PolicyDetailModal.tsx) |
| **PDF Extraction Engine** | **PyMuPDF (`pymupdf` / `fitz`)**. Opens PDF with `fitz.open(stored_path)`, iterates page-by-page, extracts text with `page.get_text("text")`, and detects tables via `page.find_tables()`. |
| **Hybrid Pipeline Decision** | For each page, checks if `len(digital_text) >= 50`.<br>• If **>= 50 chars**: Digital extraction used (`extraction_method = "digital"`, confidence `1.0`, `needs_review = False`).<br>• If **< 50 chars** (scanned/image page): Renders page to image at 250 DPI (`page.get_pixmap(dpi=250)`), sends to `ocr_service.ocr_pixmap()`. |
| **OCR Engines & Fallback** | `ocr_service.py` provides a swappable interface:<br>1. `PaddleOCREngine` (tries PaddleOCR 3.x if installed).<br>2. `TesseractOCREngine` (tries `pytesseract` if binary installed).<br>3. `PyMuPDFOCREngine` (calls `page.get_textpage_ocr()`).<br>4. `FallbackHeuristicEngine` (Active on Windows when external C-binaries are absent): Does **not** fabricate fake text; returns clear notice `[OCR NOTICE: Image-only scanned page detected...]` with confidence `0.20` and flags `needs_review = True`. |
| **Extraction Statuses** | `Uploaded` → `Extracting` → `Analysed` (or `Review needed` if low-confidence OCR detected) → `Failed`. |
| **Manual Clause Editing** | Section 3.C requirement: In `PolicyDetailModal.tsx`, clicking *"Edit"* calls `PUT /api/policies/{id}/clauses/{clause_id}`, allowing manual correction of uncertain OCR text. |

#### How to Verify Extracted Text Against Original PDF:
1. Go to **"My Policies"** → Click **"Inspect Clauses"**.
2. Click the **"Extracted Policy Clauses"** tab: View each verbatim contract clause, plain summary, and source page number.
3. Click the **"Page Inspection & OCR Confidence"** tab: View the exact text extracted per page, method (`digital` or `ocr_fallback`), and confidence score.
4. Open the original PDF located in `prototype/backend/data/uploads/<user_id>/` and confirm that page numbers match exactly.

---

### Feature 3: Local Storage & Database Audit

| Aspect | Technical Reality in Code |
|---|---|
| **Database Technology** | **SQLite 3**, managed via **SQLAlchemy 2.0** ORM. Foreign key constraints strictly enforced (`PRAGMA foreign_keys=ON`). |
| **Exact DB File & Path** | `prototype/backend/data/db/policylens.db`<br>Full Windows Path: `c:\Users\POORNIMA R\OneDrive\Desktop\policylens level1\prototype\backend\data\db\policylens.db` |
| **Original PDF Folder** | `prototype/backend/data/uploads/<user_id>/<file_uuid>.pdf`<br>PDFs are stored as raw files on disk; **never as heavy BLOBs inside SQLite**. |
| **Full-Text Search Engine** | **SQLite FTS5 virtual table** (`policy_fts`), supporting BM25-ranked keyword searches and snippet extraction (`snippet(policy_fts, 2, '<b>', '</b>', '...', 30)`). |
| **Multi-Policy Association** | Every policy has `user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))`. Users only access their own policies; deletion cascades cleanly. |
| **Persistence Proof** | **100% Persisted Locally.** Records survive browser refresh, logout, and full app/server restart. Verified via database inspection script showing 17 active tables, 7 policies, 57 clauses, and 98 fields. |

#### Safe Steps to Inspect Database:
Run the included diagnostic script in terminal:
```cmd
cd prototype\backend
.\venv\Scripts\python.exe inspect_db.py
```
*(Outputs table names, row counts, policy list, and tests FTS5 keyword retrieval).*

---

### Feature 4: Google Gemini API & Local Grounded Fallback

| Aspect | Technical Reality in Code |
|---|---|
| **Backend Implementation** | [`prototype/backend/app/services/gemini_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/gemini_service.py) |
| **Official SDK Used** | Official Google GenAI SDK: `from google import genai` (`google-genai` package). |
| **Configurable Model** | Read from `.env` via `GEMINI_MODEL=gemini-2.5-flash` (or `gemini-1.5-flash`). Model name is not hardcoded. |
| **API Key Location** | Stored strictly in `prototype/backend/.env` under `GEMINI_API_KEY`. **Never placed in frontend code, HTML, JavaScript bundles, Git, or committed files.** (`prototype/.gitignore` blocks `.env`). |
| **Health Check Endpoint** | `GET /api/health/ai` returns `{"status": "configured"|"not configured", "model": "...", "notice": "..."}`. **Never leaks or returns the API key.** |
| **Current Operating Mode** | **Local Grounded Mode (Default):** If `GEMINI_API_KEY` is not provided or user consent is pending, PolicyLens uses its local deterministic analyzer. It searches SQLite FTS5 for exact policy clauses and synthesizes the exact 4 required sections without requiring external API calls or payment. |
| **AI Privacy Notice & Consent** | In accordance with Google AI Studio free-tier terms, the frontend features an AI privacy notice and consent toggle. Real personal policyholder identifiers (PAN, phone, medical records) should never be submitted to unpaid free tiers. |

#### How to Connect Gemini API (Optional):
1. Get a free key from [Google AI Studio](https://aistudio.google.com/).
2. Open `prototype/backend/.env` in Notepad and add:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. Restart the backend. In the chat, the response JSON will now show `"engine": "gemini (gemini-2.5-flash)"`.

---

### Feature 5: Insurance Comparison (Underwriter vs. Distributor)

| Aspect | Technical Reality in Code |
|---|---|
| **Backend Implementation** | [`prototype/backend/app/services/comparison_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/comparison_service.py) & [`clause_extractor.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/clause_extractor.py) |
| **Frontend Implementation** | [`prototype/frontend/src/components/ComparisonView.tsx`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/frontend/src/components/ComparisonView.tsx) |
| **What Powers Comparison?** | **Extracted structured database fields** (`policy_fields` table). Extracted by `clause_extractor.py` during upload and normalized across 16 standard contractual categories. |
| **Carrier vs. Distributor** | Explicitly separates **Actual Underwriter** (e.g. *Star Health*, *Care Health*) from the **Distribution Channel** (e.g. *Canara Bank Bancassurance*, *Apollo Hospital Group*, *Direct Web Portal*). |
| **Normalized Categories** | 1. Sum Insured, 2. Premium, 3. Room Rent & ICU limits, 4. Co-pay, 5. Deductible, 6. Initial waiting period (30d), 7. PED waiting period (24-48m), 8. Specific ailments wait (24m), 9. General exclusions, 10. Restoration/Recharge, 11. No Claim Bonus (NCB), 12. Maternity/Day-care, 13. Geographical scope, 14. Cashless vs reimbursement rules, 15. Claim intimation deadlines. |
| **Missing Data Integrity** | If a clause is not found in the uploaded wording, it is strictly labelled `"Not found in uploaded document"`. **Missing data is never invented.** |
| **Priority Trade-offs** | Highlights trade-offs based on user priority (`balanced`, `shorter_waiting_period`, `lower_copay`, `higher_coverage`). Supports CSV export via `exportCSV()`. |

#### Sample Two-Policy Comparison Test:
- **Policy 1:** *CareSecure Direct Plan*
  - Underwriter: Care Health Insurance Limited | Channel: Direct Web Portal
  - Room Rent: Single Private Room (No capping penalty) | Co-pay: 0% Nil | PED Wait: 36 Months
- **Policy 2:** *Canara HealthProtect Scheme*
  - Underwriter: Star Health and Allied Insurance | Channel: Canara Bank (Bancassurance)
  - Room Rent: 1% of Sum Insured cap (triggers proportionate deduction) | Co-pay: 20% Zonal Co-pay | PED Wait: 24 Months
- **Evaluator Insight:** Policy 2 has a shorter PED wait (24 vs 36 months), but imposes a severe 1% room rent cap and a 20% co-payment, demonstrating why comparing brand names alone is misleading.

---

### Feature 6: PolicyLens Assistant (Evidence-Grounded Chat)

| Aspect | Technical Reality in Code |
|---|---|
| **Backend Implementation** | [`prototype/backend/app/services/agent_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/agent_service.py), [`retrieval_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/retrieval_service.py), [`gemini_service.py`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/backend/app/services/gemini_service.py) |
| **Frontend Implementation** | [`prototype/frontend/src/components/ChatView.tsx`](file:///c:/Users/POORNIMA%20R/OneDrive/Desktop/policylens%20level1/prototype/frontend/src/components/ChatView.tsx) |
| **End-to-End Query Flow** | 1. User sends message via `POST /api/chat`.<br>2. `agent_service.py` detects query intent (Inter-state travel, Post-purchase illness, Hospital network check, or General clause query).<br>3. Runs BM25 full-text query on SQLite FTS5 table `policy_fts` scoped to the user's policies.<br>4. Retrieves top matching page chunks with page numbers and document titles.<br>5. Generates grounded explanation (via Gemini API if configured or local deterministic engine).<br>6. Verifies page numbers exist, stores message and sources in `chat_messages` table, and returns JSON. |
| **Mandatory 4 Sections** | Every policy answer is structured into: <br>1. `### What the document says` (with inline references like `[Policy Name, page X]`)<br>2. `### Simple explanation`<br>3. `### What this may mean`<br>4. `### What still needs confirmation` |
| **No-Evidence Fallback** | If no matching text exists in the PDF, the assistant responds: *"I could not find this condition in the uploaded pages... check your policy schedule or verify with the insurer."* It never invents coverage. |

---

## 3. Top 10 Practical Test Questions for Hackathon Judges

Use these 10 exact questions in the **"Ask PolicyLens"** chat during evaluation:

| # | Judge Prompt | What the System Retrieves | Expected Evidence & Answer Behavior |
|---|---|---|---|
| **1** | *"I bought this policy in Karnataka but need treatment in Maharashtra. What should I check?"* | Territorial scope clauses & Claims procedure from Page 1 & 3 | Explains Pan-India coverage makes treatment valid in Maharashtra. Clarifies that cashless access requires hospital empanelment; if non-network, reimbursement claim can still be filed. Cites page numbers. |
| **2** | *"I was healthy when I bought the policy but was diagnosed with a disease two years later. Which clauses matter?"* | Waiting periods (initial, PED, specific ailments) from Page 2 | Clarifies that under IRDAI guidelines, illness diagnosed post-purchase is NOT a Pre-Existing Disease (PED). Warns it is NOT automatically covered: checks 24-month specific ailments wait (hernia, stones), continuous renewal history, and disclosure integrity. |
| **3** | *"Is this hospital cashless or should I use reimbursement?"* | Local hospital network dataset & Pre-authorisation clauses | Queries local TPA dataset. Explicitly warns: `SYNTHETIC DEMO DATA – Not verified live. Static policy PDF does not guarantee active real-time empanelment; confirm with hospital TPA desk before admission.` Outlines pre-auth deadlines. |
| **4** | *"What is the room rent limit and does proportionate deduction apply?"* | In-patient room rent & ICU clauses from Page 1 | Compares room categories: CareSecure Direct has Single Private Room (no capping penalty); Canara HealthProtect has 1% of Sum Insured per day cap and triggers proportionate deduction penalties across doctor/surgery fees if exceeded. |
| **5** | *"What is the pre-existing disease (PED) waiting period?"* | Clause 3.2 / Waiting period section from Page 2 | Cites exact period: 36 continuous months for CareSecure Direct vs 24 continuous months for Canara HealthProtect. Emphasizes that continuous renewals without break are mandatory. |
| **6** | *"Which specific diseases or surgeries have a 24-month waiting period?"* | Specific Ailments Clause 3.3 from Page 2 | Lists specified slow-developing conditions: Cataract, Hernia, Hydrocele, Gall bladder/kidney stones, Joint replacements, Benign Prostatic Hypertrophy (BPH). Notes this wait applies whether pre-existing or not. |
| **7** | *"Are day care procedures covered if I stay in the hospital for less than 24 hours?"* | Day Care Treatments Clause 2.3 from Page 1 | Cites clause confirming that modern technological surgeries requiring under 24 hours hospitalization are covered up to the Sum Insured. |
| **8** | *"Does the policy mandate a co-payment on claims?"* | Co-payment conditions from Page 3 | Highlights contrast: CareSecure Direct has NIL (0%) mandatory co-pay; Canara HealthProtect imposes 20% mandatory zonal co-payment for non-metro residents treated in Zone A metros. |
| **9** | *"What is the cumulative bonus or No Claim Bonus (NCB) structure?"* | Cumulative bonus terms from Page 3 | Cites 10% increase in base sum insured per claim-free year up to a maximum 50% accumulation without premium increase. |
| **10** | *"Are outpatient dental surgeries and cosmetic procedures covered?"* | General Exclusions Clause / Document scan | States that cosmetic surgery and routine dental care are not covered under standard in-patient hospitalization terms. If clause is missing from schedule, explicitly notes: *"I could not find outpatient dental coverage in the uploaded pages."* |

---

## 4. Feature Implementation Status Matrix

| Feature | Status | Implementation Details |
|---|---|---|
| **Demo Login** | **Fully Implemented** | One-click instant login via `POST /api/auth/demo-login` (creates/logs into `judge.demo@policylens.local`). |
| **User Registration & Login** | **Fully Implemented** | PBKDF2 HMAC SHA-256 hashed passwords in SQLite; session tokens via HTTP-only cookies and Bearer headers. |
| **Digital PDF Text Extraction** | **Fully Implemented** | PyMuPDF (`fitz`) page-by-page extraction with table detection and page numbering. |
| **Local SQLite Database** | **Fully Implemented** | Relational tables + foreign keys + SQLite FTS5 full-text indexing at `prototype/backend/data/db/policylens.db`. |
| **Local PDF File Storage** | **Fully Implemented** | Stored at `prototype/backend/data/uploads/<user_id>/<uuid>.pdf`; original PDFs never touch cloud storage. |
| **Policy Comparison** | **Fully Implemented** | Side-by-side comparison across 16 normalized fields, separating underwriter from distributor brand; CSV export. |
| **Scenario 1 (Post-Purchase Illness)** | **Fully Implemented** | Guided calculator evaluating inception vs diagnosis chronology, PED legal distinction, and IRDAI rules. |
| **Scenario 2 (Inter-State Treatment)** | **Fully Implemented** | Separates territorial validity from cashless hospital network availability; action checklist. |
| **Evidence-Grounded Policy Chat** | **Fully Implemented** | SQLite FTS5 BM25 chunk retrieval; structured 4-section synthesis with exact `[Policy, page X]` citations. |
| **Hospital Network Search** | **Fully Implemented** | Local CSV dataset search by city/name/state with source date and synthetic demo disclaimer. |
| **Manual Clause Editing** | **Fully Implemented** | Modal review tool allows editing verbatim clause text and plain summary via `PUT /api/policies/{id}/clauses/{cid}`. |
| **Gemini AI Integration** | **Fully Implemented** | Uses official `google-genai` SDK via server-side `.env`. Operates with local deterministic fallback when key is absent. |
| **Local Scanned OCR Fallback** | **Mock / Heuristic Fallback** | When external C-binaries (Tesseract/PaddleOCR) are not installed on Windows, `FallbackHeuristicEngine` safely returns an OCR review notice and sets `Review needed`. |
| **Live Third-Party Hospital Scraping** | **Not Implemented (By Design)** | Section 10 of spec explicitly forbids scraping insurer websites as live feeds; relies on verifiable local CSV imports. |

---

## 5. Potential Live Demo Risks & Mitigation Strategies

| Risk | Cause | How We Prevented It |
|---|---|---|
| **Port Conflict (`WinError 10013`)** | Port 8000 blocked by Windows services / Hyper-V. | Backend and frontend have been updated to run cleanly on **Port 8001** (`http://127.0.0.1:8001`). |
| **Judge Session Expiry / Reload Lockout** | Server restart clearing in-memory tokens. | `deps.py` automatically falls back to the seeded demo user record in SQLite so the judge is never logged out. |
| **Gemini Rate Limit or Missing API Key** | Free tier 429 quota exhaustion or no WiFi. | `gemini_service.py` features a **Local Deterministic Analyzer** that retrieves exact SQLite FTS5 clauses and generates structured answers offline. |
| **Scanned PDF Failing Silently** | External OCR binaries missing on Windows laptop. | Swappable `ocr_service.py` gracefully catches low-text pages, marks `Review needed`, and enables manual clause inspection in the UI. |
| **Missing Contract Terms** | Incomplete policy wording uploaded. | Comparison engine and assistant explicitly label missing items as `"Not found in uploaded document"` instead of hallucinating. |

---

## 6. Step-by-Step 5-Minute Judge Demo Script

1. **Open the App (Minute 0:00):**  
   Open `http://localhost:5173/` in your browser. Show the login screen.
2. **Instant Demo Access (Minute 0:30):**  
   Click **"Instant Demo Login"**. Point out that credentials are secure and stored locally.
3. **Load Synthetic Policies (Minute 1:00):**  
   Click **"Load Demo Policies"**. Explain that these two policies demonstrate two different distribution channels (Direct vs Bank Bancassurance).
4. **Inspect Clauses & OCR (Minute 1:45):**  
   Go to **"My Policies"** → Click **"Inspect Clauses"**. Show verbatim text, plain summaries, and the Page Inspection tab showing PyMuPDF extraction methods.
5. **Side-by-Side Comparison (Minute 2:30):**  
   Go to **"Compare Policies"** → Select both policies → Select *Shorter Waiting Periods* → Click **"Compare Side-by-Side"**. Show judges that the underwriter (*Care Health* vs *Star Health*) is separated from the seller (*Direct* vs *Canara Bank*). Show the trade-off summary and click **"Export CSV"**.
6. **Scenario 1 Checker (Minute 3:30):**  
   Go to **"Claim Scenarios"** → Select Scenario 1 (Illness diagnosed 2 years post-purchase) → Click **"Evaluate Scenario"**. Explain the IRDAI legal truth: *A disease first diagnosed after purchase is not a pre-existing condition, but requires checking specific 24-month waiting periods.*
7. **Evidence-Grounded Assistant (Minute 4:15):**  
   Go to **"Ask PolicyLens"** → Click *"I bought this policy in Karnataka but need treatment in Maharashtra. What should I check?"*. Point out the 4 structured sections and exact clickable page citations `[CareSecure Direct, page 3]`.
8. **Wrap-up & Privacy (Minute 5:00):**  
   Show **"Hospital Network"** and **"AI & System Status"**. Conclude by emphasizing: *All documents and databases stay on the user's laptop. No sensitive health records were uploaded to cloud storage.*
