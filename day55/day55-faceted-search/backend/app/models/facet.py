from pydantic import BaseModel
from typing import List, Dict, Any

class FacetValue(BaseModel):
    value: str
    count: int
    selected: bool = False

class Facet(BaseModel):
    name: str
    display_name: str
    values: List[FacetValue]
    facet_type: str = "categorical"  # categorical, numeric, temporal
    
class FacetSummary(BaseModel):
    total_logs: int
    facets: List[Facet]
    applied_filters: Dict[str, List[str]] = {}
