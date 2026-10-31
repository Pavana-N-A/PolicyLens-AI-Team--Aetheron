# PolicyLens – Working Prototype

**Intelligent Insurance Policy Understanding & Risk Navigator**  
*Local-First InsurTech Decision-Support System*

---

## 1. Overview & Core Mission

PolicyLens helps consumers understand and compare dense health insurance contracts. It accepts policy PDFs, extracts contract wording page-by-page, organizes clauses, explains them in simple language, compares policies side-by-side, evaluates real-world claim scenarios, and answers policyholder questions grounded strictly in retrieved document evidence.

### Key Insurance Truths Demonstrated
- **Post-Purchase Illness:** A disease first diagnosed 2–3 years after purchase is **not a Pre-Existing Disease (PED)** under IRDAI guidelines, but is also **not automatically covered**. It must be evaluated against initial 30-day waiting periods, 24-month specific ailment waiting periods (e.g. cataract, hernia, stones), continuous renewal history, disclosures, and exclusions.
- **Inter-State Hospitalization:** Buying a policy in Karnataka and getting admitted in Maharashtra involves two distinct checks:
  1. *Territorial Scope:* Pan-India coverage makes the treatment contractually eligible.
  2. *Cashless Hospital Empanelment:* If the hospital is not on the active network list, the patient uses the **reimbursement pathway** rather than being denied coverage.
- **Underwriter vs. Distributor Channel:** A policy sold by Canara Bank or Apollo Hospitals is underwritten by a licensed risk carrier (such as Star Health or Care Health). The prototype stores and evaluates the risk underwriter separately from the sales channel.

---

## 2. Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19 + Vite + TypeScript | Interactive InsurTech dashboard, side-by-side comparison, claim scenario checker, and chat |
| **Backend** | Python 3.13 + FastAPI + Uvicorn | RESTful API boundary, PDF parsing, OCR routing, and tool orchestration |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | Digital text extraction page-by-page, table detection, and page rendering |
| **OCR Pipeline** | PaddleOCR / Tesseract / Fallback | Swappable OCR behind `ocr_service.py` for scanned image pages |
| **Database** | SQLite + SQLAlchemy | Local relational database at `prototype/backend/data/db/policylens.db` |
| **Clause Index** | SQLite FTS5 Full-Text Search | BM25-ranked keyword search across all extracted policy pages |
| **AI Synthesis** | Google Gemini API (`google-genai` SDK) | Grounded 4-section synthesis with inline page citations `[Policy, page X]` |
| **Storage** | Local File System | Original PDFs preserved in `prototype/backend/data/uploads/` |

---

## 3. Quick Start on Windows

### Prerequisites
1. **Python 3.11+** installed (accessible via `py` or `python`).
2. **Node.js LTS** (v20+ or v24+) and `npm` installed.

### Option A: One-Click Startup (Recommended)
Double-click or run:
```cmd
prototype\start_policylens.bat
```
This script checks the virtual environment, launches the FastAPI backend on `http://127.0.0.1:8000`, starts the Vite frontend on `http://localhost:5173`, and opens your default browser.

### Option B: Manual Startup

#### Step 1: Start Backend
```cmd
cd prototype\backend
.\venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
- API is live at: `http://127.0.0.1:8001`
- Interactive Swagger docs at: `http://127.0.0.1:8001/docs`

#### Step 2: Start Frontend (in a separate terminal)
```cmd
cd prototype\frontend
npm run dev
```
- Open your browser at: `http://localhost:5173`

---

## 4. Google Gemini API Configuration

1. Visit [Google AI Studio](https://aistudio.google.com/) and generate an API key.
2. Open `prototype/backend/.env` in any text editor:
   ```env
   GEMINI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. Save the file and restart the backend server.
4. **Privacy Notice:** The frontend displays an explicit AI consent banner. Only extracted clause snippets relevant to the question are sent for synthesis. If Gemini is not configured, PolicyLens runs in **Local Deterministic Mode** using exact SQLite FTS5 clause excerpts.

---

## 5. Demonstration Walkthrough (for Hackathon Judges)

1. **Sign In:** Click **"Instant Demo Login"** on the login page for one-click judge access.
2. **Seed Demo Policies:** On the Dashboard, click **"Load Demo Policies"**. Two synthetic policy PDFs are automatically imported:
   - *CareSecure Direct Comprehensive Health Plan* (Risk carrier: Care Health Insurance Limited, Direct Channel, ₹10L SI, no room rent capping, 36m PED wait, 0% co-pay).
   - *Canara HealthProtect Bancassurance Scheme* (Risk carrier: Star Health, Distributor: Canara Bank, ₹5L SI, 1% room rent cap with proportionate deductions, 24m PED wait, 20% zonal co-pay).
3. **Inspect Clauses & OCR:** Go to **"My Policies"** and click **"Inspect Clauses"**. View verbatim contractual text, plain explanations, page numbers, and manual editing options.
4. **Compare Policies:** Open **"Compare Policies"**, select both demo policies, choose an evaluation priority (e.g. *Shorter Waiting Periods* or *Lowest Out-of-Pocket*), and click **"Compare Side-by-Side"**. Notice that underwriters are separated from distributor brands. Export comparison to CSV if desired.
5. **Scenario 1 (Disease After Purchase):** Go to **"Claim Scenarios"** → **"Scenario 1"**. Enter:
   - Policy Inception: `2023-01-01`
   - Diagnosis Date: `2025-06-01`
   - Condition: `Gall bladder stones`
   - Click **"Evaluate Scenario"** to inspect the legal distinction between pre-existing conditions and post-purchase illnesses, specific 24-month waiting periods, and questions for the insurer.
6. **Scenario 2 (Inter-State Treatment):** Switch to **"Scenario 2"**. Set purchase in `Karnataka` and hospital in `Maharashtra`. Inspect the territorial scope validity vs cashless network hospital empanelment.
7. **Hospital Network:** Go to **"Hospital Network"** and search for `Lilavati` or `Mumbai`. Review the synthetic demo network dataset with source verification notice.
8. **Ask PolicyLens:** Go to **"Ask PolicyLens"** and click any of the prompt chips (e.g. *"I bought this policy in Karnataka but need treatment in Maharashtra. What should I check?"*). View structured responses citing exact page numbers.

---

## 6. Running Tests

### Backend Unit Tests
```cmd
cd prototype\backend
.\venv\Scripts\python.exe test_backend.py
```
*Tests 9 automated suites including health endpoints, auth/demo login, PDF extraction, FTS5 indexing, comparison trade-offs, disease & geography scenario calculations, and hospital search.*

### Frontend Typecheck & Build
```cmd
cd prototype\frontend
npm run build
```
*Builds production Vite bundle and confirms zero TypeScript or lint errors.*

---

## 7. Local File Locations

- **SQLite Database:** `prototype/backend/data/db/policylens.db`
- **Original Uploaded PDFs:** `prototype/backend/data/uploads/<user_id>/`
- **Synthetic Demo Policies:** `prototype/backend/data/demo_policies/`
- **Local Hospital Dataset:** `prototype/backend/data/hospital_lists/`
