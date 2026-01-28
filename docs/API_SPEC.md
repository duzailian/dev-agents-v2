# API Specification

This document defines the internal and external APIs for the AI-Driven Firmware Intelligent Testing System.

## 1. Agent Tool Interfaces (Function Calling)

### `analyze_code`
- **Description**: Extracts code context and dependency graph.
- **Arguments**:
  ```json
  {
    "file_path": "string",
    "focus_function": "string (optional)"
  }
  ```

### `execute_test`
- **Description**: Triggers a test run in the specified environment.
- **Arguments**:
  ```json
  {
    "test_suite": "string",
    "environment": "qemu | board | bmc"
  }
  ```

## 2. External REST API (FastAPI)

### `GET /issues`
- **Description**: Fetch pending issues from Redmine.

### `POST /jobs`
- **Description**: Create a new agentic testing/fixing job.

### `GET /jobs/{job_id}`
- **Description**: Fetch job status, current phase, and summary.

### `GET /jobs/{job_id}/artifacts`
- **Description**: List artifacts (logs, reports, patches) produced by a job.

### `GET /jobs/{job_id}/report`
- **Description**: Download the final report for a job (Markdown/JSON).

## 3. Webhook Endpoints (Optional)

### `POST /webhooks/gitlab`
- **Description**: Receive GitLab webhook events (merge request, pipeline, push).
- **Arguments**: GitLab webhook payload (JSON) with signature verification.

### `POST /webhooks/redmine`
- **Description**: Receive Redmine issue/update events for task synchronization.
- **Arguments**: Redmine webhook payload (JSON) with signature verification.

## 4. Knowledge Base Query

### `POST /knowledge/search`
- **Arguments**:
  ```json
  {
    "query": "string",
    "product_line": "string",
    "limit": 5
  }
  ```
