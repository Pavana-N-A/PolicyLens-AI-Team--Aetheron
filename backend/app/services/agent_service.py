import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.models import Policy, PolicyPage, PolicyClause, ChatSession, ChatMessage
from app.services.retrieval_service import retrieval_service
from app.services.gemini_service import gemini_service
from app.services.comparison_service import comparison_service
from app.services.scenario_service import scenario_service
from app.services.hospital_service import hospital_service

class AgentService:
    """
    Backend orchestrator implementing the 7 specified domain tools:
    1. search_policy_clauses(policy_ids, query)
    2. get_policy_summary(policy_id)
    3. compare_policies(policy_ids, selected_fields)
    4. analyze_disease_scenario(policy_id, scenario_inputs)
    5. check_geographical_scope(policy_id, treatment_state)
    6. search_hospital_dataset(provider, city, hospital_name)
    7. explain_claim_process(policy_id)
    """

    # --- Tool 1 ---
    @staticmethod
    def search_policy_clauses(db: Session, policy_ids: List[str], query: str) -> List[Dict[str, Any]]:
        return retrieval_service.search_policy_clauses(db, query=query, policy_ids=policy_ids, limit=5)

    # --- Tool 2 ---
    @staticmethod
    def get_policy_summary(db: Session, policy_id: str) -> Dict[str, Any]:
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return {}
        return {
            "policy_id": policy.id,
            "product_name": policy.product_name,
            "insurer_name": policy.insurer_name,
            "distributor_name": policy.distributor_name,
            "page_count": policy.page_count,
            "clauses": [
                {
                    "category": c.category,
                    "heading": c.heading,
                    "verbatim_text": c.verbatim_text,
                    "plain_summary": c.plain_summary,
                    "page_number": c.page_number,
                    "status": c.extraction_status
                }
                for c in policy.clauses
            ]
        }

    # --- Tool 3 ---
    @staticmethod
    def compare_policies(db: Session, policy_ids: List[str], selected_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        return comparison_service.compare_policies(db, policy_ids=policy_ids)

    # --- Tool 4 ---
    @staticmethod
    def analyze_disease_scenario(db: Session, policy_id: str, scenario_inputs: Dict[str, Any]) -> Dict[str, Any]:
        return scenario_service.analyze_disease_scenario(
            db=db,
            policy_id=policy_id,
            policy_start_date=scenario_inputs.get("policy_start_date"),
            first_diagnosis_date=scenario_inputs.get("first_diagnosis_date"),
            disease_name=scenario_inputs.get("disease_name"),
            continuous_renewals=scenario_inputs.get("continuous_renewals", "yes"),
            pre_existing_or_treated_prior=scenario_inputs.get("pre_existing_or_treated_prior", "no")
        )

    # --- Tool 5 ---
    @staticmethod
    def check_geographical_scope(db: Session, policy_id: str, treatment_state: str = "Maharashtra", policy_state: str = "Karnataka") -> Dict[str, Any]:
        return scenario_service.check_geographical_scope(
            db=db,
            policy_id=policy_id,
            policy_state=policy_state,
            treatment_state=treatment_state
        )

    # --- Tool 6 ---
    @staticmethod
    def search_hospital_dataset(db: Session, user_id: str, city: Optional[str] = None, hospital_name: Optional[str] = None) -> Dict[str, Any]:
        return hospital_service.search_hospitals(db, user_id=user_id, city=city, hospital_name=hospital_name)

    # --- Tool 7 ---
    @staticmethod
    def explain_claim_process(db: Session, policy_id: str) -> Dict[str, Any]:
        clauses = retrieval_service.search_policy_clauses(
            db,
            query="cashless reimbursement pre-authorisation notice document submit deadline emergency planned",
            policy_ids=[policy_id],
            limit=4
        )
        return {
            "policy_id": policy_id,
            "claim_clauses": clauses
        }

    @classmethod
    def classify_question_type(cls, query: str) -> str:
        """Classifies the user's question into one of the 6 domain types for optimized retrieval."""
        lq = query.lower()
        if any(w in lq for w in ["karnataka", "maharashtra", "state", "travel", "territorial", "diagnosed later", "after purchase", "scenario"]):
            return "scenario"
        if any(w in lq for w in ["waiting period", "ped", "pre-existing", "initial waiting"]):
            return "waiting_period"
        if any(w in lq for w in ["hospital", "cashless", "reimbursement", "empanelled", "network"]):
            return "hospital_network"
        if any(w in lq for w in ["exclude", "exclusion", "not covered", "permanent exclusion"]):
            return "exclusion"
        if any(w in lq for w in ["covered", "cover", "diabetes", "maternity", "cataract", "ayush"]):
            return "coverage"
        if any(w in lq for w in ["explain", "difference between", "what is cashless", "what is reimbursement", "meaning"]):
            return "explanation"
        return "direct_fact"

    # --- Intent Orchestrator ---
    @classmethod
    def process_chat_message(
        cls,
        db: Session,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        user_consented: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrates tool selection, evidence retrieval, citation assembly,
        and grounded answer generation.
        """
        # Ensure or create session
        session = None
        if session_id:
            session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not session:
            session = ChatSession(
                user_id=user_id,
                policy_id=policy_id,
                title=message[:40] + ("..." if len(message) > 40 else "")
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # Save incoming user message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            message_text=message,
            sources_json="[]"
        )
        db.add(user_msg)
        db.commit()

        # Gather target policies
        target_policy_ids = [policy_id] if policy_id else []
        if not target_policy_ids:
            user_policies = db.query(Policy).filter(Policy.user_id == user_id).all()
            target_policy_ids = [p.id for p in user_policies]

        lower_query = message.lower()

        # Identify question type for query optimization
        q_type = cls.classify_question_type(message)

        # Retrieve relevant policy clauses
        ev_list = retrieval_service.search_policy_clauses(db, message, target_policy_ids, limit=4)

        # Additional domain context for hospital network scenario
        if q_type == "hospital_network" or any(w in lower_query for w in ["hospital", "network", "cashless"]):
            hosp_res = cls.search_hospital_dataset(db, user_id=user_id, hospital_name=message if len(message.split()) <= 4 else None)
            if hosp_res.get("results"):
                sample_hosp = hosp_res["results"][0]
                ev_list.append({
                    "policy_id": target_policy_ids[0] if target_policy_ids else "",
                    "policy_name": "Hospital Network Directory",
                    "page_number": 1,
                    "clause_heading": "Hospital Empanelment Dataset",
                    "snippet": f"Hospital dataset sample: {sample_hosp['hospital_name']} ({sample_hosp['city']}) status: {sample_hosp['network_type']}. Verified: {sample_hosp['verified_date']}."
                })

        # Synthesize evidence-grounded answer via Gemini (or intelligent local fallback)
        grounded = gemini_service.generate_grounded_answer(message, ev_list, user_consented=True)
        answer_text = grounded["answer"]
        sources = grounded.get("sources", [])

        # Save assistant message
        asst_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            message_text=answer_text,
            sources_json=json.dumps(sources)
        )
        db.add(asst_msg)
        db.commit()
        db.refresh(asst_msg)

        return {
            "id": asst_msg.id,
            "session_id": session.id,
            "role": "assistant",
            "message_text": answer_text,
            "sources": sources,
            "created_at": asst_msg.created_at
        }

agent_service = AgentService()
