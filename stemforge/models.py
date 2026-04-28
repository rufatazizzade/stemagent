"""StemForge — Data models for the stem agent specialization system.

Uses Pydantic for validation and serialization of all core data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class Finding(BaseModel):
    """A single finding produced by an agent during code analysis."""
    type: str = Field(..., description="Vulnerability type label")
    severity: str = Field(default="medium", description="Severity: low, medium, high, critical")
    file: str = Field(default="", description="Source file where the finding was detected")
    evidence: str = Field(default="", description="Code snippet or description of the issue")
    fix: str = Field(default="", description="Suggested remediation")


class AgentConfig(BaseModel):
    """Configuration for a specialized agent."""
    role: str = Field(..., description="Agent role description")
    domain: str = Field(..., description="Target domain")
    checklist: List[str] = Field(default_factory=list, description="Analysis checklist items")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="Expected output format")
    evaluation_target: str = Field(default="", description="What the agent is evaluated on")
    version: str = Field(default="0.1", description="Agent version")
    system_prompt: str = Field(default="", description="System prompt for the LLM")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DomainProfile(BaseModel):
    """Profile of a domain derived from task analysis."""
    domain_name: str
    task_type: str
    common_approach: str
    required_skills: List[str]
    possible_tools: List[str]
    output_schema: Dict[str, Any]
    evaluation_criteria: List[str]


class Strategy(BaseModel):
    """Specialist strategy generated from a domain profile."""
    checklist: List[str]
    output_format: Dict[str, Any]
    analysis_approach: str
    severity_levels: List[str] = Field(
        default_factory=lambda: ["low", "medium", "high", "critical"]
    )


class EvaluationResult(BaseModel):
    """Result of evaluating an agent against expected outputs."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class SafeguardDecision(BaseModel):
    """Decision from the safeguard system on whether to accept an evolved agent."""
    accepted: bool
    reason: str
    baseline_f1: float
    evolved_f1: float
    improvement: float


class IterationRecord(BaseModel):
    """Record of a single specialization iteration."""
    iteration: int
    f1: float
    improvement: float
    accepted: bool
    agent_version: str
