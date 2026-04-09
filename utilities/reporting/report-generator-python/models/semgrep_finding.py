from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import IntEnum


class BusinessCriticality(IntEnum):
    VERY_LOW = 1   # BC1
    LOW = 2        # BC2
    MEDIUM = 3     # BC3
    HIGH = 4       # BC4
    VERY_HIGH = 5  # BC5


class SemgrepLevel(IntEnum):
    SL1 = 1  # Basic scan completion
    SL2 = 2  # <=5 Critical + score >=60
    SL3 = 3  # 0 Critical, <=10 High + score >=70 (Enterprise Ready)
    SL4 = 4  # 0 Critical, <=3 High + score >=80
    SL5 = 5  # 0 Critical, 0 High + score >=90 (Veracode VL compliant)


@dataclass
class SemgrepFinding:
    id: str
    rule_id: str
    rule_name: str
    path: str
    start_line: int
    severity: str  # 'Critical', 'High', 'Medium', 'Low'
    message: str
    description: str
    category: str
    found_at: datetime
    status: str  # 'Open', 'Fixed', 'Ignored'
    project_name: str
    project_id: str
    exploitability_score: int  # 1-5
    remediation_effort: int    # 1-5
    owasp_category: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    assistant_recommendation: Optional[str] = None
    triage_state: Optional[str] = None


@dataclass
class ScanMetadata:
    sast_completed: bool
    supply_chain_completed: bool
    secrets_completed: bool
    files_scanned: int
    scan_duration: int  # milliseconds
    engine_version: str


@dataclass
class SemgrepProject:
    name: str
    repository: str
    business_criticality: BusinessCriticality
    last_scanned: datetime
    findings: List[SemgrepFinding]
    scan_data: ScanMetadata
    project_id: Optional[str] = None
    repo_ref_id: Optional[str] = None
