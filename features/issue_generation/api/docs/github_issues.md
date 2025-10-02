# GITHUB REST API

The GitHub REST API facilitates comprehensive issue management (Create, Read, Update, and pseudo-Delete/Closure) via repository-scoped endpoints, requiring the `{owner}` and `{repo}` path parameters in the request.[1]

### CRUD Endpoints and Permissions

| Operation                        | Method  | Path                                                                                            | Required Permission | Key Details                                                                                                                                                                                                                            |
| -------------------------------- | ------- | ----------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Create (C)**                   | `POST`  | `/repos/{owner}/{repo}/issues`                                                                  | `issues:write` [2]  | Requires a `title` in the request body.[3] Mutative actions cost **5 points** against the secondary rate limit.[2]                                                                                                                     |
| **Read (R)**                     | `GET`   | `/repos/{owner}/{repo}/issues/{issue_number}` (Single) or `/repos/{owner}/{repo}/issues` (List) | `issues:read` [2]   | List endpoints support filtering by `state`, `assignee`, `labels`, and sorting by `created`, `updated`, or `comments`.[3] Single issue requests support custom media types (`.raw+json`, `.html+json`, etc.) for content rendering.[3] |
| **Update (U)**                   | `PATCH` | `/repos/{owner}/{repo}/issues/{issue_number}`                                                   | `issues:write` [3]  | Allows modification of `title`, `body`, `assignees`, `labels` (full replacement), and `state` (`open` or `closed`).[3]                                                                                                                 |
| **Close/Archive (D-equivalent)** | `PATCH` | `/repos/{owner}/{repo}/issues/{issue_number}`                                                   | `issues:write` [3]  | Permanent deletion is not supported; closure is achieved by setting the `state` to `closed`. The optional `state_reason` can specify `completed`, `not_planned`, or `duplicate`.[3]                                                    |

### Lifecycle and Operational Notes

- **Locking:** Issues can be locked using `PUT /repos/{owner}/{repo}/issues/{issue_number}/lock`, requiring a mandatory `lock_reason` (e.g., `off-topic`, `spam`).[3] Unlocking uses the `DELETE` method on the same path.[3]
- **Rate Limits:** Mutative requests (`POST`, `PATCH`, `PUT`, `DELETE`) cost **5 points** in the secondary rate limit system, compared to 1 point for read (`GET`) requests.[2] Best practices recommend waiting at least one second between consecutive mutative requests to avoid secondary rate limiting.[2]
- **Documentation:** For comprehensive details on all associated endpoints, including comments, assignees, and labels, consult the main GitHub REST API Issues documentation.[3]

- [Official Doc & Source](https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api)
- HTTP Method Operation Category Point Cost (Per Request) Secondary Limit Constraint
  GET, HEAD, OPTIONS Read/Idempotent 1 point
  Max 900 points/minute/endpoint

POST, PATCH, PUT, DELETE Mutative/Write 5 points
Max 900 points/minute/endpoint

| Operation                    | Cost per request | Max Point Limit                   |
| ---------------------------- | ---------------- | --------------------------------- |
| **GET, HEAD, OPTIONS**       | `1 point`        | `Max 900 points/minute/endpoint ` |
| **POST, PATCH, PUT, DELETE** | `5 Points`       | `Max 900 points/minute/endpoint`  |

---

## Secure Initialization of the GitHub Client (PyGitHub)

For Python development targeting the GitHub REST API, the community-accepted and widely used client library is **PyGitHub**.[1, 2] Utilizing a client library is essential as it handles HTTP requests, JSON parsing, and object abstraction, which greatly simplifies complex operations like iterating over repositories or modifying issue fields.[1]

### The Authentication Mandate

While you can access public repository information without authentication, such requests are subject to an extremely low rate limit (typically 60 requests per hour).[3] For any meaningful automation, creation, or update (mutative) operation, **authenticated access is mandatory**, granting a much higher primary rate limit (standard 5,000 requests per hour).[3]

Authentication is managed via Personal Access Tokens (PATs) using the `github.Auth.Token` class.[1, 4]

### Required Environment Variables and Security

To maintain security and prevent credentials from being committed to source control, the authentication token must be injected dynamically via environment variables.

| Variable Name        | Purpose                         | Description                                                                                                                                 |
| -------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **`GITHUB_TOKEN`**   | **Mandatory** token storage.    | This is the ecosystem standard variable for storing a PAT or App token. The application retrieves this value at runtime.[2, 5]              |
| **`GITHUB_API_URL`** | **Optional** for GHE instances. | Used to dynamically specify the base URL when connecting to a private GitHub Enterprise instance (e.g., `https://your-ghe-host/api/v3`).[1] |

### Client Setup: Python Implementation

The client setup requires importing the main `Github` class and the `Auth` submodule. The process involves three steps:

1.  Securely retrieve the token from the environment.
2.  Create the `Auth.Token` object.
3.  Instantiate the `Github` client, optionally specifying a custom URL for GitHub Enterprise.

#### 1\. Core Authentication Setup (Public GitHub)

This snippet demonstrates the robust, secure method of initializing the client for the public GitHub API (`https://api.github.com`), including explicit error handling for missing environment variables.

```python
import os
from github import Github, Auth

# --- Step 1: Securely Retrieve Token ---
# The token is retrieved from the GITHUB_TOKEN environment variable.
TOKEN = os.environ.get("GITHUB_TOKEN") [2]

if not TOKEN:
    # A robust client should fail explicitly if credentials are missing
    raise EnvironmentError("The GITHUB_TOKEN environment variable is required for authenticated API access.")

# --- Step 2: Create the Authentication Object ---
# Use the token value to create a Token-based authentication instance.
auth = Auth.Token(TOKEN) [4]

# --- Step 3: Instantiate the Client ---
# The client object 'g' manages the connection and session.
g = Github(auth=auth) [1]

print("Successfully initialized GitHub client for user:", g.get_user().login)

# Example usage: List user's repositories
# for repo in g.get_user().get_repos():
#     print(repo.name)
```

#### 2\. Advanced Configuration (GitHub Enterprise)

If you need to connect to a private GitHub Enterprise (GHE) instance, you must supply the `base_url` parameter during initialization, typically retrieved from the optional `GITHUB_API_URL` environment variable.[1]

```python
# Assuming 'auth' object was created successfully as shown above

GHE_URL = os.environ.get("GITHUB_API_URL")

if GHE_URL:
    # Instantiate the client pointing to the specific GHE host API URL
    g_enterprise = Github(base_url=GHE_URL, auth=auth) [1]
    print(f"Connected to GHE instance at: {GHE_URL}")
else:
    print("No GITHUB_API_URL specified. Connected to public GitHub.")
```

#### 3\. Resource Management Best Practice

For long-running scripts, server processes, or applications where connection pooling is a concern, it is a crucial best practice to explicitly close the connection when the client is no longer needed to release underlying HTTP resources.[1, 4]

```python
# To close the connection when finished:
g.close() [1]
```

This structure ensures authentication is handled securely via environment variables, provides flexibility for both public and enterprise environments, and sets up the foundation for interacting with GitHub objects like repositories and issues.

---

### I. API Queue Logic and Rate Limit Management

GitHub enforces a **secondary rate limit** to prevent abuse, which is managed via a point system applied to different HTTP methods.[1] Integrations must strictly follow two critical best practices to ensure continuous operation: avoiding concurrent requests and enforcing minimum delays between write operations.[1]

1.  **Cost of Operations:** Most read operations (`GET`) cost **1 point**, while mutative operations (`POST`, `PATCH`, `PUT`, `DELETE`), such as creating an issue or adding a label, cost **5 points**.[1]
2.  **Sequential Execution Mandate:** To prevent triggering concurrency-based secondary limits, it is best practice to run API requests serially, implementing a queue system.[1]
3.  **Mandatory Write Delay:** If executing a large sequence of mutative requests, the system is required to wait **at least one second** between each consecutive `POST`, `PATCH`, `PUT`, or `DELETE` request.[1]

The robust solution is a time-aware queue that serializes all requests, enforcing a 1-second delay specifically between any mutative calls to protect the application from temporary suspension due to abuse limits.

#### Code Snippet: Queue Logic Implementation (Conceptual Python)

This conceptual structure demonstrates the necessary serialization and conditional delay for mutative operations:

```python
import time
import requests # Or PyGitHub library client

# Secondary Rate Limit Best Practice: Minimum delay between WRITE operations
MUTATIVE_DELAY_SECONDS = 1

def execute_api_call(method: str, url: str, data: dict = None):
    # Perform the API request
    response = requests.request(method, url, json=data)

    # 1. Error Handling (Crucial for rate limits)
    if response.status_code == 429 or 'x-ratelimit-remaining' in response.headers and response.headers['x-ratelimit-remaining'] == '0':
        # Implement exponential backoff or honor 'retry-after' header [1]
        print("Rate limit hit. Retrying later...")
        #... retry logic...
        return None

    # 2. Sequential Delay Enforcement for Write Operations
    if method in:
        print(f"Mutative call executed. Waiting {MUTATIVE_DELAY_SECONDS}s...")
        time.sleep(MUTATIVE_DELAY_SECONDS) # Mandatory delay [1]

    return response

# Example: Execution
# execute_api_call('POST', 'https://api.github.com/repos/user/repo/issues', {'title': 'New Issue 1'})
# execute_api_call('PATCH', 'https://api.github.com/repos/user/repo/issues/1', {'body': 'Updated Body'})
# execute_api_call('GET', 'https://api.github.com/repos/user/repo/issues/1') # No delay needed after GET
```

### II. Issue Data Transfer Object (DTO) Definitions

When creating or updating issues, the request body must conform to specific fields, representing the desired state of the Issue resource. This acts as the DTO (Data Transfer Object) for issue submission.

The minimum requirement to create an issue is the `title`.[1] Full issue definition requires parameters for core content and relationships (metadata).

| Field                       | Type             | Description                                                             | Required?        | API Endpoint for Management                                                       |
| --------------------------- | ---------------- | ----------------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------------- |
| `title`                     | string           | The required summary of the issue.                                      | Yes (Create) [2] | `POST` or `PATCH` /issues                                                         |
| `body`                      | string           | The full markdown content of the issue description.                     | Optional [2]     | `POST` or `PATCH` /issues                                                         |
| `labels`                    | array of strings | A list of label names to associate with the issue.                      | Optional [2]     | `POST` or `PATCH` /issues (Full replacement) [2], `POST` /issues/{num}/labels [1] |
| **Relationships**           |                  |                                                                         |                  |                                                                                   |
| `assignees`                 | array of strings | A list of user logins to assign to the issue.                           | Optional [2]     | `POST` or `PATCH` /issues [2], `DELETE` /issues/{num}/assignees [1]               |
| **Dependency (Blocked By)** | N/A              | Defines issues that currently block the completion of the target issue. | N/A              | `POST` /issues/{num}/dependencies/blocked_by [1]                                  |

**Note on Labels:** When using the `labels` field in a primary `PATCH` request, the provided array **completely replaces** the existing list of labels.[2] Granular label additions or removals are managed via dedicated sub-endpoints like `POST /repos/{owner}/{repo}/issues/{issue_number}/labels`.[1]

### III. Required Environment Variables

The queue and execution logic relies on a valid, authenticated client. This setup requires the same essential environment variable used for secure client initialization:

| Variable Name      | Purpose                                                                                               | Required Access                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **`GITHUB_TOKEN`** | Stores the authentication token (PAT or App Token) required for making authenticated API calls.[3, 4] | Must have `issues:write` permission for all mutative operations.[2] |

source and docs - https://docs.github.com/en/rest , https://docs.github.com/rest/issues/issues , https://docs.github.com/actions/reference/authentication-in-a-workflow
