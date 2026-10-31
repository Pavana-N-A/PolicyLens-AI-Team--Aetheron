import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), default="Policyholder")
    is_demo = Column(Boolean, default=False)
    gemini_consent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("Policy", back_populates="user", cascade="all, delete-orphan")
    comparisons = relationship("Comparison", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    hospital_imports = relationship("HospitalImport", back_populates="user", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_relative_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)
    page_count = Column(Integer, default=0)
    
    # Critical distinction from build spec:
    insurer_name = Column(String(255), default="Unknown Underwriter") # Actual risk-bearing underwriter
    distributor_name = Column(String(255), default="Direct / Unknown") # Seller / Bank / Hospital / Broker / Online
    product_name = Column(String(255), default="Health Insurance Plan")
    policy_period = Column(String(100), nullable=True)
    sum_insured = Column(String(100), nullable=True)
    premium = Column(String(100), nullable=True)
    
    upload_date = Column(DateTime, default=datetime.utcnow)
    extraction_status = Column(String(50), default="Uploaded") # Uploaded, Extracting, Review needed, Analysed, Failed
    ocr_used = Column(Boolean, default=False)
    ocr_confidence_avg = Column(Float, default=1.0)
    is_demo = Column(Boolean, default=False)

    user = relationship("User", back_populates="policies")
    pages = relationship("PolicyPage", back_populates="policy", cascade="all, delete-orphan")
    clauses = relationship("PolicyClause", back_populates="policy", cascade="all, delete-orphan")
    fields = relationship("PolicyField", back_populates="policy", cascade="all, delete-orphan")


class PolicyPage(Base):
    __tablename__ = "policy_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False) # 1-indexed
    extracted_text = Column(Text, default="")
    extraction_method = Column(String(50), default="digital") # digital, ocr, hybrid
    ocr_confidence = Column(Float, default=1.0)
    has_tables = Column(Boolean, default=False)
    needs_review = Column(Boolean, default=False)

    policy = relationship("Policy", back_populates="pages")


class PolicyClause(Base):
    __tablename__ = "policy_clauses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False) # coverage, exclusion, waiting_period, limits, copay_deductible, claims, geography, other
    heading = Column(String(255), nullable=False)
    verbatim_text = Column(Text, nullable=False)
    plain_summary = Column(Text, default="")
    page_number = Column(Integer, default=1)
    # State: Found in policy, Not found in uploaded document, Ambiguous – review needed, User-entered
    extraction_status = Column(String(50), default="Found in policy")
    evidence_json = Column(Text, default="{}") # JSON metadata: section, confidence, etc.

    policy = relationship("Policy", back_populates="clauses")


class PolicyField(Base):
    __tablename__ = "policy_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    field_key = Column(String(100), nullable=False) # e.g. sum_insured, room_rent_icu_limit, ped_waiting_period, copay
    field_label = Column(String(200), nullable=False)
    normalized_value = Column(Text, default="")
    status = Column(String(50), default="Found in policy") # Found in policy, Not found in uploaded document, Ambiguous – review needed, User-entered
    source_page = Column(Integer, nullable=True)
    source_clause_id = Column(String(36), nullable=True)
    evidence_snippet = Column(Text, default="")

    policy = relationship("Policy", back_populates="fields")


class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="Policy Comparison")
    priority_focus = Column(String(100), default="balanced") # lower_cost, shorter_waiting_period, higher_coverage, lower_copay
    tradeoff_summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="comparisons")
    policies = relationship("ComparisonPolicy", back_populates="comparison", cascade="all, delete-orphan")


class ComparisonPolicy(Base):
    __tablename__ = "comparison_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_id = Column(String(36), ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)

    comparison = relationship("Comparison", back_populates="policies")
    policy = relationship("Policy")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True) # Selected policy filter
    title = Column(String(255), default="Policy Question")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False) # user, assistant, system
    message_text = Column(Text, nullable=False)
    sources_json = Column(Text, default="[]") # JSON list of {policy_name, page_number, snippet, clause_id}
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class HospitalImport(Base):
    __tablename__ = "hospital_imports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_filename = Column(String(255), nullable=False)
    provider_name = Column(String(255), default="Insurer/TPA Network List")
    verified_date = Column(String(50), default="Not verified live")
    entry_count = Column(Integer, default=0)
    is_synthetic = Column(Boolean, default=True) # Synthetic demo data vs imported list
    import_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="hospital_imports")
    entries = relationship("HospitalEntry", back_populates="import_batch", cascade="all, delete-orphan")


class HospitalEntry(Base):
    __tablename__ = "hospital_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_id = Column(String(36), ForeignKey("hospital_imports.id", ondelete="CASCADE"), nullable=False)
    hospital_name = Column(String(255), nullable=False)
    city = Column(String(100), index=True, default="")
    state = Column(String(100), index=True, default="")
    pincode = Column(String(20), default="")
    network_type = Column(String(50), default="cashless") # cashless, reimbursement_only, blacklisted
    tier_category = Column(String(50), default="Standard")
    notes = Column(Text, default="")

    import_batch = relationship("HospitalImport", back_populates="entries")
