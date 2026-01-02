from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional

class InvocationIngest(BaseModel):
    function_name: str
    invocation_id: str
    request_id: Optional[str] = None
    timestamp: datetime
    cold_start: bool
    init_duration_ms: Optional[float] = None
    execution_duration_ms: float
    billed_duration_ms: Optional[float] = None
    memory_used_mb: Optional[int] = None
    memory_allocated_mb: Optional[int] = None
    module_timings: Optional[Dict[str, float]] = None
    runtime_version: Optional[str] = None
    architecture: Optional[str] = None

class IngestResponse(BaseModel):
    status: str = "ok"
    invocation_id: str
