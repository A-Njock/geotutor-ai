from typing import Optional, List
from pydantic import BaseModel, Field

class SourceMetadata(BaseModel):
    """
    Metadata schema for ingested chunks.
    """
    source_filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(None, description="Book or standard title")
    author: Optional[str] = Field(None, description="Author or organization")
    page_number: Optional[int] = Field(None, description="Page number in original doc")
    section: Optional[str] = Field(None, description="Section/Chapter title")
    topic: Optional[str] = Field(None, description="Geotech topic (e.g., Foundations, Slopes)")

class RetrievalResult(BaseModel):
    """
    Structured response from the Librarian agent.
    """
    content: str
    metadata: SourceMetadata
    relevance_score: float

class CalculationRequest(BaseModel):
    """
    Schema for requests to the Engineer agent.
    """
    formula: str
    variables: dict[str, float]
    description: str
