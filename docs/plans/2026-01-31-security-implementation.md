# Security Module Implementation Plan (Task 2-2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implement the Security Layer (`SecretFilter` and `SafetyChecker`) to protect the system from sensitive data leaks and malicious firmware code injection.

**Architecture:**
- **`SecretFilter`**: Utility class to redact sensitive patterns (API keys, passwords) from logs and prompts.
- **`SafetyChecker`**: Validation engine for C/C++ code modification, ensuring syntax correctness and absence of dangerous system calls.
- **Data Models**: Add `RiskLevel` to core models.

**Tech Stack:** Python 3.10+, `re` (Regex), `subprocess` (GCC invocation).

---

### Task 1: Update Data Models

**Files:**
- Modify: `src/models/code.py`

**Step 1: Add RiskLevel Enum**
Add the following Enum to `src/models/code.py` to support risk assessment:
```python
class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

**Step 2: Verify Import**
Run a one-liner to verify:
```bash
python -c "from src.models.code import RiskLevel; print(RiskLevel.HIGH)"
```

---

### Task 2: Implement SecretFilter

**Files:**
- Create: `src/security/secret_filter.py`
- Create: `src/security/__init__.py`
- Test: `tests/test_secret_filter.py`

**Step 1: Create Directory**
```bash
mkdir -p src/security
touch src/security/__init__.py
```

**Step 2: Write Test Case**
Create `tests/test_secret_filter.py`:
- Test `filter()` with string: `"password = '123456'"` -> `"password = '[REDACTED]'"`
- Test `filter()` with `"api_key='abc'"`
- Test `filter()` with safe text.

**Step 3: Implement SecretFilter**
Create `src/security/secret_filter.py` with `PATTERNS` and `filter` class method.
Patterns to catch:
- `password\s*=\s*["'][^"']+["']`
- `api[_-]?key\s*=\s*["'][^"']+["']`
- `token\s*=\s*["'][^"']+["']`

**Step 4: Run Tests**
```bash
pytest tests/test_secret_filter.py -v
```

---

### Task 3: Implement SafetyChecker (Infrastructure & Regex)

**Files:**
- Create: `src/tools/code_modification/safety_checker.py`
- Test: `tests/test_safety_checker.py`

**Step 1: Define Test Structure**
Create `tests/test_safety_checker.py`:
- Test `check_security` with dangerous code: `system("rm -rf /")`. Expected: `(False, [warnings])`.
- Test `check_security` with safe code: `int a = 1;`. Expected: `(True, [])`.

**Step 2: Implement SafetyChecker Basic Structure**
Create class `SafetyChecker`.
Implement `check_security(code: str)` using regex for:
- `system`, `exec`, `popen`, `rm -rf`, `mkfs`, `dd`.

**Step 3: Run Tests**
```bash
pytest tests/test_safety_checker.py -v
```

---

### Task 4: Implement SafetyChecker (Compiler Checks)

**Files:**
- Modify: `src/tools/code_modification/safety_checker.py`
- Modify: `tests/test_safety_checker.py`

**Step 1: Update Tests**
Add tests for `check_syntax` and `check_compile`.
*Note: Use `unittest.mock` to mock `subprocess.run` since GCC might not be in the CI environment.*

**Step 2: Implement Compiler Methods**
- `check_syntax(file_path)`: Run `gcc -fsyntax-only`.
- `check_compile(file_path)`: Run `gcc -c`.
- Use `tempfile` for output artifacts.

**Step 3: Run Tests**
```bash
pytest tests/test_safety_checker.py -v
```

---

### Task 5: Implement Risk Assessment

**Files:**
- Modify: `src/tools/code_modification/safety_checker.py`
- Modify: `tests/test_safety_checker.py`

**Step 1: Update Tests**
Add test for `assess_risk`:
- High line count (>100) -> MEDIUM/HIGH.
- Sensitive keywords (`malloc`, `free`) -> +Risk.

**Step 2: Implement assess_risk**
Implement logic to return `RiskLevel` based on code analysis.

**Step 3: Run Tests**
```bash
pytest tests/test_safety_checker.py -v
```
