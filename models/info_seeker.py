from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Document(BaseModel):
    title: str
    url: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    excerpt: Optional[str] = None

class RetrievalResult(BaseModel):
    docs: List[Document]
    retrieval_log: str
    coverage_gaps: Optional[List[str]] = None

class NormalizedData(BaseModel):
    docs_norm: List[Document]
    key_facts: List[str]
    entities: List[str]
    timeline: Optional[List[str]] = None

class VerifiedFact(BaseModel):
    claim: str
    verdict: Literal["Supported", "Contradicted", "Unclear"]
    sources: List[str]
    confidence: Literal["High", "Medium", "Low"]

class FactCheckResult(BaseModel):
    facts_verified: List[VerifiedFact]
    unresolved: List[str]
    risk_notes: Optional[List[str]] = None

class SummaryResult(BaseModel):
    tldr_bullets: List[str] = Field(..., max_items=5)
    key_stats: Optional[List[str]] = None
    notable_quotes: Optional[List[str]] = None
    open_questions: Optional[List[str]] = None

class ExplanationResult(BaseModel):
    explanations: List[dict] = Field(description="List of concept explanations")
    explanation_paragraph: Optional[str] = None
    glossary: Optional[List[dict[str, str]]] = None

class ComparisonResult(BaseModel):
    comparison_table: dict
    tradeoffs: str
    recommendation: Optional[str] = None

class RefinedQueries(BaseModel):
    """A list of refined, keyword-focused search queries."""
    queries: List[str] = Field(description="1-3 optimized search queries.")

class ResearchPack(BaseModel):
    tldr: List[str]
    explanation: Optional[str] = None
    explanations: Optional[List[dict]] = None
    comparison: Optional[ComparisonResult] = None
    citations: List[Document]
    confidence_and_caveats: List[str]
    open_questions: Optional[List[str]] = None
