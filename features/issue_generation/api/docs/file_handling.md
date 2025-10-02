# File Handling for Issues Generation

When handling files, the best approach is to use a service that provides direct methods. File paths should not be exposed directly; instead, the service should manage them behind the scenes.

The required operations are:

- Save the LLM's output to a file (i.e., the generated issues)
- Read the file and parse it into the desired format (validated Pydantic models)
- Delete the temporary file

We should define a `file_service` with the following methods:

```python
from typing import List

class FileService:
    def save_temp(doc_id: int, content: List["Issue"]):
        """
        Save a list of Issue objects as JSON in `issues_{doc_id}.json`
        """
        pass
        # implementation

    def read_temp() -> List["Issue"]:
        """
        Read all files in the temp directory and parse them into a list of Issue objects
        """
        pass
        # implementation

    async def clear_temp():
        """
        Delete all temporary files from the temp directory
        """
        pass
        # implementation
```

Temporary files will be named based on the document’s ID. At any given time, the LLM will generate issues for only one document file, and there will be one corresponding temp file per document. All temp files will be stored in the `issues-temp/` folder.

Format of stored issues:

```json
[
	{
		"title": "Issue #1",
		"body": "Issue Body",
		"labels": ["sample label"],
		"dependency": ["Issue X"]
	}
]
```

Data shape for issues:

```python
from typing import List
from pydantic import BaseModel

class Issue(BaseModel):
    title: str
    body: str
    labels: List[str]
    dependency: List[str]
```

Use case example:

```python
issues = file_service.read_temp()
```
