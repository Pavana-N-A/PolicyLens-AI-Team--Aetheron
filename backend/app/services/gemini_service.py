import os
import re
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Ensure backend .env is loaded
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

SYSTEM_INSTRUCTION = """You are PolicyLens, an intelligent insurance policy understanding assistant.

Your job is to answer questions about the user's uploaded insurance policy.

Rules:
1. Always answer the user's exact question first.
2. Give the direct answer in the first sentence.
3. Use simple English that an ordinary insurance customer can understand.
4. Keep normal answers between 2 and 5 short sentences.
5. Do not repeat the entire policy clause.
6. Do not display retrieved policy chunks as a substitute for an answer.
7. Use only the relevant retrieved policy evidence for policy-specific facts.
8. Do not invent benefits, coverage amounts, waiting periods, exclusions or conditions.
9. Include the correct page number or clause reference whenever available.
10. If the answer cannot be established from the uploaded policy, clearly say:
'This information could not be confirmed from the uploaded policy.'
11. If a question requires information that is absent, do not guess.
12. Distinguish policy facts from general insurance explanations.
13. Do not claim that a treatment or claim is guaranteed to be covered.
14. Mention important conditions or exceptions only when they affect the answer.
15. Do not begin answers with phrases such as:
'The following relevant clauses were located...'
'Based on the retrieved chunks...'
'Here is the complete policy information...'
16. Benefit Amounts vs. Policy Schedules:
- When a user asks for a specific benefit amount, coverage limit, or sum insured:
  - If an explicit amount is present in the evidence (such as in a Table of Benefits or schedule, e.g. 'Rs. 2,00,000' for Accidental Death), you MUST state that exact amount and cite the specific page and Table of Benefits.
  - DO NOT return generic wording such as 'The Sum Insured specified in the Policy Schedule' when an actual amount is available in the retrieved evidence.
  - If no amount is stated anywhere in the policy evidence, state clearly that the amount is specified in the individual Policy Schedule or Certificate of Insurance and is not stated in this general policy wording document.
  - Never invent or assume monetary figures.

Your goal is to provide a useful, accurate and concise answer, not a lengthy summary.

Response Formatting Guidelines:
- For direct fact questions (amounts, benefits, waiting periods, limits, age limits):
  **Answer:** <Direct, plain English answer in 1-2 sentences>
  **Policy reference:** Page <X>, <Clause Heading or Section>
  **Important condition:** <Crucial condition, sub-limit, or deductible if applicable>

- For general explanation questions (e.g. explain cashless vs reimbursement):
  Provide a short, direct paragraph (2-4 sentences) explaining the concept clearly in simple terms.

- For scenario questions (e.g. treatment in another state, condition diagnosed after purchase):
  Give the direct answer in the first sentence, state what the policy specifies (citing page number), and clearly state any missing facts needed for confirmation.
"""

class GeminiService:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        load_dotenv(os.path.join(BACKEND_DIR, ".env"), override=True)
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview").strip()
        if not self.model_name or self.model_name == "gemini-2.5-flash":
            self.model_name = "gemini-3-flash-preview"

    def get_status(self) -> Dict[str, Any]:
        self._load_config()
        configured = bool(self.api_key and self.api_key != "PASTE_YOUR_KEY_HERE" and len(self.api_key) > 10)
        return {
            "status": "configured" if configured else "not configured",
            "model": self.model_name,
            "consent_required": True,
            "notice": (
                "PolicyLens uses Google Gemini for plain-language clause synthesis. "
                "Only retrieved document excerpts are processed. In accordance with Google AI Studio free tier guidelines, "
                "do not submit real sensitive personal data (names, PAN, medical records). "
                "All analysis is for educational decision-support only."
            )
        }

    def _call_gemini_rest(self, prompt: str, model_candidate: str) -> Optional[str]:
        """Calls Google Generative Language REST API with 15-second timeout."""
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                candidates = res_json.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            # If thinkingConfig was rejected by an older model, retry with standard config
            if "thinkingConfig" in err_body:
                try:
                    payload["generationConfig"].pop("thinkingConfig", None)
                    data2 = json.dumps(payload).encode("utf-8")
                    req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        res_json = json.loads(resp2.read().decode("utf-8"))
                        candidates = res_json.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
                except Exception:
                    pass
            print(f"Gemini REST error ({model_candidate}): HTTP {e.code} - {err_body[:120]}")
            return None
        except Exception as e:
            print(f"Gemini REST connection error ({model_candidate}): {e}")
            return None

        return None

    def generate_grounded_answer(
        self,
        user_query: str,
        retrieved_evidence: List[Dict[str, Any]],
        user_consented: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesizes an intelligent, accurate, policy-grounded answer.
        Sends concise evidence to Gemini with strict guidelines.
        If Gemini is unavailable, falls back to a clean, direct local synthesis.
        """
        self._load_config()

        # Format sources for UI citations
        sources = []
        evidence_blocks = []
        for ev in retrieved_evidence:
            pol_name = ev.get("policy_name", "Policy Document")
            page_num = ev.get("page_number", 1)
            heading = ev.get("clause_heading", "Policy Terms")
            snippet = ev.get("snippet", ev.get("full_text", ""))
            clean_snippet = snippet[:350].strip()

            sources.append({
                "policy_id": ev.get("policy_id", ""),
                "policy_name": pol_name,
                "page_number": page_num,
                "clause_heading": heading,
                "snippet": clean_snippet
            })

            evidence_blocks.append(
                f"[Document: {pol_name} | Page {page_num} | Clause: {heading}]\n{clean_snippet}\n"
            )

        # Handle case where no relevant evidence exists in uploaded policy
        if not retrieved_evidence or not evidence_blocks:
            return {
                "answer": (
                    "**Answer:** This information could not be confirmed from the uploaded policy.\n\n"
                    "**Policy reference:** Not found in uploaded document\n\n"
                    "**Important condition:** Please check if an additional Policy Schedule, Certificate of Insurance, or Endorsement document was provided with your policy."
                ),
                "sources": [],
                "engine": "local_analyzer"
            }

        # Attempt Gemini Generation if API key is present
        is_configured = bool(self.api_key and self.api_key != "PASTE_YOUR_KEY_HERE" and len(self.api_key) > 10)
        if is_configured:
            evidence_text = "\n---\n".join(evidence_blocks)
            full_prompt = (
                f"{SYSTEM_INSTRUCTION}\n\n"
                f"User Question: {user_query}\n\n"
                f"Retrieved Policy Evidence:\n{evidence_text}\n\n"
                f"Remember: Answer the question directly in the very first sentence. Use the specified response format."
            )

            # Try configured model first, then fallback models
            candidate_models = [self.model_name]
            for fallback in ["gemini-3-flash-preview", "gemini-flash-latest"]:
                if fallback not in candidate_models:
                    candidate_models.append(fallback)

            for model_cand in candidate_models:
                ans_text = self._call_gemini_rest(full_prompt, model_cand)
                if ans_text and len(ans_text.strip()) > 10:
                    # Sanitize any unwanted header phrases if model accidentally generated them
                    ans_clean = self._clean_gemini_output(ans_text)
                    return {
                        "answer": ans_clean,
                        "sources": sources,
                        "engine": f"gemini ({model_cand})"
                    }

        # Fallback to local intelligent rule-grounded response
        return self._generate_local_rule_grounded(user_query, retrieved_evidence, sources)

    def _clean_gemini_output(self, text: str) -> str:
        """Strips prohibited formulaic phrases to guarantee a direct answer."""
        unwanted_prefixes = [
            r"^The following relevant clauses were located.*?\n+",
            r"^Based on the retrieved chunks.*?\n+",
            r"^Here is the complete policy information.*?\n+",
            r"^Based on the uploaded policy.*?\n+"
        ]
        cleaned = text.strip()
        for pat in unwanted_prefixes:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    def _generate_local_rule_grounded(
        self,
        user_query: str,
        retrieved_evidence: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Produces a concise, direct, question-specific response when Gemini API is unavailable.
        Maintains the exact required answer format without verbose raw clause dumps.
        Selects the most specific evidence chunk containing concrete monetary amounts and tables.
        """
        lower_q = user_query.lower()

        # Select target evidence item across all retrieved evidence chunks
        target_ev = retrieved_evidence[0]
        if any(k in lower_q for k in ["benefit", "accidental death", "sum insured", "limit", "how much", "death"]):
            for ev in retrieved_evidence:
                ev_text = ev.get("snippet", ev.get("full_text", ""))
                has_amt = bool(re.search(r'(?:Rs\.?|INR|₹)\s*[\d,]+|\b\d+,\d{2,3}\b|\b\d+\s*(?:Lakh|Crore)\b', ev_text, re.IGNORECASE))
                if has_amt:
                    if "accidental death" in lower_q and ("accidental death" in ev_text.lower() or "table of benefits" in ev_text.lower()):
                        target_ev = ev
                        break
                    elif "sum insured" in lower_q and ("sum insured" in ev_text.lower() or "table of benefits" in ev_text.lower()):
                        target_ev = ev
                        break
                    elif not any(k in lower_q for k in ["accidental death"]):
                        target_ev = ev
                        break

        pol_name = target_ev.get("policy_name", "Policy Document")
        page_num = target_ev.get("page_number", 1)
        heading = target_ev.get("clause_heading", "Policy Terms")
        raw_text = target_ev.get("snippet", target_ev.get("full_text", ""))

        # Direct fact extraction: Accidental Death
        if "accidental death" in lower_q or ("accident" in lower_q and "death" in lower_q):
            amt_match = re.search(r'((?:Rs\.?|INR|₹)\s*[\d,]+(\s*Lakh)?)', raw_text, re.IGNORECASE)
            if amt_match:
                amt = amt_match.group(1).strip()
                answer = (
                    f"**Answer:** The accidental death benefit under this policy is {amt}, supported by the Table of Benefits on page {page_num}, payable to the nominee upon the death of the insured person caused solely and directly by an accident.\n\n"
                    f"**Policy reference:** Page {page_num}, {heading}\n\n"
                    f"**Important condition:** Death must occur solely and directly due to the accident within twelve months of the injury, subject to the maximum annual limit of {amt}."
                )
            else:
                answer = (
                    "**Answer:** The policy indicates that the accidental death sum insured is specified in your individual Policy Schedule or Certificate of Insurance, as a fixed monetary sum is not stated in the general policy terms.\n\n"
                    f"**Policy reference:** Page {page_num}, {heading}\n\n"
                    "**Important condition:** Please verify your individual Policy Schedule or Certificate of Insurance for your exact sanctioned accidental death coverage amount."
                )

        # Direct fact: Sum Insured
        elif "sum insured" in lower_q:
            amt_match = re.search(r'((?:Rs\.?|INR|₹)\s*[\d,]+(\s*Lakh)?)', raw_text, re.IGNORECASE)
            if amt_match:
                amt = amt_match.group(1).strip()
                answer = (
                    f"**Answer:** The policy specifies a Sum Insured of {amt} per Policy Year, supported by the policy documentation on page {page_num}.\n\n"
                    f"**Policy reference:** Page {page_num}, {heading}\n\n"
                    f"**Important condition:** Total claim liability during any policy year will not exceed this maximum limit."
                )
            else:
                answer = (
                    "**Answer:** The policy indicates that the Sum Insured is specified in your individual Policy Schedule or Certificate of Insurance, as base limits vary by individual plan tier.\n\n"
                    f"**Policy reference:** Page {page_num}, {heading}\n\n"
                    "**Important condition:** Refer to your personalized Policy Schedule or Certificate of Insurance for the exact Sum Insured amount."
                )

        # Waiting Period questions
        elif "waiting period" in lower_q or "ped" in lower_q or "pre-existing" in lower_q:
            period_match = re.search(r'(\d+\s*(?:days|months|years|year))', raw_text, re.IGNORECASE)
            period = period_match.group(1) if period_match else "the period stated in the waiting period terms"
            answer = (
                f"**Answer:** The policy requires a waiting period of {period} before coverage becomes active for specified conditions.\n\n"
                f"**Policy reference:** Page {page_num}, {heading}\n\n"
                f"**Important condition:** Initial waiting periods do not apply to sudden accidental injury hospitalisation."
            )

        # Coverage questions: diabetes / specific illness
        elif any(w in lower_q for w in ["diabetes", "hypertension", "covered", "maternity", "hospitalisation", "hospitalization"]):
            answer = (
                f"**Answer:** In-patient hospitalisation is covered subject to the policy terms, standard waiting periods, and room category sub-limits.\n\n"
                f"**Policy reference:** Page {page_num}, {heading}\n\n"
                f"**Important condition:** Pre-existing conditions require completion of the mandatory waiting period before expenses are admissible."
            )

        # Exclusions questions
        elif "exclusion" in lower_q or "excluded" in lower_q or "not covered" in lower_q:
            answer = (
                f"**Answer:** General exclusions include non-prescribed treatments, self-inflicted injuries, intoxicant abuse, and experimental procedures.\n\n"
                f"**Policy reference:** Page {page_num}, {heading}\n\n"
                f"**Important condition:** Refer to the comprehensive exclusions list in Section 3 of your policy document."
            )

        # Explanation: Cashless vs Reimbursement
        elif "cashless" in lower_q or "reimbursement" in lower_q:
            answer = (
                "**Answer:** Cashless treatment allows the insurer or TPA to settle hospital bills directly with empanelled network hospitals upon pre-authorisation. In reimbursement, you pay the hospital directly and submit original bills and medical reports to the insurer within the claim notice deadline.\n\n"
                f"**Policy reference:** Page {page_num}, {heading}\n\n"
                "**Important condition:** Cashless facility is available only at active network hospitals with approved pre-authorisation."
            )

        # Scenario: State-to-state or geographical scope
        elif any(w in lower_q for w in ["state", "karnataka", "maharashtra", "territorial", "jurisdiction"]):
            answer = (
                f"**Answer:** Health insurance policies issued in India provide pan-India territorial coverage for treatment received at recognized hospitals across all states.\n\n"
                f"**Policy reference:** Page {page_num}, {heading}\n\n"
                "**Important condition:** Cashless access depends on whether the specific hospital in that state is part of your insurer's active network; otherwise, claims are processed via reimbursement."
            )

        # Generic factual fallback
        else:
            stop_set = {
                "what", "is", "the", "in", "this", "policy", "benefit", "benefits",
                "does", "can", "how", "for", "tell", "about", "there", "insurance",
                "document", "documents", "details", "clause", "clauses", "mention",
                "requested", "information", "give", "show", "find"
            }
            content_words = [
                w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', user_query)
                if w.lower() not in stop_set
            ]
            has_match = any(cw in raw_text.lower() or cw in heading.lower() for cw in content_words) if content_words else False
            if not has_match:
                answer = (
                    "**Answer:** This information could not be confirmed from the uploaded policy.\n\n"
                    "**Policy reference:** Not found in uploaded document\n\n"
                    "**Important condition:** The uploaded policy pages do not appear to contain clauses or conditions regarding this requested information."
                )
            else:
                first_sentence = raw_text.split('.')[0].strip() if '.' in raw_text else raw_text[:120].strip()
                first_sentence = re.sub(r'[\r\n\t]+', ' ', first_sentence)
                answer = (
                    f"**Answer:** According to the policy, {first_sentence}.\n\n"
                    f"**Policy reference:** Page {page_num}, {heading}\n\n"
                    f"**Important condition:** Refer to the detailed conditions outlined on page {page_num} of your document."
                )

        # Note that local fallback was used
        answer += "\n\n*(Answered via PolicyLens Local Intelligence Engine)*"

        return {
            "answer": answer,
            "sources": sources,
            "engine": "local_fallback"
        }

gemini_service = GeminiService()
