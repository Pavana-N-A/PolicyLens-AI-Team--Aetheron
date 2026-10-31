import os
import sys
import unittest
import io
import fitz # PyMuPDF
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import init_db

class TestPolicyLensFullSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.test_email = f"test.user_{os.getpid()}@policylens.local"
        cls.test_password = "SecurePassword123!"

    def test_01_health_and_diagnostics(self):
        """1. Verify system health and local mode diagnostics"""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        res_ai = self.client.get("/api/health/ai")
        self.assertEqual(res_ai.status_code, 200)
        ai_data = res_ai.json()
        self.assertIn("status", ai_data)
        self.assertIn("notice", ai_data)
        print("  -> System Health: Healthy, Local Mode Supported")

    def test_02_registration_and_login(self):
        """2. Test user registration and authentication"""
        # Register
        reg_res = self.client.post(
            "/api/auth/register",
            json={
                "email": self.test_email,
                "password": self.test_password,
                "name": "Arjun Sharma"
            }
        )
        self.assertEqual(reg_res.status_code, 200)
        self.assertEqual(reg_res.json()["email"], self.test_email)

        # Login
        login_res = self.client.post(
            "/api/auth/login",
            json={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        self.assertIn("token", login_data)
        self.__class__.user_token = login_data["token"]
        print(f"  -> Registration and Login successful for {self.test_email}")

    def test_03_demo_login(self):
        """3. Test instant Demo Login for judges"""
        demo_res = self.client.post("/api/auth/demo-login")
        self.assertEqual(demo_res.status_code, 200)
        demo_data = demo_res.json()
        self.assertTrue(demo_data["user"]["is_demo"])
        self.assertIn("token", demo_data)
        self.__class__.demo_token = demo_data["token"]
        print("  -> Demo Login verified for hackathon judge access")

    def test_04_upload_digital_and_scanned_pdf(self):
        """4. Test PDF upload, digital extraction, and OCR fallback for scanned pages"""
        headers = {"Authorization": f"Bearer {self.user_token}"}

        # A. Upload Digital PDF
        demo_dir = os.path.join(os.path.dirname(__file__), "data", "demo_policies")
        p1_path = os.path.join(demo_dir, "PolicyLens_CareSecure_Direct.pdf")
        with open(p1_path, "rb") as f:
            pdf_bytes = f.read()

        res_upload1 = self.client.post(
            "/api/policies/upload",
            files={"file": ("CareSecure_Direct_Plan.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        self.assertEqual(res_upload1.status_code, 200)
        p1_data = res_upload1.json()
        self.assertIn("id", p1_data)
        self.assertFalse(p1_data["ocr_used"]) # Digital extraction was used
        self.__class__.policy1_id = p1_data["id"]
        print(f"  -> Uploaded digital PDF: {p1_data['product_name']} ({p1_data['page_count']} pages)")

        # B. Generate and upload a Scanned Image-Only PDF to test OCR pipeline
        scanned_doc = fitz.open()
        page = scanned_doc.new_page(width=595, height=842)
        # Create an image pixmap without alpha and insert into page without digital text
        img_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 300, 300), 0)
        img_pix.set_rect(fitz.IRect(0, 0, 300, 300), (240, 240, 240))
        page.insert_image(fitz.Rect(50, 50, 545, 750), pixmap=img_pix)
        scanned_bytes = scanned_doc.tobytes()
        scanned_doc.close()

        res_upload2 = self.client.post(
            "/api/policies/upload",
            files={"file": ("Scanned_Endorsement_Schedule.pdf", scanned_bytes, "application/pdf")},
            headers=headers
        )
        self.assertEqual(res_upload2.status_code, 200)
        p2_data = res_upload2.json()
        self.assertTrue(p2_data["ocr_used"]) # OCR was triggered because page had no digital text!
        self.assertEqual(p2_data["extraction_status"], "Review needed")
        self.__class__.policy2_id = p2_data["id"]
        print(f"  -> Uploaded scanned image PDF: triggered OCR pipeline, marked '{p2_data['extraction_status']}'")

    def test_05_inspect_and_edit_clause(self):
        """5. Inspect clauses and test editing uncertain extracted text"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        res = self.client.get(f"/api/policies/{self.policy1_id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertGreater(len(detail["clauses"]), 0)

        clause_to_edit = detail["clauses"][0]
        cid = clause_to_edit["id"]
        res_edit = self.client.put(
            f"/api/policies/{self.policy1_id}/clauses/{cid}",
            json={
                "heading": "Verified In-Patient Hospitalization",
                "plain_summary": "Policyholder verified: 100% covered without room rent penalty."
            },
            headers=headers
        )
        self.assertEqual(res_edit.status_code, 200)
        updated = res_edit.json()
        self.assertEqual(updated["heading"], "Verified In-Patient Hospitalization")
        print("  -> Clause inspection and manual review editing verified")

    def test_06_policy_comparison(self):
        """6. Test side-by-side policy comparison distinguishing underwriter from distributor"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        # Also upload Policy 2 (Canara Bank Bancassurance)
        demo_dir = os.path.join(os.path.dirname(__file__), "data", "demo_policies")
        p2_path = os.path.join(demo_dir, "PolicyLens_HealthProtect_CanaraBank.pdf")
        with open(p2_path, "rb") as f:
            pdf2_bytes = f.read()

        res_up3 = self.client.post(
            "/api/policies/upload",
            files={"file": ("Canara_HealthProtect_Bancassurance.pdf", pdf2_bytes, "application/pdf")},
            headers=headers
        )
        self.assertEqual(res_up3.status_code, 200)
        p3_id = res_up3.json()["id"]

        comp_res = self.client.post(
            "/api/comparisons",
            json={
                "policy_ids": [self.policy1_id, p3_id],
                "priority_focus": "shorter_waiting_period"
            },
            headers=headers
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.json()
        self.assertEqual(len(comp_data["columns"]), 2)
        self.assertIn("tradeoff_summary", comp_data)
        
        # Verify Underwriter vs Distributor separation
        col1 = comp_data["columns"][0]
        self.assertIn("insurer_name", col1["fields"])
        self.assertIn("distributor_name", col1["fields"])
        print("  -> Side-by-side comparison verified with trade-off insights")

    def test_07_scenarios_evaluation(self):
        """7. Test guided disease scenario and inter-state treatment check"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Disease scenario (2 years post-purchase)
        res_dis = self.client.post(
            "/api/scenarios/disease",
            json={
                "policy_id": self.policy1_id,
                "policy_start_date": "2023-01-01",
                "first_diagnosis_date": "2025-06-01",
                "disease_name": "Gall bladder calculi (stones)",
                "continuous_renewals": "yes",
                "pre_existing_or_treated_prior": "no"
            },
            headers=headers
        )
        self.assertEqual(res_dis.status_code, 200)
        dis_data = res_dis.json()
        self.assertIn("NOT a Pre-Existing Disease", dis_data["is_ped_assessment"])
        self.assertGreater(len(dis_data["suggested_questions"]), 0)
        print("  -> Disease scenario verified: post-purchase illness legal distinction accurate")

        # Geography scenario (Karnataka to Maharashtra)
        res_geo = self.client.post(
            "/api/scenarios/geography",
            json={
                "policy_id": self.policy1_id,
                "policy_state": "Karnataka",
                "treatment_state": "Maharashtra",
                "hospital_name": "Lilavati Hospital Mumbai"
            },
            headers=headers
        )
        self.assertEqual(res_geo.status_code, 200)
        geo_data = res_geo.json()
        self.assertIn("territorial_scope_analysis", geo_data)
        self.assertIn("cashless_vs_reimbursement", geo_data)
        print("  -> Inter-state treatment verified: separates territorial validity from cashless network")

    def test_08_local_grounded_ai_chat(self):
        """8. Test evidence-grounded chat in local mode (no Gemini key needed)"""
        headers = {"Authorization": f"Bearer {self.user_token}"}

        # Question 1: Inter-state query
        res_chat1 = self.client.post(
            "/api/chat",
            json={
                "policy_id": self.policy1_id,
                "message": "I bought this policy in Karnataka but need treatment in Maharashtra. What should I check?"
            },
            headers=headers
        )
        self.assertEqual(res_chat1.status_code, 200)
        data1 = res_chat1.json()
        self.assertIn("What the document says", data1["message_text"])
        self.assertIn("Simple explanation", data1["message_text"])
        self.assertIn("What this may mean", data1["message_text"])
        self.assertIn("What still needs confirmation", data1["message_text"])
        self.assertGreater(len(data1["sources"]), 0)
        print("  -> Evidence-grounded Chat Q1 verified with 4 structured sections and page citations")

        # Question 2: Post-purchase disease query
        res_chat2 = self.client.post(
            "/api/chat",
            json={
                "policy_id": self.policy1_id,
                "message": "I was healthy when I bought the policy but was diagnosed with a disease two years later. Which clauses matter?"
            },
            headers=headers
        )
        self.assertEqual(res_chat2.status_code, 200)
        data2 = res_chat2.json()
        self.assertIn("What the document says", data2["message_text"])
        self.assertGreater(len(data2["sources"]), 0)
        print("  -> Evidence-grounded Chat Q2 verified with clause retrieval")

    def test_09_hospital_search_and_demo_labels(self):
        """9. Test local hospital dataset search and synthetic data labels"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        res_hosp = self.client.get("/api/hospitals/search?city=Mumbai", headers=headers)
        self.assertEqual(res_hosp.status_code, 200)
        hosp_data = res_hosp.json()
        self.assertTrue(hosp_data["is_synthetic"])
        self.assertIn("SYNTHETIC DEMO DATA", hosp_data["last_verified_date"])
        self.assertGreater(hosp_data["total_found"], 0)
        print(f"  -> Hospital dataset verified: {hosp_data['total_found']} hospitals found, strictly labeled synthetic")

if __name__ == "__main__":
    unittest.main()
