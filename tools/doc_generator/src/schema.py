from pydantic import BaseModel, Field
from typing import List


## Issue Schema
class Issue(BaseModel):
    """Always use this tool to structure your response to the user."""

    title: str = Field(description="A concise, descriptive title for the issue.")
    body: str = Field(
        description="A detailed description of the issue, explaining the problem or finding."
    )
    labels: List[str] = Field(
        description="A list of relevant tags or labels to categorize the issue (e.g., 'bug', 'enhancement', 'typo')."
    )
    dependency: List[str] = Field(
        description="A list of titles of other issues that this issue depends on or is related to."
    )


## Response Schema
class DocumentIssues(BaseModel):
    """The final structured output containing the original document and all extracted issues."""

    doc: str = Field(description="The full, original text document that was analyzed.")
    issues: List[Issue] = Field(
        description="A list of all identified issues, where each issue conforms to the Issue schema."
    )
