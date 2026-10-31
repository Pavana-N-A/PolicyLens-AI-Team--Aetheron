import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import init_db

class TestPolicyLensBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_health_endpoints(self):
        # Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        # AI Health check
        res_ai = self.client.get("/api/health/ai")
        self.assertEqual(res_ai.status_code, 200)
        self.assertIn("status", res_ai.json())

        # OCR Health check
        res_ocr = self.client.get("/api/health/ocr")
        self.assertEqual(res_ocr.status_code, 200)
        self.assertIn("active_engine", res_ocr.json())

    def test_02_auth_demo_login(self):
        # Test Demo Login
        res = self.client.post("/api/auth/demo-login")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token", data)
        self.assertTrue(data["user"]["is_demo"])
        self.__class__.token = data["token"]

    def test_03_seed_demo_policies(self):
        # Seed synthetic demo policies
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post("/api/policies/seed-demo", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("policies", res.json())

    def test_04_list_and_get_policies(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.get("/api/policies", headers=headers)
        self.assertEqual(res.status_code, 200)
        policies = res.json()
        self.assertGreaterEqual(len(policies), 2)
        
        self.__class__.policy_ids = [p["id"] for p in policies]
        first_id = policies[0]["id"]

        # Detail view
        res_detail = self.client.get(f"/api/policies/{first_id}", headers=headers)
        self.assertEqual(res_detail.status_code, 200)
        detail = res_detail.json()
        self.assertIn("clauses", detail)
        self.assertIn("fields", detail)
        self.assertGreater(len(detail["clauses"]), 0)

    def test_05_policy_comparison(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post(
            "/api/comparisons",
            json={
                "policy_ids": self.policy_ids[:2],
                "priority_focus": "shorter_waiting_period"
            },
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        comp = res.json()
        self.assertEqual(len(comp["columns"]), 2)
        self.assertIn("tradeoff_summary", comp)
        self.assertIn("Actual Underwriter", comp["columns"][0]["fields"]["insurer_name"]["label"])

    def test_06_disease_scenario(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post(
            "/api/scenarios/disease",
            json={
                "policy_id": self.policy_ids[0],
                "policy_start_date": "2023-01-01",
                "first_diagnosis_date": "2025-06-01",
                "disease_name": "Gall bladder stones",
                "continuous_renewals": "yes",
                "pre_existing_or_treated_prior": "no"
            },
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("plain_explanation", data)
        self.assertIn("NOT a Pre-Existing Disease", data["is_ped_assessment"])

    def test_07_geography_scenario(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post(
            "/api/scenarios/geography",
            json={
                "policy_id": self.policy_ids[0],
                "policy_state": "Karnataka",
                "treatment_state": "Maharashtra",
                "hospital_name": "Lilavati Hospital Mumbai"
            },
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("territorial_scope_analysis", data)
        self.assertIn("cashless_vs_reimbursement", data)

    def test_08_evidence_based_chat(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post(
            "/api/chat",
            json={
                "policy_id": self.policy_ids[0],
                "message": "What is the waiting period for pre-existing disease and room rent limit?"
            },
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("message_text", data)
        self.assertIn("sources", data)

    def test_09_hospital_search(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.get("/api/hospitals/search?city=Mumbai", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_synthetic"])
        self.assertGreater(data["total_found"], 0)

if __name__ == "__main__":
    unittest.main()
