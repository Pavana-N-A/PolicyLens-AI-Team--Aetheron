import os
import sys
import json
from dotenv import load_dotenv

# Ensure backend .env is loaded
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.database import get_db
from app.models.models import User, Policy
from app.services.agent_service import agent_service
from app.services.gemini_service import gemini_service

def run_tests():
    db = next(get_db())
    user = db.query(User).first()
    if not user:
        print("ERROR: No user found in database.")
        return

    pmsby_policy = db.query(Policy).filter(Policy.product_name.like('%Suraksha%')).first()
    care_policy = db.query(Policy).filter(Policy.product_name.like('%Caresecure%')).first()

    print("=================================================================")
    print("PolicyLens Gemini Intelligence Automated Test Suite")
    print("=================================================================")
    ai_status = gemini_service.get_status()
    print(f"Gemini Configuration Status: {ai_status['status'].upper()}")
    print(f"Configured Model: {ai_status['model']}")
    print(f"Test User: {user.email}")
    print(f"PMSBY Policy ID: {pmsby_policy.id if pmsby_policy else 'None'}")
    print(f"Care Policy ID: {care_policy.id if care_policy else 'None'}")
    print("=================================================================\n")

    test_cases = [
        {
            "id": 1,
            "question": "What is the accidental death benefit?",
            "policy": pmsby_policy,
            "type": "Direct fact question"
        },
        {
            "id": 2,
            "question": "What is the sum insured?",
            "policy": pmsby_policy,
            "type": "Direct fact question"
        },
        {
            "id": 3,
            "question": "What is the waiting period?",
            "policy": care_policy,
            "type": "Waiting-period question"
        },
        {
            "id": 4,
            "question": "What are the major exclusions?",
            "policy": pmsby_policy,
            "type": "Exclusion question"
        },
        {
            "id": 5,
            "question": "Is diabetes covered?",
            "policy": care_policy,
            "type": "Coverage question"
        },
        {
            "id": 6,
            "question": "What is the difference between cashless and reimbursement?",
            "policy": care_policy,
            "type": "Explanation question"
        },
        {
            "id": 7,
            "question": "Can I receive treatment in another state?",
            "policy": care_policy,
            "type": "Scenario question"
        },
        {
            "id": 8,
            "question": "What is the international pet travel insurance benefit?",
            "policy": pmsby_policy,
            "type": "Unsupported / Absent question"
        }
    ]

    results = []

    for tc in test_cases:
        pol = tc["policy"]
        pol_id = pol.id if pol else None
        pol_name = pol.product_name if pol else "All Policies"

        print(f"--- [Test {tc['id']}: {tc['type']}] ---")
        print(f"Question: \"{tc['question']}\"")
        print(f"Selected Policy: {pol_name}")

        try:
            res = agent_service.process_chat_message(
                db=db,
                user_id=user.id,
                message=tc["question"],
                policy_id=pol_id,
                user_consented=True
            )

            answer = res.get("message_text", "")
            sources = res.get("sources", [])

            print(f"Sources Retrieved ({len(sources)}):")
            for s in sources[:2]:
                print(f"  * [{s.get('policy_name')}, Page {s.get('page_number')}]: {s.get('snippet', '')[:90]}...")

            print("\nGenerated Response:")
            print(answer)
            print("-" * 65 + "\n")

            results.append({
                "id": tc["id"],
                "question": tc["question"],
                "policy": pol_name,
                "answer": answer,
                "sources_count": len(sources),
                "passed": len(answer.strip()) > 20 and not answer.startswith("The following relevant clauses were located")
            })
        except Exception as e:
            print(f"ERROR: {e}\n" + "-" * 65 + "\n")
            results.append({
                "id": tc["id"],
                "question": tc["question"],
                "policy": pol_name,
                "error": str(e),
                "passed": False
            })

    print("=================================================================")
    print("Test Suite Summary:")
    passed_count = sum(1 for r in results if r.get("passed"))
    print(f"Total Tests: {len(results)} | Passed: {passed_count} | Failed: {len(results) - passed_count}")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
