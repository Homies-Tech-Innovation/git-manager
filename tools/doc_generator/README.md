# Doc Generator Tool

## Overview

This utility employs Docker Compose to manage and run a service that utilizes the **Gemini API** for automated documentation generation.

---

## Prerequisites

- **Docker** and **Docker Compose** installed.
- A **Gemini API Key** from Google.

---

## Setup and Configuration

### 1. Gemini API Key

The service requires the `GEMINI_API_KEY` environment variable for operation.

1. **Obtain Key:** Retrieve your API key from the [Google AI Studio documentation](https://aistudio.google.com/api-keys).

2. **Configuration File:** Create a file named **`.env`** in the root directory where your `docker-compose.yml` file is located (or in the `tool/doc_generator/` directory if that is your execution context).

3. **Key Format:** Populate the `.env` file as follows:

   ```bash
   GEMINI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   ```

### 2. Topic Selection and Configuration

Before running the document generator, you must configure the topics to be processed:

1. **Select Topics:** Navigate to `features/issue_generation/data/topics.json` and review the available topic lists.

2. **Copy Topics:** Choose your desired topic list and copy it to `src/topics.py` with the variable name `topics`.

   **Example:**

   ```python
   # src/topics.py
   topics = [
       "Your selected topic 1",
       "Your selected topic 2",
       "Your selected topic 3",
       # ... additional topics
   ]
   ```

### 3. System Prompt Customization

The operational behavior and output style of the document generator can be modified by editing the system prompt file:

- **File Path:** `doc_generator/src/system_prompt.py`

### 4. Output Directory

Generated files are persisted to the host machine through a volume mount, allowing easy access and management:

| Host Path    | Container Path  |
| :----------- | :-------------- |
| `./src/temp` | `/app/src/temp` |

---

## Usage

The following commands facilitate the lifecycle management of the `doc_generator` service.

| Action                  | Command                                | Notes                                                                       |
| :---------------------- | :------------------------------------- | :-------------------------------------------------------------------------- |
| **Initial Build & Run** | `docker compose up --build -d`         | Builds the image if not present and starts the container in detached mode.  |
| **Start Existing**      | `docker compose up -d`                 | Starts the container using the existing built image.                        |
| **View Logs**           | `docker compose logs -f doc_generator` | Streams real-time logs for the service.                                     |
| **Stop & Clean Up**     | `docker compose down`                  | Stops and removes the container, networks, and volumes defined in the file. |
