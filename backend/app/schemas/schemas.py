from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = "Policyholder"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_demo: bool
    gemini_consent: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ConsentUpdate(BaseModel):
    consent: bool

# --- Policy Schemas ---
class PolicyPageSchema(BaseModel):
    id: str
    page_number: int
    extracted_text: str
    extraction_method: str
    ocr_confidence: float
    has_tables: bool
    needs_review: bool

    class Config:
        from_attributes = True

class PolicyClauseSchema(BaseModel):
    id: str
    category: str
    heading: str
    verbatim_text: str
    plain_summary: str
    page_number: int
    extraction_status: str
    evidence_json: str

    class Config:
        from_attributes = True

class PolicyFieldSchema(BaseModel):
    id: str
    field_key: str
    field_label: str
    normalized_value: str
    status: str
    source_page: Optional[int] = None
    evidence_snippet: str

    class Config:
        from_attributes = True

class PolicySummaryResponse(BaseModel):
    id: str
    original_filename: str
    page_count: int
    insurer_name: str
    distributor_name: str
    product_name: str
    policy_period: Optional[str] = None
    sum_insured: Optional[str] = None
    premium: Optional[str] = None
    upload_date: datetime
    extraction_status: str
    ocr_used: bool
    ocr_confidence_avg: float
    is_demo: bool

    class Config:
        from_attributes = True

class PolicyDetailResponse(PolicySummaryResponse):
    pages: List[PolicyPageSchema] = []
    clauses: List[PolicyClauseSchema] = []
    fields: List[PolicyFieldSchema] = []

class ClauseUpdateRequest(BaseModel):
    heading: Optional[str] = None
    verbatim_text: Optional[str] = None
    plain_summary: Optional[str] = None
    extraction_status: Optional[str] = None

# --- Comparison Schemas ---
class ComparisonCreateRequest(BaseModel):
    policy_ids: List[str]
    title: Optional[str] = "Policy Comparison"
    priority_focus: Optional[str] = "balanced" # lower_cost, shorter_waiting_period, higher_coverage, lower_copay

class ComparisonColumnSchema(BaseModel):
    policy_id: str
    product_name: str
    insurer_name: str
    distributor_name: str
    fields: Dict[str, Dict[str, Any]] # field_key -> {value, status, source_page, evidence}

class ComparisonResponse(BaseModel):
    id: str
    title: str
    priority_focus: str
    tradeoff_summary: str
    columns: List[ComparisonColumnSchema]
    created_at: datetime

# --- Scenario Analysis Schemas ---
class DiseaseScenarioRequest(BaseModel):
    policy_id: str
    policy_start_date: Optional[str] = None # YYYY-MM-DD or approx
    first_diagnosis_date: Optional[str] = None # YYYY-MM-DD
    disease_name: Optional[str] = ""
    continuous_renewals: str = "yes" # yes, no, not_sure
    pre_existing_or_treated_prior: str = "no" # yes, no, not_sure
    treatment_state: Optional[str] = None
    hospital_name: Optional[str] = None

class DiseaseScenarioResponse(BaseModel):
    policy_id: str
    disease_name: str
    plain_explanation: str
    is_ped_assessment: str
    waiting_period_analysis: str
    missing_facts_to_verify: List[str]
    suggested_questions: List[str]
    relevant_clauses: List[Dict[str, Any]]
    disclaimer: str

class GeoScenarioRequest(BaseModel):
    policy_id: str
    policy_state: Optional[str] = "Karnataka"
    treatment_state: str = "Maharashtra"
    hospital_name: Optional[str] = None

class GeoScenarioResponse(BaseModel):
    policy_id: str
    policy_state: str
    treatment_state: str
    territorial_scope_analysis: str
    cashless_vs_reimbursement: str
    clauses_found: List[Dict[str, Any]]
    action_checklist: List[str]
    disclaimer: str

# --- Chat Schemas ---
class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    policy_id: Optional[str] = None # Optional single policy focus
    message: str

class SourceCitation(BaseModel):
    policy_id: str
    policy_name: str
    page_number: int
    snippet: str

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    message_text: str
    sources: List[SourceCitation] = []
    created_at: datetime

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    policy_id: Optional[str] = None
    created_at: datetime
    messages: List[ChatMessageResponse] = []

# --- Hospital Schemas ---
class HospitalEntrySchema(BaseModel):
    id: str
    hospital_name: str
    city: str
    state: str
    pincode: str
    network_type: str
    tier_category: str
    notes: str
    provider_name: str
    verified_date: str
    is_synthetic: bool

    class Config:
        from_attributes = True

class HospitalSearchResponse(BaseModel):
    query_city: Optional[str] = None
    query_name: Optional[str] = None
    total_found: int
    data_source_provider: str
    last_verified_date: str
    is_synthetic: bool
    results: List[HospitalEntrySchema]

# --- Health Schemas ---
class AIHealthResponse(BaseModel):
    status: str # "configured", "not configured", or "error"
    model: str
    consent_required: bool
    notice: str
