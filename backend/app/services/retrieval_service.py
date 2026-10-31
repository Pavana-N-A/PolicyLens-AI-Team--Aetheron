import re
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.models import Policy, PolicyPage, PolicyClause

STOP_WORDS = {
    "what", "is", "the", "in", "this", "policy", "does", "can", "how", "tell",
    "me", "about", "for", "and", "or", "a", "an", "of", "to", "with", "on",
    "are", "at", "by", "from", "any", "which", "will", "be", "there", "have",
    "has", "had", "do", "if", "under", "per", "insurance", "document", "details",
    "clause", "clauses"
}

class RetrievalService:
    @staticmethod
    def index_policy_pages(db: Session, policy_id: str, pages_data: List[Dict[str, Any]]) -> None:
        """Indexes all pages of a policy into SQLite FTS5"""
        try:
            # Delete any previous index for this policy
            db.execute(text("DELETE FROM policy_fts WHERE policy_id = :pid"), {"pid": policy_id})
            
            for p in pages_data:
                p_text = p.get("text", "")
                p_num = p.get("page_number", 1)
                if p_text.strip():
                    db.execute(
                        text("INSERT INTO policy_fts(policy_id, page_number, content) VALUES (:pid, :pnum, :content)"),
                        {"pid": policy_id, "pnum": p_num, "content": p_text}
                    )
            db.commit()
        except Exception as e:
            print(f"FTS5 indexing note/warning: {e}")
            db.rollback()

    @staticmethod
    def remove_policy_index(db: Session, policy_id: str) -> None:
        try:
            db.execute(text("DELETE FROM policy_fts WHERE policy_id = :pid"), {"pid": policy_id})
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def _is_benefit_amount_query(query: str) -> bool:
        lower_q = query.lower()
        amount_cues = [
            "amount", "benefit", "how much", "sum insured", "limit", "coverage",
            "death benefit", "accidental death", "payout", "cost", "rs", "inr",
            "rupees", "lakh", "crore", "maximum", "deductible", "copay", "sub-limit"
        ]
        return any(cue in lower_q for cue in amount_cues)

    @staticmethod
    def _extract_focused_snippet(text_content: str, keywords: List[str], window_chars: int = 500) -> tuple[str, str]:
        """
        Extracts a focused window of text starting near matching keywords.
        If matching keywords appear inside a structured table or benefit row,
        extracts the complete table header, matching benefit row, and notes,
        returning a clean snippet and specific clause heading.
        """
        if not text_content:
            return "", "Policy Terms"

        lower_content = text_content.lower()

        # Check if matching keywords appear in a structured table or benefit row
        lines = text_content.split('\n')
        best_table_idx = -1
        best_table_score = 0

        for idx, line in enumerate(lines):
            line_lower = line.lower()
            score = 0
            if "|" in line or "[benefit row]" in line_lower:
                score += 10
            if re.search(r'(?:rs\.?|inr|₹|\b\d+,\d{2,3}\b)', line_lower):
                score += 15
            for kw in keywords:
                if len(kw) > 3 and kw.lower() in line_lower:
                    score += 20
            if "accidental death" in line_lower:
                score += 40

            if score > best_table_score and ("|" in line or "[benefit row]" in line_lower or "[table" in line_lower):
                best_table_score = score
                best_table_idx = idx

        if best_table_score >= 30 and best_table_idx != -1:
            # Find start of table or header block (including header row above separator)
            start_idx = best_table_idx
            for back_i in range(best_table_idx - 1, max(-1, best_table_idx - 12), -1):
                b_line = lines[back_i].lower()
                if "| ---" in b_line and back_i > 0:
                    start_idx = back_i - 1
                    break
                elif "[table:" in b_line or "| sr. no" in b_line:
                    start_idx = back_i
                    break

            end_idx = min(len(lines), start_idx + 12)
            snippet_lines = [l for l in lines[start_idx:end_idx] if l.strip()]
            snippet = "\n".join(snippet_lines[:10]).strip()

            # Determine specific heading
            matched_line = lines[best_table_idx]
            heading = "Table of Benefits"
            if "accidental death" in matched_line.lower():
                heading = "Table of Benefits - Accidental Death"
            elif "disablement" in matched_line.lower():
                heading = "Table of Benefits - Permanent Disablement"
            elif "[table:" in snippet.lower():
                t_match = re.search(r'\[TABLE:\s*([^\]]+)\]', snippet, re.IGNORECASE)
                if t_match:
                    heading = t_match.group(1).strip()

            return snippet, heading

        # Standard non-table text snippet extraction
        earliest_idx = -1
        for kw in keywords:
            idx = lower_content.find(kw.lower())
            if idx != -1:
                if earliest_idx == -1 or idx < earliest_idx:
                    earliest_idx = idx

        if earliest_idx == -1:
            clean_text = text_content[:window_chars].strip() + ("..." if len(text_content) > window_chars else "")
            return clean_text, "Policy Terms"

        # Find clean start point (start of line or up to 40 chars prior)
        start = max(0, earliest_idx - 40)
        newline_before = text_content.rfind('\n', max(0, earliest_idx - 80), earliest_idx)
        if newline_before != -1:
            start = newline_before + 1

        end = min(len(text_content), start + window_chars)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text_content) else ""
        snippet = prefix + text_content[start:end].strip() + suffix

        # Heading determination
        lines_snip = [l.strip() for l in snippet.split('\n') if l.strip()]
        heading = "Policy Terms"
        for l in lines_snip:
            if len(l) < 60 and any(c.isupper() for c in l) and not l.startswith("|") and not l.startswith("..."):
                heading = l.strip("#*- ")
                break

        return snippet, heading

    @staticmethod
    def search_policy_clauses(
        db: Session,
        query: str,
        policy_ids: Optional[List[str]] = None,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieves highly relevant, policy-grounded evidence chunks with exact page citations.
        Uses SQLite FTS5 prefix search (exact conjunction AND, then ranking OR),
        combined with structured benefit-table prioritizing and policy_clauses matching.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        tokens = re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', clean_query)
        content_terms = [t.lower() for t in tokens if t.lower() not in STOP_WORDS]
        if not content_terms:
            content_terms = [clean_query.lower()]

        results: List[Dict[str, Any]] = []
        seen_keys = set()

        # Build policy filter SQL for FTS5
        policy_filter = ""
        params: Dict[str, Any] = {"limit": 10}
        if policy_ids and len(policy_ids) > 0:
            id_placeholders = []
            for i, pid in enumerate(policy_ids):
                p_key = f"pid_{i}"
                id_placeholders.append(f":{p_key}")
                params[p_key] = pid
            policy_filter = f" AND policy_id IN ({', '.join(id_placeholders)})"

        # Tier 1: Try FTS5 with all keywords required (AND) with prefix matching
        candidate_pages: List[tuple[str, int]] = []
        if len(content_terms) > 1:
            and_query = " AND ".join(f'{term}*' for term in content_terms[:4])
            params["and_q"] = and_query
            try:
                and_sql = f"""
                    SELECT policy_id, page_number, rank
                    FROM policy_fts
                    WHERE policy_fts MATCH :and_q {policy_filter}
                    ORDER BY rank
                    LIMIT :limit
                """
                rows = db.execute(text(and_sql), params).fetchall()
                for r in rows:
                    candidate_pages.append((r[0], r[1]))
            except Exception as e:
                print(f"FTS5 AND search note: {e}")

        # Tier 2: Supplement with OR query to capture pages with synonyms or related table headers
        if len(candidate_pages) < 8:
            or_query = " OR ".join(f'{term}*' for term in content_terms[:5])
            params["or_q"] = or_query
            try:
                or_sql = f"""
                    SELECT policy_id, page_number, rank
                    FROM policy_fts
                    WHERE policy_fts MATCH :or_q {policy_filter}
                    ORDER BY rank
                    LIMIT :limit
                """
                rows = db.execute(text(or_sql), params).fetchall()
                for r in rows:
                    if (r[0], r[1]) not in candidate_pages:
                        candidate_pages.append((r[0], r[1]))
            except Exception as e:
                print(f"FTS5 OR search note: {e}")

        # Benefit amount & coverage limit re-ranking:
        # Boost candidate pages that contain explicit monetary figures or structured benefit tables.
        # Demote generic wording referring to schedules without concrete amounts.
        is_benefit_query = RetrievalService._is_benefit_amount_query(clean_query)
        scored_candidates: List[tuple[float, str, int, PolicyPage]] = []

        for p_id, p_num in candidate_pages:
            page_rec = db.query(PolicyPage).filter(
                PolicyPage.policy_id == p_id,
                PolicyPage.page_number == p_num
            ).first()
            if not page_rec:
                continue

            text_raw = page_rec.extracted_text or ""
            text_lower = text_raw.lower()

            # Monetary amounts present? e.g. Rs. 2,00,000, 2,00,000, 2 Lakh
            has_amount = bool(re.search(r'(?:Rs\.?|INR|₹)\s*[\d,]+|\b\d+,\d{2,3}(?:,\d{3})*|\b\d+\s*(?:Lakh|Crore)\b', text_raw, re.IGNORECASE))
            has_table = bool("[table" in text_lower or "table of benefits" in text_lower or "[benefit row]" in text_lower or "| sum insured" in text_lower)

            # Direct proximity of query benefit phrase to explicit monetary figure
            has_direct_benefit_match = False
            for benefit_phrase in ["accidental death", "death benefit", "loss of both eyes", "loss of sight", "permanent disablement", "sum insured"]:
                if benefit_phrase in clean_query.lower() and benefit_phrase in text_lower:
                    if has_amount:
                        pat = rf'{benefit_phrase}.{{0,120}}(?:Rs\.?|INR|₹)\s*[\d,]+'
                        pat_rev = rf'(?:Rs\.?|INR|₹)\s*[\d,]+.{{0,120}}{benefit_phrase}'
                        if re.search(pat, text_lower, re.DOTALL) or re.search(pat_rev, text_lower, re.DOTALL):
                            has_direct_benefit_match = True
                            break

            # Deflecting generic wording: "as specified in the Policy Schedule/Certificate of Insurance" without concrete figures
            is_deflecting = bool(
                ("policy schedule" in text_lower or "schedule of coverage" in text_lower)
                and "as specified in" in text_lower
                and not has_amount
            )

            score = 0.0
            if is_benefit_query:
                if has_direct_benefit_match:
                    score += 60.0
                elif has_table and has_amount:
                    score += 35.0
                elif has_amount:
                    score += 15.0

                if is_deflecting:
                    score -= 25.0

            # Term match frequency
            tf = sum(text_lower.count(t) for t in content_terms)
            score += min(tf * 1.5, 20.0)

            scored_candidates.append((score, p_id, p_num, page_rec))

        # Sort candidate pages by calculated relevance score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Convert top scored candidate pages into rich evidence chunks
        for _, p_id, p_num, page_record in scored_candidates:
            if len(results) >= limit:
                break
            key = (p_id, p_num)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            policy = db.query(Policy).filter(Policy.id == p_id).first()
            page_text = page_record.extracted_text or ""
            clean_snippet, heading = RetrievalService._extract_focused_snippet(page_text, content_terms, window_chars=400)

            results.append({
                "policy_id": p_id,
                "policy_name": policy.product_name if policy else "Policy Document",
                "insurer_name": policy.insurer_name if policy else "Insurer",
                "distributor_name": policy.distributor_name if policy else "Direct",
                "page_number": p_num,
                "clause_heading": heading,
                "category": "benefits" if "table of benefits" in heading.lower() else "terms",
                "snippet": clean_snippet,
                "full_text": clean_snippet
            })

        # Tier 3: If still under limit, search structured policy_clauses table for high-scoring headings
        if len(results) < limit:
            try:
                clause_query = db.query(PolicyClause).join(Policy, PolicyClause.policy_id == Policy.id)
                if policy_ids and len(policy_ids) > 0:
                    clause_query = clause_query.filter(PolicyClause.policy_id.in_(policy_ids))

                all_candidate_clauses = clause_query.all()
                scored_clauses = []
                for c in all_candidate_clauses:
                    combined_text = f"{c.heading} {c.category} {c.verbatim_text}".lower()
                    score = sum(3 if kw in c.heading.lower() else (1 if kw in combined_text else 0) for kw in content_terms)
                    if score > 0:
                        scored_clauses.append((score, c))

                scored_clauses.sort(key=lambda x: x[0], reverse=True)
                for _, c in scored_clauses:
                    p = c.policy
                    key = (c.policy_id, c.page_number)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        snippet = c.verbatim_text[:400] + ("..." if len(c.verbatim_text) > 400 else "")
                        results.append({
                            "policy_id": c.policy_id,
                            "policy_name": p.product_name if p else "Policy Document",
                            "insurer_name": p.insurer_name if p else "Insurer",
                            "distributor_name": p.distributor_name if p else "Direct",
                            "page_number": c.page_number,
                            "clause_heading": c.heading,
                            "category": c.category,
                            "snippet": snippet,
                            "full_text": c.verbatim_text
                        })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"Clause search fallback note: {e}")

        return results[:limit]

retrieval_service = RetrievalService()
