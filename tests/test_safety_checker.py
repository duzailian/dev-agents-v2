import pytest
from src.tools.code_modification.safety_checker import SafetyChecker

@pytest.fixture
def safety_checker():
    return SafetyChecker()

def test_check_security_safe_code(safety_checker):
    code = """
    int main() {
        int a = 1;
        printf("Hello World: %d", a);
        return 0;
    }
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is True
    assert len(warnings) == 0

def test_check_security_system_call(safety_checker):
    code = """
    #include <stdlib.h>
    int main() {
        system("rm -rf /");
        return 0;
    }
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("system" in w for w in warnings)

def test_check_security_exec_call(safety_checker):
    code = """
    #include <unistd.h>
    int main() {
        execl("/bin/sh", "sh", NULL);
        return 0;
    }
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("exec" in w for w in warnings)

def test_check_security_popen_call(safety_checker):
    code = """
    #include <stdio.h>
    int main() {
        FILE *fp = popen("ls", "r");
        return 0;
    }
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("popen" in w for w in warnings)

def test_check_security_rm_rf(safety_checker):
    code = """
    // Some dangerous comment or code string
    char *cmd = "rm -rf /";
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("rm -rf" in w for w in warnings)

def test_check_security_mkfs(safety_checker):
    code = """
    char *cmd = "mkfs.ext4 /dev/sda1";
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("mkfs" in w for w in warnings)

def test_check_security_dd_if(safety_checker):
    code = """
    char *cmd = "dd if=/dev/zero of=/dev/null";
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert any("dd if=" in w for w in warnings)

def test_check_security_multiple_issues(safety_checker):
    code = """
    int main() {
        system("echo hello");
        popen("ls", "r");
    }
    """
    is_safe, warnings = safety_checker.check_security(code)
    assert is_safe is False
    assert len(warnings) >= 2
