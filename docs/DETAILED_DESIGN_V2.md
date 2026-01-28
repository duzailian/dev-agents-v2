# AI驱动固件智能测试系统 — 详细设计文档（DETAILED_DESIGN_V2）

> 文档版本：v2.0
>
> 目标：基于现有架构文档，提供完整的系统详细设计方案，确保所有模块的精确实现规格
>
> 基于：REQUIREMENTS.md（18点需求）、ARCHITECTURE_V2.md（系统架构）、AGENT_DESIGN.md（Agent设计）、STATE_MACHINE.md（状态机）、KNOWLEDGE_SCHEMA.md（知识库Schema）、WORK_PLAN_V2.md（工作计划）
>
> 对齐：所有已有文档的设计规范，确保完整一致性

---

## 导航索引

- 0. Phase 2 MVP 边界说明
- 1. 核心模块详细设计
- 2. CrewAI Agent系统详细设计
- 3. LangGraph状态机详细设计
- 4. 知识库系统详细设计
- 5. 数据模型
- 6. API规范
- 7. 配置与策略
- 8. 集成服务设计 (Layer 4)
- 9. 运行约束与治理（并发、权限、限流、记忆、日志）

## 0. Phase 2 MVP 边界说明

为避免范围膨胀，Phase 2 仅实现“闭环最小可用链路”，其余能力作为后续阶段增强：

- **Phase 2 必做**：CodeAnalyzer、CodeModifier、TestOrchestrator、ResultAnalyzer 的最小闭环；CLI 最小入口；基础日志与配置。
- **Phase 2 延后**：Webhook 集成、WebUI、监控告警、缓存加速、完整 RBAC/多租户支持。
- **可选依赖**：Redis 缓存、对象存储/存储服务，仅在明确需求与验收后引入。

### 0.1 模块依赖与实现顺序（Phase 2）

1. **基础设施与配置**：配置加载、日志初始化、基础目录与依赖检查。
2. **CodeAnalyzer → CodeModifier**：确保分析结果可直接生成可执行的修改计划。
3. **TestOrchestrator**：打通最小测试执行路径（QEMU优先）。
4. **ResultAnalyzer**：统一测试结果解析与结构化输出，为闭环决策提供输入。
5. **最小CLI入口**：串联上述模块形成闭环路径。

---

## 9. 运行约束与治理（并发、权限、限流、记忆、日志）

### 9.1 并发与异步策略
- 核心I/O流程（仓库拉取、模型调用、测试执行、日志采集）必须使用 `async/await` 接口。
- 任务级并行与资源锁（板卡、端口）使用调度器统一管理。

### 9.2 Agent解耦与消息总线
- Agent间通信通过消息总线/事件队列完成，禁止直接调用对方内部实现。
- 消息包含 `task_id`、`iteration_id`、`sender`、`receiver`、`payload_schema_version`。

### 9.3 LLM输出结构化校验
- LLM输出统一映射到Pydantic模型（示例：PatchPlan、TestPlan、AnalysisSummary）。
- 校验失败时进入降级流程（重试/模板化/人工介入），不得进入执行阶段。

### 9.4 工具执行权限与范围
- 工具执行需受限于路径白名单、命令白名单与运行环境隔离。
- 权限校验失败必须记录审计日志并阻断执行。

### 9.5 Token与迭代预算
- 为每次模型调用设置最大Token上限与超时。
- 状态机必须配置最大迭代次数与收敛条件（超限即终止或人工介入）。

### 9.6 记忆分层策略
- **短期记忆**：仅存当前任务上下文，设置窗口与TTL。
- **长期记忆**：仅写入已验证的知识单元（KnowledgeUnit），进入向量检索体系。

### 9.7 结构化日志与可追溯性
- 每个步骤输出结构化日志，至少包含 `task_id`、`iteration_id`、`step`、`status`。
- 关键结论与决策必须引用证据（日志行、KnowledgeUnit ID或artifact链接）。

### 9.8 基于角色的访问控制（RBAC）

#### 9.8.1 角色定义

系统采用基于角色的访问控制（RBAC）模型，将用户权限与角色绑定，实现细粒度的操作权限管理。

**用户角色（User Roles）**

| 角色 | 描述 | 典型用户 |
| :--- | :--- | :--- |
| **Admin** | 系统管理员，拥有最高权限 | DevOps工程师、安全管理员 |
| **Engineer** | 开发工程师，执行代码分析、修改和测试 | 固件开发人员、AI Agent |
| **Viewer** | 只读用户，仅能查询状态和结果 | 产品经理、技术评审人员、外部审计员 |

**角色层级关系**
```mermaid
graph TD
    A[Admin] --> B[Engineer]
    A --> C[Viewer]
    B --> C
```

#### 9.8.2 权限定义

**操作权限（Operation Permissions）**

| 操作权限 | 描述 | Admin | Engineer | Viewer |
| :--- | :--- | :---: | :---: | :---: |
| `task:query` | 查询任务状态和历史 | ✓ | ✓ | ✓ |
| `task:create` | 创建新任务 | ✓ | ✓ | ✗ |
| `task:cancel` | 取消或终止任务 | ✓ | ✓ | ✗ |
| `code:read` | 读取源代码 | ✓ | ✓ | ✓ |
| `code:modify` | 修改代码并生成补丁 | ✓ | ✓ | ✗ |
| `code:commit` | 提交代码变更到仓库 | ✓ | ✗ | ✗ |
| `patch:view` | 查看补丁内容 | ✓ | ✓ | ✓ |
| `patch:approve` | 审批或拒绝补丁 | ✓ | ✗ | ✗ |
| `patch:apply` | 应用已审批的补丁 | ✓ | ✓ | ✗ |
| `test:execute` | 执行测试用例 | ✓ | ✓ | ✗ |
| `test:view` | 查看测试结果 | ✓ | ✓ | ✓ |
| `kb:read` | 读取知识库内容 | ✓ | ✓ | ✓ |
| `kb:write` | 写入知识单元 | ✓ | ✓ | ✗ |
| `kb:manage` | 管理知识库（删除、修改元数据） | ✓ | ✗ | ✗ |
| `audit:view` | 查看审计日志 | ✓ | ✗ | ✗ |
| `config:view` | 查看系统配置 | ✓ | ✓ | ✗ |
| `config:modify` | 修改系统配置 | ✓ | ✗ | ✗ |

**权限继承规则**
- Admin 继承所有 Engineer 和 Viewer 权限
- Engineer 继承所有 Viewer 权限
- 特殊权限（如 `code:commit`、`patch:approve`）需要显式授权

#### 9.8.3 权限校验机制

**权限校验接口定义**

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

class Permission(Enum):
    """操作权限枚举"""
    TASK_QUERY = "task:query"
    TASK_CREATE = "task:create"
    TASK_CANCEL = "task:cancel"
    CODE_READ = "code:read"
    CODE_MODIFY = "code:modify"
    CODE_COMMIT = "code:commit"
    PATCH_VIEW = "patch:view"
    PATCH_APPROVE = "patch:approve"
    PATCH_APPLY = "patch:apply"
    TEST_EXECUTE = "test:execute"
    TEST_VIEW = "test:view"
    KB_READ = "kb:read"
    KB_WRITE = "kb:write"
    KB_MANAGE = "kb:manage"
    AUDIT_VIEW = "audit:view"
    CONFIG_VIEW = "config:view"
    CONFIG_MODIFY = "config:modify"

class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"

@dataclass
class UserContext:
    """用户上下文信息"""
    user_id: str
    roles: List[Role]
    permissions: List[Permission]
    department: Optional[str] = None
    project_scope: Optional[List[str]] = None

@dataclass
class PermissionResult:
    """权限校验结果"""
    allowed: bool
    reason: Optional[str] = None
    required_permission: Optional[Permission] = None
```

**权限校验器实现**

```python
class RBACValidator:
    """基于角色的访问控制校验器"""

    # 角色-权限映射表
    ROLE_PERMISSIONS = {
        Role.ADMIN: set(Permission),  # 拥有所有权限
        Role.ENGINEER: {
            Permission.TASK_QUERY,
            Permission.TASK_CREATE,
            Permission.TASK_CANCEL,
            Permission.CODE_READ,
            Permission.CODE_MODIFY,
            Permission.PATCH_VIEW,
            Permission.TEST_EXECUTE,
            Permission.TEST_VIEW,
            Permission.KB_READ,
            Permission.KB_WRITE,
            Permission.CONFIG_VIEW,
        },
        Role.VIEWER: {
            Permission.TASK_QUERY,
            Permission.CODE_READ,
            Permission.PATCH_VIEW,
            Permission.TEST_VIEW,
            Permission.KB_READ,
        },
    }

    # 需要特殊审批的权限
    PRIVILEGED_PERMISSIONS = {
        Permission.CODE_COMMIT,
        Permission.PATCH_APPROVE,
        Permission.CONFIG_MODIFY,
        Permission.KB_MANAGE,
        Permission.AUDIT_VIEW,
    }

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.audit_logger = self._init_audit_logger()

    def get_user_permissions(self, user: UserContext) -> set:
        """获取用户的所有权限（基于角色继承）"""
        permissions = set()
        for role in user.roles:
            permissions.update(self.ROLE_PERMISSIONS.get(role, set()))
        # 添加用户直接授予的特殊权限
        permissions.update(user.permissions)
        return permissions

    def check_permission(
        self,
        user: UserContext,
        permission: Permission,
        resource: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> PermissionResult:
        """检查用户是否拥有指定权限"""
        user_permissions = self.get_user_permissions(user)

        # 检查基础权限
        if permission in user_permissions:
            # 对于特权权限，需要额外验证
            if permission in self.PRIVILEGED_PERMISSIONS:
                return self._check_privileged_access(
                    user, permission, resource, context
                )
            return PermissionResult(allowed=True)

        # 权限不足，记录审计日志
        self.audit_logger.log_permission_denied(
            user_id=user.user_id,
            permission=permission,
            resource=resource,
            context=context
        )

        return PermissionResult(
            allowed=False,
            reason=f"User {user.user_id} does not have permission: {permission.value}",
            required_permission=permission
        )

    def require_permission(
        self,
        user: UserContext,
        permission: Permission,
        resource: Optional[str] = None
    ) -> None:
        """权限校验失败时抛出异常"""
        result = self.check_permission(user, permission, resource)
        if not result.allowed:
            raise PermissionDeniedError(
                user_id=user.user_id,
                permission=permission,
                reason=result.reason
            )

    def _check_privileged_access(
        self,
        user: UserContext,
        permission: Permission,
        resource: Optional[str],
        context: Optional[Dict]
    ) -> PermissionResult:
        """检查特权权限访问"""
        # 检查是否在允许的时间范围内（如工作时间）
        if self.config.get("privileged_time_restriction"):
            if not self._is_within_working_hours():
                return PermissionResult(
                    allowed=False,
                    reason="Privileged access only allowed during working hours"
                )

        # 检查是否需要多因素认证
        if self.config.get("privileged_require_mfa"):
            if not context or not context.get("mfa_verified"):
                return PermissionResult(
                    allowed=False,
                    reason="MFA verification required for privileged access"
                )

        return PermissionResult(allowed=True)

    def _is_within_working_hours(self) -> bool:
        """检查是否在允许的工作时间范围内"""
        import datetime
        now = datetime.datetime.now()
        start = datetime.time(9, 0)
        end = datetime.time(18, 0)
        return start <= now.time() <= end
```

**权限拦截策略**

```python
from functools import wraps
from fastapi import Request, HTTPException

class PermissionInterceptor:
    """权限拦截器"""

    def __init__(self, rbac_validator: RBACValidator):
        self.validator = rbac_validator

    def require(self, permission: Permission, resource_param: str = None):
        """装饰器：要求特定权限"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = self._extract_request(args, kwargs)
                user = self._get_user_from_request(request)

                # 提取资源标识
                resource = None
                if resource_param:
                    resource = kwargs.get(resource_param)

                result = self.validator.check_permission(
                    user=user,
                    permission=permission,
                    resource=resource,
                    context={"request": request}
                )

                if not result.allowed:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "permission_denied",
                            "message": result.reason,
                            "required_permission": permission.value
                        }
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def _extract_request(self, args, kwargs) -> Request:
        """从函数参数中提取FastAPI Request对象"""
        for arg in args:
            if isinstance(arg, Request):
                return arg
        return kwargs.get("request")

    def _get_user_from_request(self, request: Request) -> UserContext:
        """从请求中获取用户上下文"""
        # 从JWT Token或认证头中解析用户信息
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            return self._parse_jwt_token(token[7:])
        raise AuthenticationError("Missing or invalid authorization token")
```

**权限校验执行点**

| 模块 | 操作 | 执行校验的权限 | 校验时机 |
| :--- | :--- | :--- | :--- |
| TaskManager | 创建任务 | `task:create` | 任务创建入口 |
| TaskManager | 查询任务 | `task:query` | 任务列表/详情查询 |
| TaskManager | 取消任务 | `task:cancel` | 任务终止请求 |
| CodeModifier | 读取代码 | `code:read` | 代码仓库访问 |
| CodeModifier | 生成补丁 | `code:modify` | 补丁生成入口 |
| CodeModifier | 提交代码 | `code:commit` | Git提交操作 |
| CodeModifier | 审批补丁 | `patch:approve` | 审批工作流 |
| TestOrchestrator | 执行测试 | `test:execute` | 测试启动入口 |
| KBAgent | 写入知识库 | `kb:write` | 知识单元创建 |
| KBAgent | 管理知识库 | `kb:manage` | 删除/修改操作 |
| AuditService | 查看审计日志 | `audit:view` | 日志查询请求 |

---

### 9.9 操作审计日志

#### 9.9.1 AuditLog数据模型

**审计日志核心结构**

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

class AuditAction(Enum):
    """审计操作类型"""
    # 任务相关
    TASK_CREATE = "task:create"
    TASK_START = "task:start"
    TASK_COMPLETE = "task:complete"
    TASK_CANCEL = "task:cancel"
    TASK_FAIL = "task:fail"

    # 代码相关
    CODE_READ = "code:read"
    CODE_MODIFY = "code:modify"
    CODE_COMMIT = "code:commit"

    # 补丁相关
    PATCH_GENERATE = "patch:generate"
    PATCH_VIEW = "patch:view"
    PATCH_APPROVE = "patch:approve"
    PATCH_REJECT = "patch:reject"
    PATCH_APPLY = "patch:apply"
    PATCH_ROLLBACK = "patch:rollback"

    # 测试相关
    TEST_START = "test:start"
    TEST_COMPLETE = "test:complete"
    TEST_FAIL = "test:fail"

    # 知识库相关
    KB_CREATE = "kb:create"
    KB_UPDATE = "kb:update"
    KB_DELETE = "kb:delete"
    KB_QUERY = "kb:query"

    # 权限相关
    PERMISSION_GRANT = "permission:grant"
    PERMISSION_REVOKE = "permission:revoke"
    LOGIN_SUCCESS = "auth:login_success"
    LOGIN_FAIL = "auth:login_fail"

    # 系统相关
    CONFIG_CHANGE = "config:change"
    SYSTEM_ERROR = "system:error"
    SECURITY_ALERT = "security:alert"

class AuditSeverity(Enum):
    """审计日志严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditContext:
    """审计上下文信息"""
    task_id: Optional[str] = None
    iteration_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class AuditParameter:
    """审计参数详情"""
    name: str
    value: Any
    sensitive: bool = False  # 标记是否为敏感参数

@dataclass
class AuditLog:
    """审计日志数据模型"""
    # 核心字段
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: AuditAction
    severity: AuditSeverity = AuditSeverity.INFO

    # 执行者信息
    actor_id: str  # 用户ID或Agent ID
    actor_type: str  # "user" 或 "agent"
    actor_name: Optional[str] = None

    # 资源信息
    resource_type: str  # "task", "patch", "code", "kb", "config"
    resource_id: str
    resource_name: Optional[str] = None

    # 操作详情
    parameters: List[AuditParameter] = field(default_factory=list)
    result: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

    # 上下文信息
    context: AuditContext = field(default_factory=AuditContext)

    # 变更追踪
    changes: Dict[str, Any] = field(default_factory=dict)  # before/after对比

    # 元数据
    version: str = "1.0"
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "severity": self.severity.value,
            "actor": {
                "id": self.actor_id,
                "type": self.actor_type,
                "name": self.actor_name
            },
            "resource": {
                "type": self.resource_type,
                "id": self.resource_id,
                "name": self.resource_name
            },
            "parameters": [
                {
                    "name": p.name,
                    "value": p.value if not p.sensitive else "***REDACTED***",
                    "sensitive": p.sensitive
                }
                for p in self.parameters
            ],
            "result": self.result,
            "success": self.success,
            "error_message": self.error_message,
            "context": {
                "task_id": self.context.task_id,
                "iteration_id": self.context.iteration_id,
                "agent_id": self.context.agent_id,
                "session_id": self.context.session_id,
                "request_id": self.context.request_id,
                "source_ip": self.context.source_ip,
                "user_agent": self.context.user_agent
            },
            "changes": self.changes,
            "version": self.version,
            "schema_version": self.schema_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLog":
        """从字典创建审计日志"""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["context"] = AuditContext(**data.get("context", {}))
        data["parameters"] = [
            AuditParameter(**p) for p in data.get("parameters", [])
        ]
        data["action"] = AuditAction(data["action"])
        data["severity"] = AuditSeverity(data["severity"])
        return cls(**data)
```

#### 9.9.2 审计日志服务实现

```python
import json
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class AuditStorageBackend(ABC):
    """审计日志存储后端抽象"""

    @abstractmethod
    async def write(self, log: AuditLog) -> bool:
        """写入单条审计日志"""
        pass

    @abstractmethod
    async def write_batch(self, logs: List[AuditLog]) -> int:
        """批量写入审计日志"""
        pass

    @abstractmethod
    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[AuditLog]:
        """查询审计日志"""
        pass

    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """统计符合条件的日志数量"""
        pass

    @abstractmethod
    async def delete_old_logs(self, before: datetime) -> int:
        """删除指定时间之前的日志"""
        pass


class FileAuditStorage(AuditStorageBackend):
    """文件系统审计日志存储"""

    def __init__(self, config: Dict[str, Any]):
        self.base_path = config.get("path", "/var/log/audit")
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.current_file = None
        self.file_lock = asyncio.Lock()

    async def write(self, log: AuditLog) -> bool:
        """写入单条日志到文件"""
        async with self.file_lock:
            try:
                line = json.dumps(log.to_dict(), ensure_ascii=False) + "\n"
                await self._ensure_file_open()
                await self.current_file.write(line)

                # 检查文件大小，必要时轮转
                if self.current_file.tell() > self.max_file_size:
                    await self._rotate_file()

                return True
            except Exception as e:
                print(f"Failed to write audit log: {e}")
                return False

    async def write_batch(self, logs: List[AuditLog]) -> int:
        """批量写入日志"""
        success_count = 0
        for log in logs:
            if await self.write(log):
                success_count += 1
        return success_count

    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[AuditLog]:
        """查询日志（通过grep实现）"""
        import subprocess
        import os

        # 构建查询命令
        cmd = ["grep", "-r", self.base_path]

        if "actor_id" in filters:
            cmd.extend(["--grep", f'"actor_id":"{filters["actor_id"]}"'])
        if "action" in filters:
            cmd.extend(["--grep", f'"action":"{filters["action"]}"'])

        # 简化实现：返回空列表
        return []

    async def count(self, filters: Dict[str, Any]) -> int:
        """统计日志数量"""
        return 0

    async def delete_old_logs(self, before: datetime) -> int:
        """删除过期日志"""
        return 0

    async def _ensure_file_open(self):
        """确保日志文件已打开"""
        pass

    async def _rotate_file(self):
        """日志文件轮转"""
        pass


class DatabaseAuditStorage(AuditStorageBackend):
    """数据库审计日志存储"""

    def __init__(self, config: Dict[str, Any]):
        self.connection_string = config.get("connection_string")
        self.table_name = config.get("table_name", "audit_logs")

    async def write(self, log: AuditLog) -> bool:
        """写入数据库"""
        # 使用数据库驱动实现
        return True

    async def write_batch(self, logs: List[AuditLog]) -> int:
        """批量写入数据库"""
        success_count = 0
        for log in logs:
            if await self.write(log):
                success_count += 1
        return success_count

    async def query(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[AuditLog]:
        """从数据库查询"""
        return []

    async def count(self, filters: Dict[str, Any]) -> int:
        """统计数量"""
        return 0

    async def delete_old_logs(self, before: datetime) -> int:
        """删除过期日志"""
        return 0


class AuditLogger:
    """审计日志服务主类"""

    def __init__(self, storage: AuditStorageBackend, config: Dict[str, Any] = None):
        self.storage = storage
        self.config = config or {}
        self.buffer: List[AuditLog] = []
        self.buffer_size = self.config.get("buffer_size", 100)
        self.flush_interval = self.config.get("flush_interval", 5)  # 秒
        self._flush_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动审计日志服务"""
        self._flush_task = asyncio.create_task(self._periodic_flush())

    async def stop(self):
        """停止审计日志服务"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # 刷新剩余日志
        await self._flush_buffer()

    async def log(
        self,
        action: AuditAction,
        actor_id: str,
        actor_type: str,
        resource_type: str,
        resource_id: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        parameters: Optional[List[AuditParameter]] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        context: Optional[AuditContext] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            action=action,
            severity=severity,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            parameters=parameters or [],
            result=result or {},
            error_message=error_message,
            context=context or AuditContext(),
            changes=changes or {},
            **kwargs
        )

        self.buffer.append(log)

        if len(self.buffer) >= self.buffer_size:
            await self._flush_buffer()

        return log

    async def log_task_operation(
        self,
        task_id: str,
        operation: str,
        actor_id: str,
        actor_type: str,
        success: bool,
        details: Optional[Dict] = None
    ):
        """快捷方法：记录任务操作"""
        action_map = {
            "create": AuditAction.TASK_CREATE,
            "start": AuditAction.TASK_START,
            "complete": AuditAction.TASK_COMPLETE,
            "cancel": AuditAction.TASK_CANCEL,
            "fail": AuditAction.TASK_FAIL,
        }
        action = action_map.get(operation, AuditAction.TASK_CREATE)

        await self.log(
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type="task",
            resource_id=task_id,
            result=details or {},
            success=success,
            context=AuditContext(task_id=task_id)
        )

    async def log_patch_operation(
        self,
        patch_id: str,
        task_id: str,
        operation: str,
        actor_id: str,
        actor_type: str,
        success: bool,
        changes: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """快捷方法：记录补丁操作"""
        action_map = {
            "generate": AuditAction.PATCH_GENERATE,
            "view": AuditAction.PATCH_VIEW,
            "approve": AuditAction.PATCH_APPROVE,
            "reject": AuditAction.PATCH_REJECT,
            "apply": AuditAction.PATCH_APPLY,
            "rollback": AuditAction.PATCH_ROLLBACK,
        }
        action = action_map.get(operation, AuditAction.PATCH_GENERATE)

        # 根据操作结果设置严重级别
        severity = AuditSeverity.INFO
        if operation in ("approve", "apply"):
            severity = AuditSeverity.WARNING
        if not success:
            severity = AuditSeverity.ERROR

        await self.log(
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type="patch",
            resource_id=patch_id,
            severity=severity,
            success=success,
            error_message=error_message,
            changes=changes,
            context=AuditContext(task_id=task_id)
        )

    async def log_security_event(
        self,
        event_type: str,
        actor_id: str,
        description: str,
        details: Optional[Dict] = None
    ):
        """记录安全事件"""
        await self.log(
            action=AuditAction.SECURITY_ALERT,
            actor_id=actor_id,
            actor_type="system",
            resource_type="security",
            resource_id=event_type,
            severity=AuditSeverity.CRITICAL,
            success=True,
            result={"description": description, **(details or {})}
        )

    async def _flush_buffer(self):
        """刷新缓冲区到存储"""
        if not self.buffer:
            return

        logs_to_flush = self.buffer.copy()
        self.buffer.clear()

        try:
            written = await self.storage.write_batch(logs_to_flush)
            if written < len(logs_to_flush):
                print(f"Warning: Only {written}/{len(logs_to_flush)} audit logs written")
        except Exception as e:
            print(f"Failed to flush audit logs: {e}")
            # 重新加入缓冲区
            self.buffer.extend(logs_to_flush)

    async def _periodic_flush(self):
        """定期刷新任务"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()
```

#### 9.9.3 审计日志查询接口

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class AuditQueryRequest(BaseModel):
    """审计日志查询请求"""
    actor_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success: Optional[bool] = None
    severity: Optional[AuditSeverity] = None
    task_id: Optional[str] = None

    # 分页
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

    # 排序
    sort_by: str = Field(default="timestamp")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class AuditQueryResponse(BaseModel):
    """审计日志查询响应"""
    total: int
    logs: List[Dict[str, Any]]
    limit: int
    offset: int

class AuditQueryService:
    """审计日志查询服务"""

    def __init__(self, storage: AuditStorageBackend):
        self.storage = storage

    async def query(self, request: AuditQueryRequest) -> AuditQueryResponse:
        """查询审计日志"""
        filters = request.model_dump(exclude_none=True)
        filters.pop("limit", None)
        filters.pop("offset", None)
        filters.pop("sort_by", None)
        filters.pop("sort_order", None)

        logs = await self.storage.query(
            filters=filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )

        total = await self.storage.count(filters)

        return AuditQueryResponse(
            total=total,
            logs=[log.to_dict() for log in logs],
            limit=request.limit,
            offset=request.offset
        )

    async def get_operation_history(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """获取指定资源的操作历史"""
        response = await self.query(AuditQueryRequest(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=100
        ))
        return response.logs

    async def get_user_activity(
        self,
        actor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取用户活动记录"""
        response = await self.query(AuditQueryRequest(
            actor_id=actor_id,
            start_time=start_time,
            end_time=end_time,
            limit=200
        ))
        return response.logs

    async def get_security_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取安全事件日志"""
        response = await self.query(AuditQueryRequest(
            action=AuditAction.SECURITY_ALERT,
            start_time=start_time,
            end_time=end_time,
            limit=500
        ))
        return response.logs
```

#### 9.9.4 日志清理策略

**日志保留与归档策略**

| 日志类型 | 保留期限 | 归档位置 | 清理方式 |
| :--- | :--- | :--- | :--- |
| 普通操作日志 | 90天 | 冷存储/S3 | 自动删除或压缩归档 |
| 安全审计日志 | 365天 | 冷存储/S3 | 加密后长期保留 |
| 错误日志 | 30天 | 本地存储 | 自动清理 |
| 调试日志 | 7天 | 临时存储 | 自动清理 |
| 敏感操作日志 | 730天（2年） | 加密归档 | 仅允许特定角色查询 |

**日志清理实现**

```python
import os
import gzip
from pathlib import Path
from datetime import datetime, timedelta

class LogCleanupPolicy:
    """日志清理策略"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.policies = self._init_policies()

    def _init_policies(self) -> Dict[str, Dict]:
        """初始化清理策略"""
        return {
            "audit": {
                "retention_days": 90,
                "archive_days": 180,
                "delete_days": 365,
                "archive_path": "/var/log/archive/audit",
                "compress": True,
                "encryption": True
            },
            "security": {
                "retention_days": 365,
                "archive_days": 730,
                "delete_days": 2555,  # 7年
                "archive_path": "/var/log/archive/security",
                "compress": True,
                "encryption": True
            },
            "error": {
                "retention_days": 30,
                "archive_days": 90,
                "delete_days": 180,
                "archive_path": "/var/log/archive/error",
                "compress": True,
                "encryption": False
            },
            "debug": {
                "retention_days": 7,
                "archive_days": 14,
                "delete_days": 30,
                "archive_path": "/var/log/archive/debug",
                "compress": True,
                "encryption": False
            }
        }

    async def run_cleanup(self, log_type: str = None) -> Dict[str, int]:
        """执行日志清理"""
        results = {}
        types_to_process = [log_type] if log_type else self.policies.keys()

        for log_type in types_to_process:
            policy = self.policies.get(log_type)
            if not policy:
                continue

            deleted = await self._cleanup_by_policy(log_type, policy)
            archived = await self._archive_by_policy(log_type, policy)
            results[log_type] = {"deleted": deleted, "archived": archived}

        return results

    async def _cleanup_by_policy(
        self,
        log_type: str,
        policy: Dict
    ) -> int:
        """根据策略删除过期日志"""
        delete_before = datetime.utcnow() - timedelta(days=policy["delete_days"])
        log_path = Path(self.config.get("log_path", "/var/log")) / log_type

        deleted_count = 0
        if log_path.exists():
            for file in log_path.glob("**/*.log*"):
                if file.stat().st_mtime < delete_before.timestamp():
                    file.unlink()
                    deleted_count += 1

        return deleted_count

    async def _archive_by_policy(
        self,
        log_type: str,
        policy: Dict
    ) -> int:
        """根据策略归档日志"""
        archive_before = datetime.utcnow() - timedelta(days=policy["archive_days"])
        retention_before = datetime.utcnow() - timedelta(days=policy["retention_days"])
        log_path = Path(self.config.get("log_path", "/var/log")) / log_type
        archive_path = Path(policy["archive_path"])

        # 确保归档目录存在
        archive_path.mkdir(parents=True, exist_ok=True)

        archived_count = 0
        if log_path.exists():
            for file in log_path.glob("**/*.log"):
                if retention_before < file.stat().st_mtime < archive_before.timestamp():
                    await self._archive_file(file, archive_path, policy)
                    archived_count += 1

        return archived_count

    async def _archive_file(
        self,
        file: Path,
        archive_path: Path,
        policy: Dict
    ):
        """归档单个文件"""
        # 创建以日期为名的子目录
        date_dir = archive_path / file.stat().st_mtime.strftime("%Y-%m")
        date_dir.mkdir(parents=True, exist_ok=True)

        # 压缩文件
        if policy.get("compress"):
            archived_file = date_dir / f"{file.stem}.gz"
            with open(file, 'rb') as f_in:
                with gzip.open(archived_file, 'wb') as f_out:
                    f_out.write(f_in.read())

        # 加密文件（如果需要）
        if policy.get("encryption"):
            # 调用加密工具
            pass

        # 删除原始文件
        file.unlink()
```

---

### 9.10 敏感代码与凭证管理

#### 9.10.1 敏感数据识别规则

```python
from dataclasses import dataclass
from typing import List, Pattern
import re

@dataclass
class SensitiveDataPattern:
    """敏感数据模式定义"""
    name: str  # 模式名称
    pattern: str  # 正则表达式
    severity: str  # high, medium, low
    description: str
    examples: List[str]

# 预定义的敏感数据模式
SENSITIVE_PATTERNS = [
    SensitiveDataPattern(
        name="API Key",
        pattern=r"(?i)(api[_-]?key|apikey|api_secret)[\s=:\"']+([a-zA-Z0-9_\-]{20,})",
        severity="high",
        description="API密钥泄露",
        examples=["api_key=abc123xyz456", 'apikey: "sk-xxxxx"']
    ),
    SensitiveDataPattern(
        name="AWS Access Key",
        pattern=r"(?i)AKIA[0-9A-Z]{16}",
        severity="high",
        description="AWS访问密钥泄露",
        examples=["AKIAIOSFODNN7EXAMPLE"]
    ),
    SensitiveDataPattern(
        name="AWS Secret Key",
        pattern=r"(?i)aws[_-]?secret[_-]?access[_-]?key[\s=:\"']+[a-zA-Z0-9/+=]{40}",
        severity="high",
        description="AWS密钥泄露",
        examples=["wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"]
    ),
    SensitiveDataPattern(
        name="Generic Secret",
        pattern=r"(?i)(secret|password|passwd|pwd|token|auth)[\s]*[:=][\s]*[\"'][^\"']+[\"']",
        severity="medium",
        description="通用密码或令牌",
        examples=['password="mypassword"', "token=abc123"]
    ),
    SensitiveDataPattern(
        name="Private Key",
        pattern=r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        severity="critical",
        description="私钥泄露",
        examples=["-----BEGIN RSA PRIVATE KEY-----"]
    ),
    SensitiveDataPattern(
        name="JWT Token",
        pattern=r"(?i)eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
        severity="high",
        description="JWT令牌泄露",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    ),
    SensitiveDataPattern(
        name="Database Connection String",
        pattern=r"(?i)(mongodb|postgres|mysql|postgresql)://[^\s\"']+",
        severity="high",
        description="数据库连接字符串泄露",
        examples=["mongodb://user:pass@host:27017/db"]
    ),
    SensitiveDataPattern(
        name="Hardcoded IP",
        pattern=r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        severity="low",
        description="硬编码IP地址",
        examples=["192.168.1.100"]
    ),
    SensitiveDataPattern(
        name="Credit Card",
        pattern=r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b",
        severity="critical",
        description="信用卡号泄露",
        examples=["4111111111111111"]
    ),
    SensitiveDataPattern(
        name="Social Security Number (US)",
        pattern=r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
        severity="critical",
        description="社会安全号码泄露",
        examples=["123-45-6789"]
    )
]

class SensitiveDataDetector:
    """敏感数据检测器"""

    def __init__(self, custom_patterns: List[SensitiveDataPattern] = None):
        self.patterns = SENSITIVE_PATTERNS + (custom_patterns or [])
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式"""
        self.compiled_patterns = []
        for sp in self.patterns:
            try:
                regex = re.compile(sp.pattern)
                self.compiled_patterns.append((sp, regex))
            except re.error as e:
                print(f"Warning: Invalid pattern {sp.name}: {e}")

    def scan_content(self, content: str) -> List[Dict]:
        """扫描内容中的敏感数据"""
        findings = []
        for sp, regex in self.compiled_patterns:
            for match in regex.finditer(content):
                findings.append({
                    "pattern_name": sp.name,
                    "severity": sp.severity,
                    "description": sp.description,
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        return findings

    def scan_file(self, file_path: str) -> List[Dict]:
        """扫描文件中的敏感数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.scan_content(content)
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
            return []

    def scan_patch(self, patch_content: str) -> Dict:
        """扫描补丁中的敏感数据"""
        findings = self.scan_content(patch_content)

        if findings:
            # 根据严重级别汇总
            summary = {
                "total_findings": len(findings),
                "critical": len([f for f in findings if f["severity"] == "critical"]),
                "high": len([f for f in findings if f["severity"] == "high"]),
                "medium": len([f for f in findings if f["severity"] == "medium"]),
                "low": len([f for f in findings if f["severity"] == "low"]),
                "findings": findings
            }
            return summary

        return {
            "total_findings": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "findings": []
        }
```

#### 9.10.2 存储加密方案

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dataclasses import dataclass
from typing import Optional
import base64
import os

@dataclass
class EncryptionConfig:
    """加密配置"""
    algorithm: str = "AES-256-GCM"
    key Derivation: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 32
    nonce_length: int = 12
    master_key_path: Optional[str] = None

class KeyManagementService:
    """密钥管理服务"""

    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.master_key = None
        self.fernet = None

    def initialize(self):
        """初始化密钥服务"""
        self.master_key = self._load_or_generate_master_key()
        self.fernet = Fernet(self.master_key)

    def _load_or_generate_master_key(self) -> bytes:
        """加载或生成主密钥"""
        if self.config.master_key_path:
            try:
                with open(self.config.master_key_path, 'rb') as f:
                    return f.read()
            except FileNotFoundError:
                pass

        # 生成新的主密钥
        key = Fernet.generate_key()
        if self.config.master_key_path:
            os.makedirs(
                os.path.dirname(self.config.master_key_path),
                exist_ok=True
            )
            with open(self.config.master_key_path, 'wb') as f:
                f.write(key)
            os.chmod(self.config.master_key_path, 0o600)
        return key

    def derive_key(self, salt: bytes, purpose: str) -> bytes:
        """派生特定用途的密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt + purpose.encode(),
            iterations=self.config.iterations
        )
        return kdf.derive(self.master_key)

    def encrypt(self, data: bytes, purpose: str = "general") -> Dict[str, bytes]:
        """加密数据"""
        salt = os.urandom(self.config.salt_length)
        nonce = os.urandom(self.config.nonce_length)

        # 派生密钥
        key = self.derive_key(salt, purpose)

        # 加密
        f = Fernet(key)
        ciphertext = f.encrypt(data)

        return {
            "salt": salt,
            "nonce": nonce,
            "ciphertext": ciphertext
        }

    def decrypt(self, encrypted_data: Dict[str, bytes], purpose: str = "general") -> bytes:
        """解密数据"""
        salt = encrypted_data["salt"]
        ciphertext = encrypted_data["ciphertext"]

        # 派生密钥
        key = self.derive_key(salt, purpose)

        # 解密
        f = Fernet(key)
        return f.decrypt(ciphertext)

    def encrypt_string(self, text: str, purpose: str = "general") -> str:
        """加密字符串，返回Base64编码"""
        encrypted = self.encrypt(text.encode(), purpose)
        return base64.b64encode(encrypted["ciphertext"]).decode()

    def decrypt_string(self, encrypted_text: str, purpose: str = "general") -> str:
        """解密Base64编码的字符串"""
        ciphertext = base64.b64decode(encrypted_text.encode())
        decrypted = self.decrypt({
            "salt": os.urandom(32),  # 简化处理
            "ciphertext": ciphertext
        }, purpose)
        return decrypted.decode()
```

#### 9.10.3 日志脱敏规则

```python
from typing import Any, Dict, List, Optional
import json
import re

class LogSanitizer:
    """日志脱敏处理器"""

    # 预定义的脱敏规则
    SANITIZATION_RULES = [
        {
            "name": "mask_api_key",
            "pattern": r"(?i)(api[_-]?key|apikey)[\s]*[:=][\s]*([^\s\"']+)",
            "replacement": r"\1: ***REDACTED***"
        },
        {
            "name": "mask_password",
            "pattern": r"(?i)(password|passwd|pwd)[\s]*[:=][\s]*([^\s\"']+)",
            "replacement": r"\1: ***REDACTED***"
        },
        {
            "name": "mask_token",
            "pattern": r"(?i)(token|bearer|auth)[\s]*[:=][\s]*([^\s\"']+)",
            "replacement": r"\1: ***REDACTED***"
        },
        {
            "name": "mask_email",
            "pattern": r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "replacement": r"***@***.\2"
        },
        {
            "name": "mask_ip",
            "pattern": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "replacement": "***.***.***.***"
        },
        {
            "name": "mask_credit_card",
            "pattern": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b",
            "replacement": "****-****-****-****"
        },
        {
            "name": "mask_ssn",
            "pattern": r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
            "replacement": "***-**-****"
        }
    ]

    def __init__(self, custom_rules: List[Dict] = None):
        self.rules = self.SANITIZATION_RULES + (custom_rules or [])
        self._compile_rules()

    def _compile_rules(self):
        """编译脱敏规则"""
        self.compiled_rules = []
        for rule in self.rules:
            try:
                regex = re.compile(rule["pattern"])
                self.compiled_rules.append({
                    "name": rule["name"],
                    "regex": regex,
                    "replacement": rule["replacement"]
                })
            except re.error as e:
                print(f"Warning: Invalid sanitization rule {rule['name']}: {e}")

    def sanitize_text(self, text: str) -> str:
        """对文本进行脱敏"""
        sanitized = text
        for rule in self.compiled_rules:
            sanitized = rule["regex"].sub(rule["replacement"], sanitized)
        return sanitized

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        sensitive_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """对字典进行脱敏（递归处理嵌套结构）"""
        if sensitive_keys is None:
            sensitive_keys = [
                "password", "passwd", "pwd", "secret", "token",
                "api_key", "apikey", "access_key", "credential",
                "private_key", "connection_string"
            ]

        def process_value(value: Any) -> Any:
            if isinstance(value, str):
                return self.sanitize_text(value)
            elif isinstance(value, dict):
                return sanitize_dict(value, sensitive_keys)
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            else:
                return value

        def sanitize_dict(d: Dict, keys: List[str]) -> Dict:
            result = {}
            for key, value in d.items():
                key_lower = key.lower()
                if any(sk in key_lower for sk in keys):
                    # 敏感字段完全遮蔽
                    if isinstance(value, str):
                        result[key] = "***REDACTED***"
                    elif isinstance(value, dict):
                        result[key] = {"***REDACTED***": "***REDACTED***"}
                    else:
                        result[key] = value
                else:
                    result[key] = process_value(value)
            return result

        return sanitize_dict(data, sensitive_keys)

    def sanitize_json(self, json_str: str) -> str:
        """对JSON字符串进行脱敏"""
        try:
            data = json.loads(json_str)
            sanitized = self.sanitize_dict(data)
            return json.dumps(sanitized, ensure_ascii=False)
        except json.JSONDecodeError:
            # 非JSON文本，直接脱敏
            return self.sanitize_text(json_str)

    def sanitize_audit_log(self, log: Dict) -> Dict:
        """对审计日志进行脱敏"""
        # 敏感字段
        sensitive_fields = ["parameters", "result", "changes"]
        for field in sensitive_fields:
            if field in log and isinstance(log[field], (dict, list)):
                log[field] = self.sanitize_dict(log[field])
        return log
```

---

### 9.11 系统可观测性

#### 9.11.1 结构化日志格式

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import json
import logging

class LogLevel(Enum):
    """日志级别"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

@dataclass
class StructuredLog:
    """结构化日志数据模型"""

    # 核心字段
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = LogLevel.INFO.name
    message: str

    # 任务上下文
    task_id: Optional[str] = None
    iteration_id: Optional[str] = None
    agent_id: Optional[str] = None
    step: Optional[str] = None

    # 执行上下文
    operation: Optional[str] = None
    duration_ms: Optional[float] = None

    # 资源标识
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    # 详细数据
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 追踪信息
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    # 错误信息
    error: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "task_id": self.task_id,
            "iteration_id": self.iteration_id,
            "agent_id": self.agent_id,
            "step": self.step,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "error": self.error
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "StructuredLog":
        """从字典创建"""
        return cls(**data)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(
        self,
        name: str,
        log_dir: str = "/var/log",
        console_output: bool = True,
        json_format: bool = True
    ):
        self.name = name
        self.log_dir = log_dir
        self.json_format = json_format
        self.task_context: Dict[str, str] = {}

        # 设置标准Python日志
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(console_handler)

        # 文件处理器
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            f"{log_dir}/{name}.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def set_task_context(self, task_id: str, iteration_id: str = None):
        """设置任务上下文"""
        self.task_context = {
            "task_id": task_id,
            "iteration_id": iteration_id
        }

    def clear_task_context(self):
        """清除任务上下文"""
        self.task_context = {}

    def _create_log(
        self,
        level: LogLevel,
        message: str,
        operation: str = None,
        step: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        error: Dict = None,
        **kwargs
    ) -> StructuredLog:
        """创建结构化日志"""
        return StructuredLog(
            level=level.name,
            message=message,
            task_id=self.task_context.get("task_id"),
            iteration_id=self.task_context.get("iteration_id"),
            operation=operation,
            step=step,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            error=error,
            **kwargs
        )

    def debug(
        self,
        message: str,
        operation: str = None,
        step: str = None,
        details: Dict = None,
        **kwargs
    ):
        """记录DEBUG日志"""
        log = self._create_log(LogLevel.DEBUG, message, operation, step, details=details, **kwargs)
        self._emit(log)

    def info(
        self,
        message: str,
        operation: str = None,
        step: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        **kwargs
    ):
        """记录INFO日志"""
        log = self._create_log(
            LogLevel.INFO, message, operation, step,
            resource_type, resource_id, details, **kwargs
        )
        self._emit(log)

    def warning(
        self,
        message: str,
        operation: str = None,
        step: str = None,
        details: Dict = None,
        **kwargs
    ):
        """记录WARNING日志"""
        log = self._create_log(LogLevel.WARNING, message, operation, step, details=details, **kwargs)
        self._emit(log)

    def error(
        self,
        message: str,
        operation: str = None,
        step: str = None,
        error: Dict = None,
        details: Dict = None,
        **kwargs
    ):
        """记录ERROR日志"""
        log = self._create_log(
            LogLevel.ERROR, message, operation, step,
            error=error, details=details, **kwargs
        )
        self._emit(log)

    def critical(
        self,
        message: str,
        operation: str = None,
        step: str = None,
        error: Dict = None,
        details: Dict = None,
        **kwargs
    ):
        """记录CRITICAL日志"""
        log = self._create_log(
            LogLevel.CRITICAL, message, operation, step,
            error=error, details=details, **kwargs
        )
        self._emit(log)

    def _emit(self, log: StructuredLog):
        """输出日志"""
        if self.json_format:
            self.logger.info(log.to_json())
        else:
            log_line = f"[{log.timestamp}] [{log.level}] [{log.task_id or 'N/A'}] {log.message}"
            if log.error:
                log_line += f" Error: {log.error}"
            self.logger.info(log_line)

    def log_operation_start(self, operation: str, details: Dict = None):
        """记录操作开始"""
        self.info(
            f"Operation started: {operation}",
            operation=operation,
            step="start",
            details=details
        )

    def log_operation_complete(self, operation: str, duration_ms: float, details: Dict = None):
        """记录操作完成"""
        self.info(
            f"Operation completed: {operation}",
            operation=operation,
            step="complete",
            duration_ms=duration_ms,
            details=details
        )

    def log_operation_error(self, operation: str, error: Dict, details: Dict = None):
        """记录操作错误"""
        self.error(
            f"Operation failed: {operation}",
            operation=operation,
            step="error",
            error=error,
            details=details
        )
```

#### 9.11.2 性能指标收集

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import time
import asyncio

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"          # 计数器
    GAUGE = "gauge"              # 瞬时值
    HISTOGRAM = "histogram"      # 直方图
    SUMMARY = "summary"          # 摘要

@dataclass
class Metric:
    """指标数据模型"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = ""

@dataclass
class PerformanceMetrics:
    """性能指标收集器"""

    # 系统级指标
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)

    # 应用级指标
    request_count: int = 0
    request_latency_ms: float = 0.0
    error_count: int = 0
    active_tasks: int = 0

    # 业务指标
    code_analysis_count: int = 0
    patch_generation_count: int = 0
    test_execution_count: int = 0
    success_rate: float = 0.0

class MetricsCollector:
    """性能指标收集服务"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.metrics: Dict[str, List[Metric]] = {}
        self._lock = asyncio.Lock()

    async def record_counter(
        self,
        name: str,
        value: float = 1,
        labels: Dict = None,
        description: str = ""
    ):
        """记录计数器指标"""
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=value,
            labels=labels or {},
            description=description
        )
        await self._store_metric(metric)

    async def record_gauge(
        self,
        name: str,
        value: float,
        labels: Dict = None,
        description: str = ""
    ):
        """记录瞬时值指标"""
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            labels=labels or {},
            description=description
        )
        await self._store_metric(metric)

    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: Dict = None,
        description: str = ""
    ):
        """记录直方图指标"""
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            labels=labels or {},
            description=description
        )
        await self._store_metric(metric)

    async def _store_metric(self, metric: Metric):
        """存储指标"""
        async with self._lock:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = []
            self.metrics[metric.name].append(metric)

            # 限制内存中的指标数量
            max_entries = self.config.get("max_entries_per_metric", 1000)
            if len(self.metrics[metric.name]) > max_entries:
                self.metrics[metric.name] = self.metrics[metric.name][-max_entries:]

    def get_metrics(self, name: str = None) -> Dict[str, List[Metric]]:
        """获取指标"""
        if name:
            return {name: self.metrics.get(name, [])}
        return self.metrics

    def get_summary(self, name: str) -> Dict[str, Any]:
        """获取指标汇总"""
        metrics = self.metrics.get(name, [])
        if not metrics:
            return {}

        values = [m.value for m in metrics]

        return {
            "name": name,
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "last": values[-1] if values else None
        }

    async def record_task_duration(
        self,
        task_id: str,
        duration_ms: float,
        task_type: str,
        success: bool
    ):
        """记录任务执行时长"""
        await self.record_histogram(
            name="task_duration_ms",
            value=duration_ms,
            labels={
                "task_type": task_type,
                "success": str(success)
            },
            description="Task execution duration in milliseconds"
        )

        await self.record_counter(
            name="task_total",
            value=1,
            labels={
                "task_type": task_type,
                "success": str(success)
            }
        )

    async def record_llm_call(
        self,
        model: str,
        duration_ms: float,
        tokens: int,
        success: bool
    ):
        """记录LLM调用指标"""
        await self.record_histogram(
            name="llm_duration_ms",
            value=duration_ms,
            labels={"model": model, "success": str(success)},
            description="LLM API call duration"
        )

        await self.record_histogram(
            name="llm_tokens",
            value=tokens,
            labels={"model": model},
            description="Number of tokens in LLM call"
        )


class TimedContext:
    """计时上下文管理器"""

    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        labels: Dict = None
    ):
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        await self.collector.record_histogram(
            name=self.metric_name,
            value=duration_ms,
            labels=self.labels
        )
```

#### 9.11.3 分布式链路追踪

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

@dataclass
class TraceContext:
    """追踪上下文"""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

    def create_child(self) -> "TraceContext":
        """创建子span上下文"""
        return TraceContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            baggage=self.baggage.copy()
        )

@dataclass
class Span:
    """追踪跨度"""
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str = "ok"  # ok, error
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    links: List[Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links
        }


class DistributedTracer:
    """分布式链路追踪器"""

    def __init__(self, service_name: str, config: Dict = None):
        self.service_name = service_name
        self.config = config or {}
        self.current_context: Optional[TraceContext] = None
        self.spans: List[Span] = []

    def start_trace(self, baggage: Dict = None) -> TraceContext:
        """开始新的追踪"""
        self.current_context = TraceContext(baggage=baggage or {})
        return self.current_context

    def start_span(
        self,
        name: str,
        attributes: Dict = None
    ) -> Span:
        """开始新的span"""
        if not self.current_context:
            self.start_trace()

        span = Span(
            name=name,
            trace_id=self.current_context.trace_id,
            span_id=self.current_context.span_id,
            parent_span_id=self.current_context.parent_span_id,
            start_time=datetime.utcnow().isoformat(),
            attributes=attributes or {}
        )

        self.spans.append(span)

        # 更新当前上下文
        self.current_context = self.current_context.create_child()

        return span

    def end_span(self, span: Span, status: str = "ok"):
        """结束span"""
        span.end_time = datetime.utcnow().isoformat()
        span.status = status

        # 计算持续时间
        from datetime import datetime as dt
        start = dt.fromisoformat(span.start_time)
        end = dt.fromisoformat(span.end_time)
        span.duration_ms = (end - start).total_seconds() * 1000

    def add_span_event(
        self,
        span: Span,
        name: str,
        attributes: Dict = None
    ):
        """向span添加事件"""
        span.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {}
        })

    def inject_context(self) -> Dict[str, str]:
        """注入追踪上下文到传输格式"""
        if not self.current_context:
            return {}

        return {
            "trace_id": self.current_context.trace_id,
            "span_id": self.current_context.span_id,
            "parent_span_id": self.current_context.parent_span_id or "",
            "baggage": ",".join(f"{k}={v}" for k, v in self.current_context.baggage.items())
        }

    def extract_context(self, headers: Dict[str, str]) -> TraceContext:
        """从传输格式提取追踪上下文"""
        trace_id = headers.get("X-Trace-ID", str(uuid.uuid4()))
        span_id = headers.get("X-Span-ID", str(uuid.uuid4())[:16])
        parent_span_id = headers.get("X-Parent-Span-ID") or None

        baggage = {}
        baggage_header = headers.get("X-Baggage")
        if baggage_header:
            for item in baggage_header.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    baggage[k] = v

        self.current_context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=baggage
        )

        return self.current_context

    def get_trace_tree(self) -> Dict:
        """获取追踪树结构"""
        span_dict = {s.span_id: s.to_dict() for s in self.spans}

        # 构建树结构
        roots = []
        for span in self.spans:
            span_data = span_dict[span.span_id]
            if not span.parent_span_id:
                roots.append(span_data)
            else:
                parent = span_dict.get(span.parent_span_id)
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(span_data)

        return {
            "trace_id": self.spans[0].trace_id if self.spans else None,
            "spans_count": len(self.spans),
            "roots": roots
        }
```

---

### 9.12 错误隔离与恢复安全

#### 9.12.1 错误分类

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class ErrorCategory(Enum):
    """错误类别"""
    SYSTEM_ERROR = "system_error"           # 系统内部错误
    USER_ERROR = "user_error"               # 用户输入错误
    VALIDATION_ERROR = "validation_error"   # 验证失败
    EXTERNAL_DEPENDENCY_ERROR = "external"  # 外部依赖错误
    RESOURCE_ERROR = "resource_error"       # 资源不足错误
    TIMEOUT_ERROR = "timeout_error"         # 超时错误
    SECURITY_ERROR = "security_error"       # 安全相关错误
    UNKNOWN_ERROR = "unknown_error"         # 未知错误

class ErrorSeverity(Enum):
    """错误严重级别"""
    FATAL = "fatal"       # 导致系统不可用
    HIGH = "high"         # 主要功能受影响
    MEDIUM = "medium"     # 次要功能受影响
    LOW = "low"           # 轻微影响，可忽略

@dataclass
class SystemError:
    """系统错误数据模型"""
    category: ErrorCategory
    severity: ErrorSeverity
    error_code: str
    message: str
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None
    task_id: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_action: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "stack_trace": self.stack_trace,
            "recovery_action": self.recovery_action
        }


class ErrorClassifier:
    """错误分类器"""

    # 错误代码映射
    ERROR_CODE_MAP = {
        # 系统1错误 (xxx)
        "1001": (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH, "Null pointer exception"),
        "1002": (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH, "Index out of bounds"),
        "1003": (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.FATAL, "Out of memory"),
        "1004": (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH, "Database connection failed"),

        # 用户错误 (2xxx)
        "2001": (ErrorCategory.USER_ERROR, ErrorSeverity.LOW, "Invalid input format"),
        "2002": (ErrorCategory.USER_ERROR, ErrorSeverity.MEDIUM, "Required field missing"),
        "2003": (ErrorCategory.USER_ERROR, ErrorSeverity.LOW, "Duplicate entry"),

        # 验证错误 (3xxx)
        "3001": (ErrorCategory.VALIDATION_ERROR, ErrorSeverity.MEDIUM, "Schema validation failed"),
        "3002": (ErrorCategory.VALIDATION_ERROR, ErrorSeverity.HIGH, "Signature verification failed"),

        # 外部依赖错误 (4xxx)
        "4001": (ErrorCategory.EXTERNAL_DEPENDENCY_ERROR, ErrorSeverity.MEDIUM, "LLM API timeout"),
        "4002": (ErrorCategory.EXTERNAL_DEPENDENCY_ERROR, ErrorSeverity.HIGH, "LLM API rate limit"),
        "4003": (ErrorCategory.EXTERNAL_DEPENDENCY_ERROR, ErrorSeverity.HIGH, "Git repository access failed"),
        "4004": (ErrorCategory.EXTERNAL_DEPENDENCY_ERROR, ErrorSeverity.MEDIUM, "Build tool not found"),

        # 资源错误 (5xxx)
        "5001": (ErrorCategory.RESOURCE_ERROR, ErrorSeverity.HIGH, "Insufficient disk space"),
        "5002": (ErrorCategory.RESOURCE_ERROR, ErrorSeverity.MEDIUM, "Memory limit exceeded"),
        "5003": (ErrorCategory.RESOURCE_ERROR, ErrorSeverity.HIGH, "Network bandwidth exceeded"),

        # 超时错误 (6xxx)
        "6001": (ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM, "Task execution timeout"),
        "6002": (ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.LOW, "Query timeout"),

        # 安全错误 (7xxx)
        "7001": (ErrorCategory.SECURITY_ERROR, ErrorSeverity.FATAL, "Authentication failed"),
        "7002": (ErrorCategory.SECURITY_ERROR, ErrorSeverity.HIGH, "Authorization denied"),
        "7003": (ErrorCategory.SECURITY_ERROR, ErrorSeverity.CRITICAL, "Potential security threat detected"),
    }

    def classify(
        self,
        exception: Exception,
        error_code: str = None,
        context: Dict = None
    ) -> SystemError:
        """分类错误"""
        # 确定错误代码
        code = error_code or self._extract_error_code(exception)

        # 确定类别和严重级别
        if code in self.ERROR_CODE_MAP:
            category, severity, base_message = self.ERROR_CODE_MAP[code]
        else:
            category = ErrorCategory.UNKNOWN_ERROR
            severity = ErrorSeverity.MEDIUM
            base_message = str(exception)

        return SystemError(
            category=category,
            severity=severity,
            error_code=code,
            message=base_message,
            details={
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                **(context or {})
            },
            stack_trace=self._extract_stack_trace(exception)
        )

    def _extract_error_code(self, exception: Exception) -> str:
        """从异常中提取错误代码"""
        if hasattr(exception, "error_code"):
            return exception.error_code
        return "0000"  # 未知错误代码

    def _extract_stack_trace(self, exception: Exception) -> str:
        """提取堆栈跟踪"""
        import traceback
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
```

#### 9.12.2 错误隔离机制

```python
from abc import ABC, abstractmethod
from typing import Callable, Any, TypeVar, Dict
import asyncio
import contextlib

T = TypeVar("T")

class ErrorBoundary:
    """错误边界容器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.error_handlers: Dict[str, Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}

    def register_error_handler(
        self,
        error_type: type,
        handler: Callable[[Exception], Any]
    ):
        """注册错误处理器"""
        self.error_handlers[error_type.__name__] = handler

    def register_fallback(
        self,
        operation_name: str,
        fallback: Callable[..., Any]
    ):
        """注册降级处理器"""
        self.fallback_handlers[operation_name] = fallback

    @contextlib.asynccontextmanager
    async def capture(
        self,
        operation_name: str,
        reraise: bool = True,
        context: Dict = None
    ):
        """捕获错误的上下文管理器"""
        try:
            yield
        except Exception as e:
            # 记录错误
            await self._handle_error(e, operation_name, context)

            # 调用错误处理器
            handler_name = type(e).__name__
            if handler_name in self.error_handlers:
                await self.error_handlers[handler_name](e)

            # 调用降级处理器
            if operation_name in self.fallback_handlers:
                await self.fallback_handlers[operation_name](e)

            if reraise:
                raise

    async def capture_sync(
        self,
        operation_name: str,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """同步函数错误捕获包装器"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            await self._handle_error(e, operation_name, {})
            if operation_name in self.fallback_handlers:
                return self.fallback_handlers[operation_name](e)
            raise

    async def _handle_error(
        self,
        error: Exception,
        operation_name: str,
        context: Dict
    ):
        """处理错误"""
        # 记录到监控系统
        print(f"Error in {operation_name}: {error}")

    def circuit_breaker(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        """熔断器装饰器"""
        def decorator(func: Callable):
            state = {"failures": 0, "last_failure": None, "state": "closed"}

            async def wrapper(*args, **kwargs):
                if state["state"] == "open":
                    # 检查是否超时
                    if state["last_failure"] and \
                       (datetime.utcnow() - state["last_failure"]).seconds > recovery_timeout:
                        state["state"] = "half_open"
                    else:
                        raise CircuitOpenError(
                            f"Circuit breaker is open for {func.__name__}"
                        )

                try:
                    result = await func(*args, **kwargs)
                    state["failures"] = 0
                    state["state"] = "closed"
                    return result
                except Exception as e:
                    state["failures"] += 1
                    state["last_failure"] = datetime.utcnow()

                    if state["failures"] >= failure_threshold:
                        state["state"] = "open"

                    raise

            return wrapper
        return decorator


class CircuitOpenError(Exception):
    """熔断器开启错误"""
    pass


class IsolationManager:
    """错误隔离管理器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.resource_limits = self._init_resource_limits()
        self.isolation_groups: Dict[str, set] = {}

    def _init_resource_limits(self) -> Dict:
        """初始化资源限制"""
        return {
            "max_concurrent_tasks": self.config.get("max_concurrent_tasks", 100),
            "max_memory_per_task_mb": self.config.get("max_memory_per_task_mb", 1024),
            "max_execution_time_seconds": self.config.get("max_execution_time", 3600),
            "max_file_descriptors": self.config.get("max_file_descriptors", 1024),
        }

    async def validate_resource_usage(self, task_id: str) -> bool:
        """验证资源使用是否在限制内"""
        current_usage = await self._get_current_usage()

        return (
            current_usage["active_tasks"] < self.resource_limits["max_concurrent_tasks"]
            and current_usage["memory_mb"] < self.resource_limits["max_memory_per_task_mb"]
        )

    async def _get_current_usage(self) -> Dict:
        """获取当前资源使用情况"""
        import psutil
        process = psutil.Process()
        return {
            "active_tasks": 0,  # 从任务管理器获取
            "memory_mb": process.memory_info().rss / (1024 * 1024),
            "cpu_percent": process.cpu_percent()
        }

    def create_isolation_group(self, group_id: str, members: set):
        """创建隔离组"""
        self.isolation_groups[group_id] = members

    async def execute_in_isolation(
        self,
        group_id: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """在隔离环境中执行操作"""
        if group_id not in self.isolation_groups:
            raise ValueError(f"Isolation group {group_id} not found")

        # 设置资源限制
        import resource
        limits = self.resource_limits

        # 设置最大文件描述符
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (limits["max_file_descriptors"], limits["max_file_descriptors"])
        )

        try:
            return await operation(*args, **kwargs)
        finally:
            # 恢复默认限制
            resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
```

#### 9.12.3 恢复流程安全验证

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class RecoveryStatus(Enum):
    """恢复状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"

class RecoveryCheckpoint:
    """恢复检查点"""

    def __init__(self, checkpoint_id: str, data: Dict):
        self.checkpoint_id = checkpoint_id
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """计算数据校验和"""
        import hashlib
        data_str = str(self.data) + self.timestamp
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def verify(self) -> bool:
        """验证检查点完整性"""
        return self.checksum == self._calculate_checksum()


@dataclass
class RecoveryPlan:
    """恢复计划"""
    plan_id: str
    task_id: str
    checkpoints: List[RecoveryCheckpoint]
    recovery_steps: List[Dict]
    rollback_plan: Dict
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: RecoveryStatus = RecoveryStatus.NOT_STARTED


class RecoveryValidator:
    """恢复验证器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    async def validate_recovery(
        self,
        recovery_plan: RecoveryPlan,
        current_state: Dict
    ) -> Dict[str, Any]:
        """验证恢复计划的有效性"""
        validations = {
            "checkpoint_integrity": self._validate_checkpoints(recovery_plan.checkpoints),
            "state_compatibility": self._validate_state_compatibility(
                recovery_plan, current_state
            ),
            "rollback_safety": self._validate_rollback_safety(recovery_plan),
            "resource_availability": await self._validate_resources()
        }

        # 计算总体验证结果
        all_passed = all(
            v.get("passed", False) for v in validations.values()
        )

        return {
            "valid": all_passed,
            "validations": validations,
            "recommendations": self._generate_recommendations(validations)
        }

    def _validate_checkpoints(
        self,
        checkpoints: List[RecoveryCheckpoint]
    ) -> Dict:
        """验证检查点完整性"""
        results = {
            "passed": True,
            "details": [],
            "issues": []
        }

        for cp in checkpoints:
            if cp.verify():
                results["details"].append(
                    f"Checkpoint {cp.checkpoint_id}: valid"
                )
            else:
                results["passed"] = False
                results["issues"].append(
                    f"Checkpoint {cp.checkpoint_id}: checksum mismatch"
                )

        if not checkpoints:
            results["passed"] = False
            results["issues"].append("No checkpoints available")

        return results

    def _validate_state_compatibility(
        self,
        recovery_plan: RecoveryPlan,
        current_state: Dict
    ) -> Dict:
        """验证状态兼容性"""
        results = {
            "passed": True,
            "details": [],
            "issues": []
        }

        # 验证必需的检查点
        required_fields = ["task_id", "agent_states", "configuration"]
        for field in required_fields:
            if field not in current_state:
                results["passed"] = False
                results["issues"].append(f"Missing required field: {field}")

        # 验证版本兼容性
        if recovery_plan.checkpoints:
            latest_cp = recovery_plan.checkpoints[-1]
            if latest_cp.data.get("version") != current_state.get("version"):
                results["issues"].append(
                    "Version mismatch between checkpoint and current state"
                )

        return results

    def _validate_rollback_safety(
        self,
        recovery_plan: RecoveryPlan
    ) -> Dict:
        """验证回滚安全性"""
        results = {
            "passed": True,
            "details": [],
            "issues": []
        }

        # 验证回滚计划存在
        if not recovery_plan.rollback_plan:
            results["passed"] = False
            results["issues"].append("Rollback plan not defined")
            return results

        # 验证回滚步骤
        rollback_steps = recovery_plan.rollback_plan.get("steps", [])
        if not rollback_steps:
            results["issues"].append("No rollback steps defined")

        # 验证数据一致性保证
        if "data_consistency" not in recovery_plan.rollback_plan:
            results["issues"].append(
                "Rollback plan does not guarantee data consistency"
            )

        return results

    async def _validate_resources(self) -> Dict:
        """验证资源可用性"""
        results = {
            "passed": True,
            "details": [],
            "issues": []
        }

        # 检查磁盘空间
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)

        if free_gb < self.config.get("min_disk_space_gb", 5):
            results["passed"] = False
            results["issues"].append(f"Low disk space: {free_gb}GB available")
        else:
            results["details"].append(f"Disk space: {free_gb}GB available")

        return results

    def _generate_recommendations(self, validations: Dict) -> List[str]:
        """生成恢复建议"""
        recommendations = []

        for name, result in validations.items():
            if not result.get("passed", False):
                for issue in result.get("issues", []):
                    if name == "checkpoint_integrity":
                        recommendations.append(
                            "建议：从最近的已知良好状态重新创建检查点"
                        )
                    elif name == "state_compatibility":
                        recommendations.append(
                            "建议：检查系统版本并执行必要的迁移步骤"
                        )
                    elif name == "rollback_safety":
                        recommendations.append(
                            "建议：手动验证数据一致性后再继续"
                        )
                    elif name == "resource_availability":
                        recommendations.append(
                            "建议：释放资源或扩展存储空间"
                        )

        return recommendations


class RecoveryExecutor:
    """恢复执行器"""

    def __init__(
        self,
        validator: RecoveryValidator,
        logger,
        config: Dict = None
    ):
        self.validator = validator
        self.logger = logger
        self.config = config or {}

    async def execute_recovery(
        self,
        recovery_plan: RecoveryPlan,
        current_state: Dict
    ) -> Dict:
        """执行恢复流程"""
        # 验证恢复计划
        validation_result = await self.validator.validate_recovery(
            recovery_plan, current_state
        )

        if not validation_result["valid"]:
            return {
                "status": RecoveryStatus.FAILED,
                "reason": "Recovery plan validation failed",
                "validations": validation_result
            }

        # 执行恢复步骤
        for step in recovery_plan.recovery_steps:
            try:
                await self._execute_step(step)
            except Exception as e:
                self.logger.error(f"Recovery step failed: {step}", error={"error": str(e)})
                # 触发回滚
                return await self._execute_rollback(recovery_plan.rollback_plan)

        return {
            "status": RecoveryStatus.SUCCESS,
            "checkpoints_restored": len(recovery_plan.checkpoints),
            "validations": validation_result
        }

    async def _execute_step(self, step: Dict):
        """执行单个恢复步骤"""
        step_type = step.get("type")
        params = step.get("params", {})

        if step_type == "restore_snapshot":
            await self._restore_snapshot(params)
        elif step_type == "restore_database":
            await self._restore_database(params)
        elif step_type == "reinitialize_agent":
            await self._reinitialize_agent(params)

    async def _restore_snapshot(self, params: Dict):
        """恢复快照"""
        snapshot_id = params.get("snapshot_id")
        # 实现快照恢复逻辑
        pass

    async def _restore_database(self, params: Dict):
        """恢复数据库"""
        backup_path = params.get("backup_path")
        # 实现数据库恢复逻辑
        pass

    async def _reinitialize_agent(self, params: Dict):
        """重新初始化Agent"""
        agent_id = params.get("agent_id")
        # 实现Agent重初始化逻辑
        pass

    async def _execute_rollback(self, rollback_plan: Dict) -> Dict:
        """执行回滚"""
        self.logger.warning("Executing rollback plan")
        # 实现回滚逻辑
        return {
            "status": RecoveryStatus.ROLLBACK,
            "rollback_plan": rollback_plan
        }
```

---

## 1. 核心模块详细设计

### 1.1 CodeAnalyzer（代码分析器）

**职责定位**：基于Tree-sitter和AI模型的C/C++代码智能分析引擎

**核心功能**：
- C/C++语法解析和AST构建
- 静态代码分析（clang-tidy、cppcheck集成）
- AI辅助代码理解和问题诊断
- 代码度量计算和复杂度分析
- 依赖关系图构建

**接口定义**：
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AnalysisType(Enum):
    SYNTAX = "syntax"
    STATIC = "static" 
    SEMANTIC = "semantic"
    METRICS = "metrics"
    DEPENDENCY = "dependency"

@dataclass
class CodeFile:
    file_path: str
    content: str
    language: str
    encoding: str = "utf-8"

@dataclass
class AnalysisResult:
    analysis_id: str
    file_count: int
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    dependency_graph: Dict[str, Any]
    confidence_score: float

class CodeAnalyzer:
    """代码分析器主接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tree_sitter_parser = self._init_tree_sitter()
        self.static_analyzers = self._init_static_analyzers()
        self.ai_model = self._init_ai_model()
        
    async def analyze_code(self, 
                          files: List[CodeFile], 
                          analysis_type: AnalysisType,
                          context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """分析代码并返回结构化结果"""
        pass
        
    async def detect_issues(self, 
                          files: List[CodeFile],
                          rules: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """检测代码问题"""
        pass
        
    async def calculate_metrics(self, files: List[CodeFile]) -> Dict[str, Any]:
        """计算代码度量"""
        pass
        
    async def build_dependency_graph(self, files: List[CodeFile]) -> Dict[str, Any]:
        """构建依赖关系图"""
        pass
```

**实现要点**：
- 支持增量分析，只处理变更文件
- 集成多个静态分析工具，统一输出格式
- AI模型提供语义级理解和问题诊断
- 支持自定义分析规则和插件扩展

### 1.2 CodeModifier（代码修改器）

**职责定位**：基于分析结果生成和应用代码修改的智能引擎

**核心功能**：
- AI驱动的代码修改建议生成
- Patch文件生成和应用
- 代码冲突检测和解决
- 修改安全性验证
- 回滚机制实现

**接口定义**：
```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskAssessment:
    """代码修改风险评估数据模型"""
    plan_id: str
    affected_files_count: int
    total_lines_added: int
    total_lines_removed: int
    impact_scope: List[str]  # 受影响的功能模块或路径
    security_level: RiskLevel
    risk_score: float        # 0.0 - 1.0 的量化分值
    warnings: List[str]      # 具体的风险提示信息

@dataclass
class ModificationPlan:
    plan_id: str
    target_files: List[str]
    changes: List[Dict[str, Any]]
    risk_level: str
    dependencies: List[str]
    rollback_info: Dict[str, Any]
    risk_assessment: Optional[RiskAssessment] = None

@dataclass
class ModificationResult:
    result_id: str
    success: bool
    applied_patches: List[str]
    failed_patches: List[Dict[str, Any]]
    build_status: str
    conflict_resolution: Optional[Dict[str, Any]]

class CodeModifier:
    """代码修改器主接口"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ai_model = self._init_ai_model()
        self.git_handler = self._init_git_handler()
        self.patch_generator = self._init_patch_generator()

    async def generate_modifications(self,
                                   analysis_result: AnalysisResult,
                                   requirements: Dict[str, Any]) -> List[ModificationPlan]:
        """生成修改方案"""
        pass

    async def apply_modifications(self,
                                plans: List[ModificationPlan],
                                dry_run: bool = False) -> ModificationResult:
        """应用代码修改"""
        pass

    async def diff_preview(self, plans: List[ModificationPlan]) -> List[Dict[str, Any]]:
        """生成修改预览，返回修改前后对比"""
        pass

    async def validate_patch(self, patch_content: str) -> Dict[str, Any]:
        """补丁安全性校验，检查敏感API和权限操作"""
        pass

    async def create_patch(self,
                          file_path: str,
                          original_content: str,
                          modified_content: str) -> str:
        """创建Git patch文件"""
        pass

    async def rollback(self, plan_id: str) -> bool:
        """基于快照或Git记录撤销修改"""
        pass

    async def request_approval(self, plan_id: str) -> bool:
        """应用补丁前的人工审批逻辑"""
        pass
```

**实现要点**：
- 支持多种修改策略（最小化修改、特性添加、bug修复等）
- 集成编译检查确保修改后代码可编译
- 支持原子性操作，要么全部成功要么全部回滚
- 提供详细的修改日志和影响分析

#### 1.2.1 安全修改流程与审批机制

在自动修复循环中，为防止 AI 生成不当修改导致系统崩溃或安全漏洞，CodeModifier 引入了标准化的预览与审批流。

**1. 补丁应用生命周期**
1. **生成 (Generation)**: CodeAgent 生成初步的修改方案。
2. **评估 (Assessment)**: 自动调用风险评估模块生成 `RiskAssessment` 报告。
3. **预览 (Preview)**: 生成统一差分格式 (Unified Diff) 供审计。
4. **审批 (Approval)**: 根据风险等级决定是自动执行还是等待人工干预。
5. **执行 (Execution)**: 创建快照并应用补丁。
6. **验证 (Verification)**: 执行编译和冒烟测试。

**2. Diff 预览技术细节**
`diff_preview` 接口返回的数据结构不仅包含代码差异，还包含上下文语义：
- **语义摘要**: 描述每个 Hunk 的修改意图（如“修复数组越界”、“更新配置参数”）。
- **影响分析**: 识别修改涉及的函数调用链，预测可能产生的侧面影响。
- **冲突检测**: 实时对比当前仓库状态，识别是否存在 Patch 冲突。

**3. 审批工作流设计**
审批逻辑支持灵活配置。对于固件开发，默认策略如下：
- **低风险**: 修改注释、增加测试用例、不涉及逻辑的重构 -> 自动审批。
- **中风险**: 业务逻辑修改、新功能添加 -> 需要 1 名开发人员审批。
- **高风险**: 修改 `common` 库、修改中断处理、修改内存分配器 -> 需要 2 名以上专家（含安全专家）审批。

#### 1.2.2 风险评估系统设计

风险评估模块是 CodeModifier 的核心守门人，它通过静态和动态特征量化补丁风险。

**1. 风险评分维度 (Risk Scoring Metrics)**
| 维度 | 检查项 | 权重 | 说明 |
| :--- | :--- | :--- | :--- |
| **规模 (Scale)** | 变更行数/文件数 | 15% | 大范围修改通常意味着更高的不确定性 |
| **位置 (Location)** | 关键路径/目录匹配 | 30% | 修改驱动、内核、加密模块风险极高 |
| **API 安全 (API)** | 禁止/危险函数调用 | 25% | 检查补丁是否引入了不安全的 C 标准库函数 |
| **复杂度 (Complexity)** | 圈复杂度增量 | 20% | 逻辑过于复杂的补丁难以维护且易藏 Bug |
| **合规性 (Compliance)** | 编码规范违反项 | 10% | 是否符合 MISRA C 或公司内部规范 |

**2. 自动阻断阈值**
系统预设了 `CRITICAL_RISK_THRESHOLD = 0.8`。任何评估分数超过此值的补丁将被直接拦截并标记为 `Rejected`，要求 Agent 重新设计方案。

**3. 风险评估流程图**
```mermaid
graph TD
    A[开始风险评估] --> B{解析补丁内容}
    B --> C[统计变更规模]
    B --> D[识别敏感API]
    B --> E[分析修改路径]
    C --> F[计算加权风险分数]
    D --> F
    E --> F
    F --> G{分数 > 阈值?}
    G -- 是 --> H[触发人工审批]
    G -- 否 --> I[自动审批通过]
    H --> J[更新风险等级]
    I --> J
    J --> K[返回RiskAssessment结果]
```

#### 1.2.3 自动化安全校验点

`validate_patch()` 方法在补丁应用前执行深度扫描，确保补丁本身不含有“毒素”。

**1. 敏感 API 扫描 (Banned API Checker)**
- **强制检查项**: `strcpy`, `strcat`, `gets`, `sprintf`, `vsprintf` 等。
- **建议替代方案**: 自动提示将 `strcpy` 替换为 `strncpy` 或更安全的库函数。

**2. 权限与敏感操作校验**
- **文件权限**: 禁止在补丁中直接调用 `chmod 777` 或类似提权操作。
- **网络访问**: 检查是否引入了未经授权的网络套接字创建逻辑。
- **硬编码密钥**: 扫描补丁是否包含硬编码的密码、Token 或加密密钥。

**3. 资源管理检查**
- **内存对齐**: 在固件开发中，检查修改后的数据结构是否破坏了内存对齐要求。
- **锁平衡**: 如果补丁涉及互斥锁 (Mutex) 或信号量，校验锁定与释放逻辑是否成对出现，防止死锁。

#### 1.2.4 原子化操作与回滚保障

为应对固件测试中常见的环境崩溃问题，CodeModifier 实现了严格的事务性保障。

**1. 快照与备份策略**
- **Git 原子提交**: 利用 Git 暂存区和分支机制。补丁应用在临时分支上，通过测试后再合并。
- **物理备份**: 对于非 Git 追踪的配置文件，在修改前执行 `tar` 压缩备份至指定安全位置。
- **数据库快照**: 如果修改涉及配置数据库，执行 `SQL Dump` 快照。

**2. 交互时序图**
```mermaid
sequenceDiagram
    participant Agent as CodeAgent
    participant CM as CodeModifier
    participant Auditor as Human Auditor
    participant Repo as Repository

    Agent->>CM: generate_modifications()
    CM->>CM: Risk Assessment
    CM->>CM: validate_patch()
    
    alt risk_score > threshold
        CM->>Auditor: request_approval(plan_id)
        Auditor-->>CM: approved / rejected
    else risk_score <= threshold
        CM->>CM: Auto-approve
    end
    
    CM->>Repo: create_snapshot()
    CM->>Repo: apply_patches()
    
    alt build_failed OR test_failed
        CM->>Repo: rollback(plan_id)
    else success
        CM->>Repo: commit_changes()
    end
```

**3. 回滚执行路径**
`rollback()` 方法支持以下两种回滚模式：
- **Soft Rollback**: 通过 `git checkout` 或 `git revert` 撤销代码层面的修改。
- **Hard Rollback**: 直接从磁盘备份恢复物理文件，并重置环境状态（如数据库、配置文件）。

#### 1.2.5 代码修改安全性原则与规范

为指导 Agent 生成更高质量的补丁，我们定义了以下安全性原则。

**1. 最小变更原则 (Least Change Principle)**
- **聚焦补丁**: 严禁在修复一个 Bug 的同时进行无关的代码重构。
- **限制范围**: 修改范围应限制在受影响的函数内部，除非必须通过接口变更解决。

**2. 防御性编程规范**
- **输入校验**: 所有从外部读取的参数（如硬件寄存器、网络包）在处理前必须校验合法性。
- **溢出预防**: 涉及算术运算的地方应优先使用带溢出检测的宏或库。
- **指针安全**: 在解引用前必须显式进行非空检查。

**3. 资源生命周期管理**
- **配对原则**: 所有的 `malloc` 必须有对应的 `free`，所有的 `lock` 必须有对应的 `unlock`。
- **错误路径清理**: 在函数的错误返回分支中，必须正确释放已申请的资源。

#### 1.2.6 典型安全校验场景示例与审计规范

**1. 典型校验场景**
- **场景 A：处理缓冲区溢出**: Agent 识别出 `strcpy` 导致潜在溢出。方案：替换为 `strncpy` 且手动补齐 `\0`。校验：`validate_patch` 检查是否正确处理了 `N-1` 长度及截断情况。
- **场景 B：修改敏感配置**: 修改 SSH 端口配置。方案：更新配置文件解析逻辑。校验：`RiskAssessment` 识别为 `High` 风险，强制触发人工审批。

**2. 审计日志规范**
每次补丁应用均需记录审计日志，包含：
- **操作流水**: 时间戳、操作员 ID、计划 ID。
- **变更证据**: 修改前后的代码片段、Patch 文件。
- **评估报告**: 风险分值、警告信息、审批记录。
- **执行结果**: 编译状态、冒烟测试结果、回滚触发原因（如有）。

### 1.3 ResultAnalyzer（结果分析器）

**职责定位**：对测试产物进行结构化解析与归因汇总，输出可用于决策的分析结果。

**核心功能**：
- 日志/报告解析与标准化
- 失败类型归类与证据抽取
- 关键指标统计（耗时、通过率、失败分布）
- 生成结构化分析结论与建议摘要

**接口定义**：
```python
@dataclass
class RawTestArtifacts:
    logs: List[str]
    reports: List[str]
    metrics: Dict[str, Any]

@dataclass
class AnalysisSummary:
    status: str
    failure_type: Optional[str]
    evidence: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]

class ResultAnalyzer:
    """结果分析器主接口"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parsers = self._init_parsers()

    async def analyze(self, artifacts: RawTestArtifacts) -> AnalysisSummary:
        """解析测试产物并输出结构化结论"""
        pass
```

**实现要点**：
- 解析器可插件化扩展（不同测试框架/日志格式）。
- 输出需满足可追溯性要求（保留证据引用）。

### 1.4 TestOrchestrator（测试编排器）

**职责定位**：统一的测试执行编排引擎，支持多环境测试

**核心功能**：
- 测试环境抽象和生命周期管理
- QEMU和目标板的统一接口
- 测试用例调度和执行
- 并发控制和资源管理
- 测试结果统一收集

**接口定义**：
```python
from enum import Enum

class EnvironmentType(Enum):
    QEMU = "qemu"
    TARGET_BOARD = "target_board"
    BMC = "bmc"
    WINDOWS_SCRIPT = "windows_script"

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestCase:
    case_id: str
    name: str
    command: str
    timeout: int
    environment_vars: Dict[str, str]
    expected_result: Optional[Dict[str, Any]]

@dataclass
class TestResult:
    result_id: str
    case_id: str
    status: TestStatus
    exit_code: Optional[int]
    output: str
    error_output: str
    execution_time: float
    artifacts: List[str]

class TestEnvironment:
    """测试环境抽象"""

    def __init__(self, env_type: EnvironmentType, config: Dict[str, Any]):
        self.env_type = env_type
        self.config = config
        self.status = "initialized"

    async def setup(self) -> bool:
        """环境准备"""
        pass

    async def start(self) -> bool:
        """启动环境"""
        pass

    async def execute_test(self, test_case: TestCase) -> TestResult:
        """执行测试"""
        pass

    async def cleanup(self):
        """环境清理"""
        pass

class TestOrchestrator:
    """测试编排器主接口"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.environments: Dict[str, TestEnvironment] = {}
        self.test_scheduler = self._init_scheduler()
        self.result_collector = self._init_collector()

    async def register_environment(self,
                                  env_id: str,
                                  env_type: EnvironmentType,
                                  config: Dict[str, Any]) -> bool:
        """注册测试环境"""
        pass

    async def execute_test_suite(self,
                               env_id: str,
                               test_cases: List[TestCase],
                               parallel: bool = False) -> List[TestResult]:
        """执行测试套件"""
        pass

    async def monitor_environment(self, env_id: str) -> Dict[str, Any]:
        """监控环境状态"""
        pass
```

**实现要点**：
- 支持动态环境创建和销毁
- 实现资源池管理，避免环境冲突
- 提供统一的日志和指标收集
- 支持测试用例的优先级和依赖关系管理

#### 1.3.1 TestEnvironment基类设计

为统一不同测试环境（QEMU、目标板、BMC等）的管理，TestOrchestrator定义了通用的环境抽象基类，确保所有环境具有标准化的生命周期管理和健康检查机制。

**统一基类接口定义**：
```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio

class EnvironmentState(Enum):
    """环境状态枚举"""
    INITIALIZED = "initialized"      # 初始化完成
    SETTING_UP = "setting_up"        # 环境准备中
    READY = "ready"                  # 环境就绪
    RUNNING = "running"              # 测试执行中
    CLEANING = "cleaning"            # 清理中
    ERROR = "error"                  # 错误状态
    UNHEALTHY = "unhealthy"          # 不健康状态

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class EnvironmentConfig:
    """环境配置数据模型"""
    env_id: str
    env_type: EnvironmentType
    timeout: int = 300
    retry_count: int = 3
    health_check_interval: int = 30
    log_level: str = "INFO"
    resource_constraints: Dict[str, Any] = None

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    checks: Dict[str, bool]
    metrics: Dict[str, float]
    message: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class LogSource:
    """日志源定义"""
    name: str
    path: str
    type: str  # stdout, stderr, file, serial, network
    format: str = "text"  # text, json, binary

class TestEnvironment(ABC):
    """测试环境抽象基类 - 统一接口规范"""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.env_id = config.env_id
        self.env_type = config.env_type
        self.state = EnvironmentState.INITIALIZED
        self.log_collector = LogCollector(config)
        self.metrics_collector = MetricsCollector(config)
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_result: Optional[HealthCheckResult] = None
        self._lock = asyncio.Lock()
        self._active_tests = 0
        
    # ==================== 生命周期管理 ====================
    
    async def setup(self) -> bool:
        """
        环境准备 - 初始化必要资源和配置
        返回: 准备是否成功
        """
        async with self._lock:
            if self.state != EnvironmentState.INITIALIZED:
                raise RuntimeError(f"Cannot setup from state: {self.state}")
            
            self.state = EnvironmentState.SETTING_UP
            try:
                success = await self._setup_internal()
                if success:
                    self.state = EnvironmentState.READY
                    # 启动健康检查任务
                    self._health_check_task = asyncio.create_task(self._health_check_loop())
                else:
                    self.state = EnvironmentState.ERROR
                return success
            except Exception as e:
                self.state = EnvironmentState.ERROR
                await self.log_collector.collect_log("setup", f"Setup failed: {str(e)}", "ERROR")
                return False
    
    @abstractmethod
    async def _setup_internal(self) -> bool:
        """子类实现具体的环境准备逻辑"""
        pass
    
    async def start(self) -> bool:
        """
        启动环境 - 实际启动目标环境
        返回: 启动是否成功
        """
        async with self._lock:
            if self.state not in [EnvironmentState.READY, EnvironmentState.CLEANING]:
                raise RuntimeError(f"Cannot start from state: {self.state}")
            
            try:
                success = await self._start_internal()
                if success:
                    self.state = EnvironmentState.RUNNING
                    await self.log_collector.collect_log("start", "Environment started successfully", "INFO")
                return success
            except Exception as e:
                self.state = EnvironmentState.ERROR
                await self.log_collector.collect_log("start", f"Start failed: {str(e)}", "ERROR")
                return False
    
    @abstractmethod
    async def _start_internal(self) -> bool:
        """子类实现具体的环境启动逻辑"""
        pass
    
    async def execute_test(self, test_case: TestCase) -> TestResult:
        """
        执行测试 - 在环境中运行测试用例
        返回: 测试结果
        """
        if self.state != EnvironmentState.RUNNING:
            raise RuntimeError(f"Cannot execute test in state: {self.state}")
        
        async with self._lock:
            self._active_tests += 1
        
        try:
            # 启动前健康检查
            health_result = await self.health_check()
            if health_result.status != HealthStatus.HEALTHY:
                await self.log_collector.collect_log(
                    "test", 
                    f"Skipping test due to unhealthy environment: {health_result.message}", 
                    "WARNING"
                )
                return TestResult(
                    result_id=f"{test_case.case_id}_skipped",
                    case_id=test_case.case_id,
                    status=TestStatus.SKIPPED,
                    output="",
                    error_output=f"Unhealthy environment: {health_result.message}",
                    execution_time=0.0,
                    artifacts=[]
                )
            
            result = await self._execute_test_internal(test_case)
            return result
        finally:
            async with self._lock:
                self._active_tests -= 1
    
    @abstractmethod
    async def _execute_test_internal(self, test_case: TestCase) -> TestResult:
        """子类实现具体的测试执行逻辑"""
        pass
    
    async def cleanup(self) -> bool:
        """
        环境清理 - 释放资源和执行清理操作
        返回: 清理是否成功
        """
        async with self._lock:
            if self._health_check_task:
                self._health_check_task.cancel()
                self._health_check_task = None
            
            self.state = EnvironmentState.CLEANING
            try:
                success = await self._cleanup_internal()
                self.state = EnvironmentState.INITIALIZED if success else EnvironmentState.ERROR
                await self.log_collector.collect_log("cleanup", "Environment cleanup completed", "INFO")
                return success
            except Exception as e:
                self.state = EnvironmentState.ERROR
                await self.log_collector.collect_log("cleanup", f"Cleanup failed: {str(e)}", "ERROR")
                return False
    
    @abstractmethod
    async def _cleanup_internal(self) -> bool:
        """子类实现具体的环境清理逻辑"""
        pass
    
    # ==================== 健康检查与恢复 ====================
    
    async def health_check(self) -> HealthCheckResult:
        """
        同步健康检查 - 立即执行一次健康检查
        返回: 健康检查结果
        """
        try:
            result = await self._perform_health_checks()
            self._last_health_result = result
            
            if result.status != HealthStatus.HEALTHY:
                async with self._lock:
                    self.state = EnvironmentState.UNHEALTHY
            
            return result
        except Exception as e:
            await self.log_collector.collect_log("health_check", f"Health check failed: {str(e)}", "ERROR")
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                checks={},
                metrics={},
                message=f"Health check exception: {str(e)}"
            )
    
    @abstractmethod
    async def _perform_health_checks(self) -> HealthCheckResult:
        """
        子类实现具体的健康检查逻辑
        应包含多个检查项（CPU、内存、连接状态等）
        """
        pass
    
    async def _health_check_loop(self):
        """后台健康检查循环"""
        while True:
            try:
                if self.state in [EnvironmentState.READY, EnvironmentState.RUNNING]:
                    await self.health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log_collector.collect_log("health_check", f"Health check loop error: {str(e)}", "ERROR")
    
    async def recover_from_failure(self, failure_info: Dict[str, Any]) -> bool:
        """
        故障恢复 - 自动尝试从故障状态中恢复
        返回: 恢复是否成功
        """
        async with self._lock:
            if self.state not in [EnvironmentState.ERROR, EnvironmentState.UNHEALTHY]:
                return True  # 无需恢复
            
            await self.log_collector.collect_log("recovery", f"Attempting recovery from {self.state}", "INFO")
            
            try:
                success = await self._recover_internal(failure_info)
                if success:
                    self.state = EnvironmentState.READY
                    await self.log_collector.collect_log("recovery", "Recovery successful", "INFO")
                return success
            except Exception as e:
                await self.log_collector.collect_log("recovery", f"Recovery failed: {str(e)}", "ERROR")
                return False
    
    async def _recover_internal(self, failure_info: Dict[str, Any]) -> bool:
        """
        子类实现具体的故障恢复逻辑
        默认实现：cleanup -> setup -> start
        """
        try:
            await self.cleanup()
            await self.setup()
            return await self.start()
        except Exception:
            return False
    
    async def wait_until_ready(self, timeout: Optional[int] = None) -> bool:
        """
        等待环境就绪
        返回: 是否在指定时间内就绪
        """
        timeout = timeout or self.config.timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self.state == EnvironmentState.RUNNING:
                health = await self.health_check()
                if health.status == HealthStatus.HEALTHY:
                    return True
            elif self.state in [EnvironmentState.ERROR, EnvironmentState.UNHEALTHY]:
                return False
            await asyncio.sleep(1)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取环境状态信息"""
        return {
            "env_id": self.env_id,
            "env_type": self.env_type.value,
            "state": self.state.value,
            "active_tests": self._active_tests,
            "health_status": self._last_health_result.status.value if self._last_health_result else "unknown",
            "config": {
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count,
                "health_check_interval": self.config.health_check_interval
            }
        }

#### 1.3.2 QEMU适配器实现规范

QEMU环境适配器实现了TestEnvironment基类，提供对QEMU虚拟化环境的完整支持，包括镜像管理、启动参数配置、日志采集和性能监控。

**QEMU环境配置模型**：
```python
@dataclass
class QEMUConfig:
    """QEMU配置数据模型"""
    qemu_binary: str = "qemu-system-x86_64"
    machine_type: str = "pc"
    cpu_model: str = "host"
    memory_size: str = "4G"
    
    # 镜像配置
    disk_image: str = None
    disk_format: str = "qcow2"
    snapshot_mode: bool = True
    
    # 网络配置
    network_mode: str = "user"  # user, tap, bridge
    host_forward_ports: List[Dict[str, int]] = None
    
    # 启动配置
    boot_command: str = None
    kernel_image: str = None
    initrd_image: str = None
    
    # 监控接口
    monitor_port: int = 4444
    qmp_socket: str = None  # QMP (QEMU Monitor Protocol)
    
    # 日志配置
    qemu_log_file: str = None
    serial_log_file: str = None

class QEMUEnvironment(TestEnvironment):
    """QEMU环境适配器"""
    
    def __init__(self, config: EnvironmentConfig, qemu_config: QEMUConfig):
        super().__init__(config)
        self.qemu_config = qemu_config
        self.qemu_process: Optional[asyncio.subprocess.Process] = None
        self.qmp_connection: Optional[QMPClient] = None
        self._snapshot_restored = False
        
    async def _setup_internal(self) -> bool:
        """QEMU环境准备"""
        # 1. 验证QEMU二进制文件存在
        if not await self._validate_qemu_binary():
            return False
        
        # 2. 验证镜像文件
        if not await self._validate_disk_image():
            return False
        
        # 3. 初始化QMP客户端
        if self.qemu_config.qmp_socket:
            self.qmp_connection = QMPClient(self.qemu_config.qmp_socket)
        
        # 4. 配置日志收集
        await self._setup_log_collection()
        
        return True
    
    async def _validate_qemu_binary(self) -> bool:
        """验证QEMU二进制文件"""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.qemu_config.qemu_binary, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            await self.log_collector.collect_log("setup", f"QEMU binary validation failed: {e}", "ERROR")
            return False
    
    async def _validate_disk_image(self) -> bool:
        """验证磁盘镜像文件"""
        import os
        if not os.path.exists(self.qemu_config.disk_image):
            await self.log_collector.collect_log("setup", f"Disk image not found: {self.qemu_config.disk_image}", "ERROR")
            return False
        
        # 验证镜像格式
        try:
            proc = await asyncio.create_subprocess_exec(
                "qemu-img", "info", self.qemu_config.disk_image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            await self.log_collector.collect_log("setup", f"Disk image validation failed: {e}", "ERROR")
            return False
    
    def _build_qemu_command(self) -> List[str]:
        """构建QEMU启动命令"""
        cmd = [self.qemu_config.qemu_binary]
        
        # 基础配置
        cmd.extend(["-machine", self.qemu_config.machine_type])
        cmd.extend(["-cpu", self.qemu_config.cpu_model])
        cmd.extend(["-m", self.qemu_config.memory_size])
        
        # 磁盘配置
        cmd.extend([
            "-drive", 
            f"file={self.qemu_config.disk_image},format={self.qemu_config.disk_format}"
        ])
        
        # 快照模式
        if self.qemu_config.snapshot_mode:
            cmd.append("-snapshot")
        
        # 网络配置
        if self.qemu_config.network_mode == "user":
            cmd.extend(["-net", "user", "-net", "nic"])
            # 端口转发
            for forward in (self.qemu_config.host_forward_ports or []):
                cmd.extend(["-net", f"user,hostfwd=tcp::{forward['host_port']}-:{forward['guest_port']}"])
        
        # 串口日志
        if self.qemu_config.serial_log_file:
            cmd.extend(["-serial", f"file:{self.qemu_config.serial_log_file}"])
        
        # QMP监控
        if self.qemu_config.qmp_socket:
            cmd.extend(["-qmp", f"unix:{self.qemu_config.qmp_socket},server,nowait"])
        
        # 启动配置
        if self.qemu_config.kernel_image:
            cmd.extend(["-kernel", self.qemu_config.kernel_image])
        if self.qemu_config.initrd_image:
            cmd.extend(["-initrd", self.qemu_config.initrd_image])
        if self.qemu_config.boot_command:
            cmd.extend(["-append", self.qemu_config.boot_command])
        
        # 日志输出
        if self.qemu_config.qemu_log_file:
            cmd.extend(["-D", self.qemu_config.qemu_log_file])
        
        return cmd
    
    async def _setup_log_collection(self):
        """配置日志收集"""
        log_sources = []
        
        if self.qemu_config.qemu_log_file:
            log_sources.append(LogSource(
                name="qemu_main",
                path=self.qemu_config.qemu_log_file,
                type="file"
            ))
        
        if self.qemu_config.serial_log_file:
            log_sources.append(LogSource(
                name="serial_console",
                path=self.qemu_config.serial_log_file,
                type="file"
            ))
        
        if self.qemu_config.qmp_socket:
            log_sources.append(LogSource(
                name="qmp_events",
                path=self.qemu_config.qmp_socket,
                type="network"
            ))
        
        await self.log_collector.register_sources(log_sources)
    
    async def _start_internal(self) -> bool:
        """启动QEMU环境"""
        cmd = self._build_qemu_command()
        
        # 确保日志目录存在
        import os
        for log_file in [self.qemu_config.qemu_log_file, self.qemu_config.serial_log_file]:
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        try:
            # 启动QEMU进程
            self.qemu_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await self.log_collector.collect_log("start", f"QEMU started with PID: {self.qemu_process.pid}", "INFO")
            
            # 连接QMP
            if self.qmp_connection:
                await asyncio.sleep(2)  # 等待QMP启动
                await self.qmp_connection.connect()
            
            # 等待系统启动
            await asyncio.sleep(10)  # 基础等待时间
            return True
            
        except Exception as e:
            await self.log_collector.collect_log("start", f"Failed to start QEMU: {e}", "ERROR")
            return False
    
    async def _execute_test_internal(self, test_case: TestCase) -> TestResult:
        """在QEMU中执行测试"""
        import time
        start_time = time.time()
        
        # 通过SSH或串口执行测试（示例使用SSH）
        try:
            # 这里应实现SSH连接和执行逻辑
            # 为简化示例，使用直接命令执行
            proc = await asyncio.create_subprocess_shell(
                test_case.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=test_case.environment_vars
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=test_case.timeout
            )
            
            execution_time = time.time() - start_time
            
            # 收集输出作为artifact
            output_file = f"/tmp/test_output_{test_case.case_id}.log"
            with open(output_file, 'w') as f:
                f.write(stdout.decode() + "\\n" + stderr.decode())
            
            status = TestStatus.PASSED if proc.returncode == 0 else TestStatus.FAILED
            
            return TestResult(
                result_id=f"qemu_{test_case.case_id}_{int(start_time)}",
                case_id=test_case.case_id,
                status=status,
                exit_code=proc.returncode,
                output=stdout.decode(),
                error_output=stderr.decode(),
                execution_time=execution_time,
                artifacts=[output_file]
            )
            
        except asyncio.TimeoutError:
            if proc:
                proc.kill()
            return TestResult(
                result_id=f"qemu_{test_case.case_id}_timeout",
                case_id=test_case.case_id,
                status=TestStatus.FAILED,
                exit_code=-1,
                output="",
                error_output=f"Test timeout after {test_case.timeout}s",
                execution_time=test_case.timeout,
                artifacts=[]
            )
    
    async def _cleanup_internal(self) -> bool:
        """清理QEMU环境"""
        try:
            # 通过QMP发送关机命令
            if self.qmp_connection:
                await self.qmp_connection.send_powerdown()
                await asyncio.sleep(5)
            
            # 强制终止进程
            if self.qemu_process:
                self.qemu_process.terminate()
                await asyncio.wait_for(self.qemu_process.wait(), timeout=30)
            
            # 清理日志收集
            await self.log_collector.cleanup()
            
            return True
        except Exception as e:
            await self.log_collector.collect_log("cleanup", f"Cleanup failed: {e}", "ERROR")
            return False
    
    async def _perform_health_checks(self) -> HealthCheckResult:
        """执行QEMU健康检查"""
        checks = {}
        metrics = {}
        
        # 检查1: 进程状态
        if self.qemu_process:
            checks["qemu_process_running"] = self.qemu_process.returncode is None
        else:
            checks["qemu_process_running"] = False
        
        # 检查2: QMP连接状态
        if self.qmp_connection:
            checks["qmp_connection"] = await self.qmp_connection.ping()
        
        # 检查3: 系统响应（通过SSH或串口）
        try:
            # 示例：尝试简单命令
            proc = await asyncio.create_subprocess_exec(
                "echo", "ping",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
            checks["system_responsive"] = proc.returncode == 0
        except:
            checks["system_responsive"] = False
        
        # 检查4: 资源使用（通过QMP获取）
        if self.qmp_connection and checks["qmp_connection"]:
            metrics.update(await self.qmp_connection.get_system_metrics())
        
        # 判断整体状态
        failed_checks = [k for k, v in checks.items() if not v]
        if not any(checks.values()):
            status = HealthStatus.FAILED
            message = "All health checks failed"
        elif failed_checks:
            status = HealthStatus.DEGRADED
            message = f"Failed checks: {', '.join(failed_checks)}"
        else:
            status = HealthStatus.HEALTHY
            message = "All systems healthy"
        
        return HealthCheckResult(
            status=status,
            checks=checks,
            metrics=metrics,
            message=message
        )

#### 1.3.3 目标板适配器实现规范

目标板环境适配器支持通过多种接入方式（SSH、BMC、串口）对真实硬件进行测试编排，提供与QEMU一致的统一接口。

**目标板接入方式枚举**：
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class BoardAccessType(Enum):
    """目标板接入方式"""
    SSH = "ssh"
    BMC = "bmc"
    SERIAL = "serial"
    TELNET = "telnet"

@dataclass
class BoardConfig:
    """目标板配置数据模型"""
    board_id: str
    board_model: str
    access_type: BoardAccessType
    
    # 通用配置
    power_control: bool = True  # 是否支持电源控制
    boot_timeout: int = 300    # 启动超时时间
    
    # 资源约束
    max_concurrent_tests: int = 1
    exclusive_resources: List[str] = None

@dataclass
class SSHConfig:
    """SSH接入配置"""
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    timeout: int = 30
    keepalive_interval: int = 60

@dataclass
class BMCConfig:
    """BMC接入配置"""
    bmc_ip: str
    bmc_username: str
    bmc_password: str
    bmc_type: str = "ipmi"  # ipmi, redfish, ssh
    power_on_command: Optional[str] = None
    power_off_command: Optional[str] = None
    reset_command: Optional[str] = None

@dataclass
class SerialConfig:
    """串口接入配置"""
    device_path: str  # /dev/ttyUSB0
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    flow_control: bool = False
    timeout: int = 10

class BoardEnvironment(TestEnvironment):
    """目标板环境适配器 - 支持多种接入方式"""
    
    def __init__(self, config: EnvironmentConfig, board_config: BoardConfig):
        super().__init__(config)
        self.board_config = board_config
        self.ssh_config: Optional[SSHConfig] = None
        self.bmc_config: Optional[BMCConfig] = None
        self.serial_config: Optional[SerialConfig] = None
        self.ssh_client: Optional[SSHClient] = None
        self.bmc_client: Optional[BMCClient] = None
        self.serial_connection: Optional[SerialConnection] = None
        self._access_client = None
        
    def set_access_config(self, access_type: BoardAccessType, config: Any):
        """设置接入配置"""
        if access_type == BoardAccessType.SSH:
            self.ssh_config = config
        elif access_type == BoardAccessType.BMC:
            self.bmc_config = config
        elif access_type == BoardAccessType.SERIAL:
            self.serial_config = config
        else:
            raise ValueError(f"Unsupported access type: {access_type}")
    
    async def _setup_internal(self) -> bool:
        """目标板环境准备"""
        # 1. 根据接入类型初始化客户端
        if self.board_config.access_type == BoardAccessType.SSH:
            if not self.ssh_config:
                raise ValueError("SSH config not provided")
            self._access_client = SSHClient(self.ssh_config)
            
        elif self.board_config.access_type == BoardAccessType.BMC:
            if not self.bmc_config:
                raise ValueError("BMC config not provided")
            self._access_client = BMCClient(self.bmc_config)
            
        elif self.board_config.access_type == BoardAccessType.SERIAL:
            if not self.serial_config:
                raise ValueError("Serial config not provided")
            self._access_client = SerialConnection(self.serial_config)
        
        # 2. 配置日志收集
        await self._setup_board_log_collection()
        
        return True
    
    async def _setup_board_log_collection(self):
        """配置目标板日志收集"""
        log_sources = []
        
        # 系统日志（通过接入方式收集）
        if self.board_config.access_type == BoardAccessType.SSH:
            log_sources.append(LogSource(
                name="syslog",
                path="/var/log/syslog",
                type="remote_file",
                format="text"
            ))
        elif self.board_config.access_type == BoardAccessType.SERIAL:
            log_sources.append(LogSource(
                name="serial_console",
                path=self.serial_config.device_path,
                type="serial",
                format="text"
            ))
        
        # BMC事件日志
        if self.board_config.access_type == BoardAccessType.BMC:
            log_sources.append(LogSource(
                name="bmc_events",
                path=f"{self.bmc_config.bmc_ip}/events",
                type="network",
                format="json"
            ))
        
        await self.log_collector.register_sources(log_sources)
    
    async def _start_internal(self) -> bool:
        """启动目标板环境"""
        try:
            # 1. 电源控制（如果支持）
            if self.board_config.power_control:
                await self._power_cycle_board()
            
            # 2. 等待系统启动
            await self._wait_for_system_boot()
            
            # 3. 建立接入连接
            if self._access_client:
                await self._access_client.connect()
                await self.log_collector.collect_log("start", "Board access client connected", "INFO")
            
            return True
            
        except Exception as e:
            await self.log_collector.collect_log("start", f"Board start failed: {e}", "ERROR")
            return False
    
    async def _power_cycle_board(self):
        """电源循环目标板"""
        if isinstance(self._access_client, BMCClient):
            # 通过BMC控制电源
            await self._access_client.power_off()
            await asyncio.sleep(5)
            await self._access_client.power_on()
        else:
            # TODO: 实现其他方式的电源控制
            pass
    
    async def _wait_for_system_boot(self):
        """等待系统启动完成"""
        boot_timeout = self.board_config.boot_timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < boot_timeout:
            try:
                if isinstance(self._access_client, SSHClient):
                    # 尝试SSH连接
                    result = await self._access_client.execute_command("uptime")
                    if result.returncode == 0:
                        await self.log_collector.collect_log("boot", "System boot completed", "INFO")
                        return
                elif isinstance(self._access_client, SerialConnection):
                    # 检查启动完成标志
                    if await self._access_client.wait_for_pattern("login:", timeout=10):
                        await self.log_collector.collect_log("boot", "System boot completed", "INFO")
                        return
            except:
                pass
            
            await asyncio.sleep(5)
        
        raise TimeoutError("Board boot timeout")
    
    async def _execute_test_internal(self, test_case: TestCase) -> TestResult:
        """在目标板执行测试"""
        import time
        start_time = time.time()
        
        try:
            if not self._access_client:
                raise RuntimeError("Access client not available")
            
            # 根据接入方式执行测试
            if isinstance(self._access_client, SSHClient):
                result = await self._execute_ssh_test(test_case)
            elif isinstance(self._access_client, BMCClient):
                result = await self._execute_bmc_test(test_case)
            elif isinstance(self._access_client, SerialConnection):
                result = await self._execute_serial_test(test_case)
            else:
                raise RuntimeError("Unsupported access client")
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            await self.log_collector.collect_log("test", f"Test execution failed: {e}", "ERROR")
            return TestResult(
                result_id=f"board_{test_case.case_id}_error",
                case_id=test_case.case_id,
                status=TestStatus.FAILED,
                exit_code=-1,
                output="",
                error_output=str(e),
                execution_time=0.0,
                artifacts=[]
            )
    
    async def _execute_ssh_test(self, test_case: TestCase) -> TestResult:
        """通过SSH执行测试"""
        result = await self._access_client.execute_command(
            test_case.command,
            timeout=test_case.timeout,
            environment=test_case.environment_vars
        )
        
        return TestResult(
            result_id=f"ssh_{test_case.case_id}_{int(asyncio.get_event_loop().time())}",
            case_id=test_case.case_id,
            status=TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED,
            exit_code=result.returncode,
            output=result.stdout,
            error_output=result.stderr,
            execution_time=0.0,
            artifacts=[result.log_file] if result.log_file else []
        )
    
    async def _execute_serial_test(self, test_case: TestCase) -> TestResult:
        """通过串口执行测试"""
        # 发送测试命令
        await self._access_client.send_command(test_case.command)
        
        # 收集输出
        output = await self._access_client.read_until_timeout(test_case.timeout)
        
        # 解析结果（假设输出包含退出码）
        exit_code = self._parse_exit_code(output)
        
        return TestResult(
            result_id=f"serial_{test_case.case_id}_{int(asyncio.get_event_loop().time())}",
            case_id=test_case.case_id,
            status=TestStatus.PASSED if exit_code == 0 else TestStatus.FAILED,
            exit_code=exit_code,
            output=output,
            error_output="",
            execution_time=0.0,
            artifacts=[]
        )
    
    async def _execute_bmc_test(self, test_case: TestCase) -> TestResult:
        """通过BMC执行测试"""
        # BMC环境下通常使用SOL(Serial-over-LAN)
        sol_output = await self._access_client.execute_sol_command(
            test_case.command,
            timeout=test_case.timeout
        )
        
        exit_code = self._parse_exit_code(sol_output)
        
        return TestResult(
            result_id=f"bmc_{test_case.case_id}_{int(asyncio.get_event_loop().time())}",
            case_id=test_case.case_id,
            status=TestStatus.PASSED if exit_code == 0 else TestStatus.FAILED,
            exit_code=exit_code,
            output=sol_output,
            error_output="",
            execution_time=0.0,
            artifacts=[]
        )
    
    def _parse_exit_code(self, output: str) -> int:
        """从输出中解析退出码"""
        # 实际实现中应解析命令执行的退出码
        # 这里简化处理
        import re
        match = re.search(r"EXIT_CODE:(\\d+)", output)
        if match:
            return int(match.group(1))
        return -1
    
    async def _cleanup_internal(self) -> bool:
        """清理目标板环境"""
        try:
            if self._access_client:
                await self._access_client.disconnect()
            
            await self.log_collector.cleanup()
            return True
        except Exception as e:
            await self.log_collector.collect_log("cleanup", f"Cleanup failed: {e}", "ERROR")
            return False
    
    async def _perform_health_checks(self) -> HealthCheckResult:
        """执行目标板健康检查"""
        checks = {}
        metrics = {}
        
        try:
            if isinstance(self._access_client, SSHClient):
                # 检查系统负载
                result = await self._access_client.execute_command("uptime")
                checks["system_load"] = result.returncode == 0
                
                # 检查磁盘空间
                result = await self._access_client.execute_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
                if result.returncode == 0:
                    disk_usage = int(result.stdout.strip())
                    checks["disk_space"] = disk_usage < 90
                    metrics["disk_usage_percent"] = disk_usage
                
                # 检查内存使用
                result = await self._access_client.execute_command("free | grep Mem | awk '{print $4/$2 * 100.0}'")
                if result.returncode == 0:
                    memory_available = float(result.stdout.strip())
                    checks["memory_available"] = memory_available > 10
                    metrics["memory_available_percent"] = memory_available
                
                # 检查SSH连接
                checks["ssh_connection"] = self._access_client.is_connected()
                
            elif isinstance(self._access_client, BMCClient):
                # 检查BMC连接
                checks["bmc_connection"] = await self._access_client.ping()
                
                # 检查电源状态
                power_state = await self._access_client.get_power_state()
                checks["power_state"] = power_state == "on"
                metrics["power_state"] = 1 if power_state == "on" else 0
                
                # 检查传感器
                sensors = await self._access_client.get_sensor_data()
                checks["temperature"] = all(s["value"] < s.get("critical", 80) for s in sensors if s["type"] == "temperature")
                metrics.update({s["name"]: s["value"] for s in sensors})
                
            elif isinstance(self._access_client, SerialConnection):
                # 检查串口连接
                checks["serial_connection"] = self._access_client.is_connected()
                
                # 测试简单命令
                await self._access_client.send_command("echo health_check")
                response = await self._access_client.read_until_timeout(10)
                checks["system_responsive"] = "health_check" in response
        
        except Exception as e:
            await self.log_collector.collect_log("health_check", f"Health check error: {e}", "ERROR")
            checks["health_check_error"] = False
        
        # 评估结果
        failed_checks = [k for k, v in checks.items() if not v]
        if not any(checks.values()):
            status = HealthStatus.FAILED
            message = "Board not responding"
        elif failed_checks:
            status = HealthStatus.DEGRADED
            message = f"Degraded: {', '.join(failed_checks)}"
        else:
            status = HealthStatus.HEALTHY
            message = "Board healthy"
        
        return HealthCheckResult(
            status=status,
            checks=checks,
            metrics=metrics,
            message=message
        )

#### 1.3.4 统一日志收集接口设计

统一日志收集接口LogCollector为不同环境（QEMU、目标板、BMC）提供标准化的日志采集、存储和分析能力，支持多种日志源和格式。

**LogCollector核心设计**：
```python
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import os

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogFormat(Enum):
    """日志格式枚举"""
    PLAIN_TEXT = "plain_text"
    STRUCTURED_JSON = "structured_json"
    SYSLOG = "syslog"
    KERNEL_RING = "kernel_ring"
    BINARY = "binary"

@dataclass
class LogEntry:
    """标准化日志条目"""
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    env_id: Optional[str] = None
    test_case_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "source": self.source,
            "message": self.message,
            "metadata": self.metadata,
            "env_id": self.env_id,
            "test_case_id": self.test_case_id
        }

@dataclass
class LogStream:
    """日志流定义"""
    source: str
    log_type: str  # stdout, stderr, file, network, serial
    format: LogFormat
    parser: Optional[Callable[[str], LogEntry]] = None
    enabled: bool = True
    buffer_size: int = 4096
    
class LogCollector:
    """统一日志收集器 - 标准化日志采集接口"""
    
    def __init__(self, env_config: EnvironmentConfig):
        self.env_config = env_config
        self.log_streams: Dict[str, LogStream] = {}
        self.log_caches: Dict[str, List[LogEntry]] = {}
        self.output_dir = f"/tmp/logs/{env_config.env_id}"
        self._collection_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._running = False
        
        # 创建日志输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def register_sources(self, sources: List[LogSource]) -> List[str]:
        """
        注册日志源
        返回: 注册的源ID列表
        """
        registered_ids = []
        
        for source in sources:
            source_id = f"{source.name}_{len(self.log_streams)}"
            
            # 创建日志流
            log_format = self._detect_format(source.format, source.path)
            log_stream = LogStream(
                source=source.path,
                log_type=source.type,
                format=log_format,
                parser=self._get_parser(log_format, source.type)
            )
            
            self.log_streams[source_id] = log_stream
            self.log_caches[source_id] = []
            registered_ids.append(source_id)
            
            await self.collect_log("setup", f"Registered log source: {source_id}", "INFO")
        
        return registered_ids
    
    def _detect_format(self, format_hint: str, path: str) -> LogFormat:
        """检测日志格式"""
        if format_hint == "json":
            return LogFormat.STRUCTURED_JSON
        elif format_hint == "binary":
            return LogFormat.BINARY
        elif path.startswith("/dev/") or "tty" in path:
            return LogFormat.KERNEL_RING
        else:
            return LogFormat.PLAIN_TEXT
    
    def _get_parser(self, log_format: LogFormat, log_type: str) -> Callable[[str], LogEntry]:
        """获取日志解析器"""
        if log_format == LogFormat.STRUCTURED_JSON:
            return self._parse_json_log
        elif log_format == LogFormat.SYSLOG:
            return self._parse_syslog
        else:
            return lambda x, t=log_type: self._parse_plain_text(x, t)
    
    def _parse_json_log(self, line: str) -> LogEntry:
        """解析JSON格式日志"""
        try:
            data = json.loads(line)
            return LogEntry(
                timestamp=datetime.fromisoformat(data.get("timestamp")),
                level=LogLevel(data.get("level", "INFO")),
                source=data.get("source", "unknown"),
                message=data.get("message", ""),
                metadata=data.get("metadata", {}),
                env_id=self.env_config.env_id
            )
        except:
            return self._parse_plain_text(line, "json_fallback")
    
    def _parse_syslog(self, line: str) -> LogEntry:
        """解析syslog格式"""
        # 简化实现，实际应解析完整的syslog格式
        import re
        pattern = r'(\\w+\\s+\\d+\\s+\\d+:\\d+:\\d+)\\s+(\\S+)\\s+(\\w+):\\s+(.*)'
        match = re.match(pattern, line)
        
        if match:
            return LogEntry(
                timestamp=datetime.now(),  # 应解析真实时间
                level=LogLevel.INFO,  # 应从日志级别解析
                source=match.group(2),
                message=match.group(4),
                metadata={},
                env_id=self.env_config.env_id
            )
        else:
            return self._parse_plain_text(line, "syslog")
    
    def _parse_plain_text(self, line: str, source_type: str) -> LogEntry:
        """解析普通文本日志"""
        # 检测日志级别
        level = LogLevel.INFO
        upper_line = line.upper()
        if "ERROR" in upper_line:
            level = LogLevel.ERROR
        elif "WARN" in upper_line:
            level = LogLevel.WARNING
        elif "DEBUG" in upper_line:
            level = LogLevel.DEBUG
        
        return LogEntry(
            timestamp=datetime.now(),
            level=level,
            source=source_type,
            message=line.strip(),
            metadata={},
            env_id=self.env_config.env_id
        )
    
    async def start_collection(self):
        """启动日志收集"""
        if self._running:
            return
        
        self._running = True
        for source_id, log_stream in self.log_streams.items():
            if log_stream.enabled:
                task = asyncio.create_task(self._collect_from_source(source_id, log_stream))
                self._collection_tasks[source_id] = task
    
    async def stop_collection(self):
        """停止日志收集"""
        self._running = False
        for task in self._collection_tasks.values():
            task.cancel()
        
        if self._collection_tasks:
            await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)
        
        self._collection_tasks.clear()
    
    async def _collect_from_source(self, source_id: str, log_stream: LogStream):
        """从指定源收集日志"""
        while self._running:
            try:
                if log_stream.log_type == "file":
                    await self._tail_file(source_id, log_stream)
                elif log_stream.log_type == "stdout":
                    await self._read_stdout(source_id, log_stream)
                elif log_stream.log_type == "network":
                    await self._read_network(source_id, log_stream)
                elif log_stream.log_type == "serial":
                    await self._read_serial(source_id, log_stream)
                else:
                    await asyncio.sleep(1)  # 未知类型，等待
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.collect_log("collection", f"Error collecting from {source_id}: {e}", "ERROR")
                await asyncio.sleep(5)  # 出错后等待重试
    
    async def _tail_file(self, source_id: str, log_stream: LogStream):
        """跟踪文件日志"""
        import aiofiles
        
        if not os.path.exists(log_stream.source):
            await asyncio.sleep(2)  # 等待文件创建
            return
        
        async with aiofiles.open(log_stream.source, 'r') as f:
            # 移动到文件末尾
            await f.seek(0, os.SEEK_END)
            
            while self._running:
                line = await f.readline()
                if line:
                    entry = log_stream.parser(line)
                    await self._store_log_entry(source_id, entry)
                else:
                    await asyncio.sleep(0.5)
    
    async def _read_stdout(self, source_id: str, log_stream: LogStream):
        """读取标准输出"""
        # 实际实现应从进程stdout读取
        await asyncio.sleep(1)
    
    async def _read_network(self, source_id: str, log_stream: LogStream):
        """读取网络日志"""
        # 实际实现应连接网络套接字
        await asyncio.sleep(1)
    
    async def _read_serial(self, source_id: str, log_stream: LogStream):
        """读取串口日志"""
        # 实际实现应使用pyserial等库
        await asyncio.sleep(1)
    
    async def _store_log_entry(self, source_id: str, entry: LogEntry):
        """存储日志条目"""
        async with self._lock:
            self.log_caches[source_id].append(entry)
            
            # 限制缓存大小
            if len(self.log_caches[source_id]) > 10000:
                self.log_caches[source_id] = self.log_caches[source_id][-5000:]
        
        # 写入文件（异步）
        await self._write_log_to_file(entry)
    
    async def _write_log_to_file(self, entry: LogEntry):
        """写入日志到文件"""
        log_file = f"{self.output_dir}/logs.jsonl"
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(entry.to_dict()) + "\\n")
    
    async def collect_log(self, source: str, message: str, level: str = "INFO", 
                         metadata: Dict[str, Any] = None, test_case_id: str = None):
        """
        手动收集单条日志
        用于系统自身的事件记录
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel(level),
            source=source,
            message=message,
            metadata=metadata or {},
            env_id=self.env_config.env_id,
            test_case_id=test_case_id
        )
        
        if "default" not in self.log_caches:
            self.log_caches["default"] = []
        
        await self._store_log_entry("default", entry)
    
    def get_logs(self, source_id: str = None, level: LogLevel = None, 
                 start_time: datetime = None, end_time: datetime = None) -> List[LogEntry]:
        """
        查询日志
        支持按源、级别、时间范围过滤
        """
        results = []
        
        sources_to_check = [source_id] if source_id else list(self.log_caches.keys())
        
        for src_id in sources_to_check:
            if src_id not in self.log_caches:
                continue
            
            for entry in self.log_caches[src_id]:
                if level and entry.level != level:
                    continue
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                
                results.append(entry)
        
        return sorted(results, key=lambda x: x.timestamp)
    
    async def get_logs_async(self, **kwargs) -> List[LogEntry]:
        """异步获取日志"""
        return await asyncio.get_event_loop().run_in_executor(None, self.get_logs, **kwargs)
    
    async def cleanup(self):
        """清理日志收集器"""
        await self.stop_collection()
        
        # 清理缓存
        self.log_caches.clear()
        self.log_streams.clear()

class MetricsCollector:
    """指标收集器 - 与环境指标集成"""
    
    def __init__(self, env_config: EnvironmentConfig):
        self.env_config = env_config
        self.metrics = {}
        self._sampling_task = None
        self._running = False
    
    async def start_sampling(self, interval: int = 30):
        """启动指标采样"""
        if self._running:
            return
        
        self._running = True
        self._sampling_task = asyncio.create_task(self._sample_loop(interval))
    
    async def stop_sampling(self):
        """停止指标采样"""
        self._running = False
        if self._sampling_task:
            self._sampling_task.cancel()
            try:
                await self._sampling_task
            except asyncio.CancelledError:
                pass
    
    async def _sample_loop(self, interval: int):
        """采样循环"""
        while self._running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但不停止采样
                print(f"Metrics sampling error: {e}")
                await asyncio.sleep(interval)
    
    async def collect_system_metrics(self):
        """收集系统指标"""
        # 实际实现应收集CPU、内存、磁盘等指标
        pass
    
    def get_metric(self, name: str, default: Any = None) -> Any:
        """获取指标值"""
        return self.metrics.get(name, default)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return self.metrics.copy()

class QMPClient:
    """QEMU Monitor Protocol客户端"""
    
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self._reader = None
        self._writer = None
        self._command_id = 0
    
    async def connect(self):
        """连接QMP"""
        import json
        self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
        
        # 读取QMP欢迎消息
        welcome = await self._reader.readline()
        # 读取 capabilities
        capabilities = await self._reader.readline()
    
    async def disconnect(self):
        """断开QMP连接"""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """发送QMP命令"""
        import json
        self._command_id += 1
        command["id"] = self._command_id
        
        self._writer.write(json.dumps(command).encode() + b"\\n")
        await self._writer.drain()
        
        response = await self._reader.readline()
        return json.loads(response.decode())
    
    async def ping(self) -> bool:
        """测试QMP连接"""
        try:
            response = await self.send_command({"execute": "query-status"})
            return response.get("return") is not None
        except:
            return False
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        metrics = {}
        
        try:
            # 查询内存信息
            response = await self.send_command({"execute": "query-memory-size-summary"})
            if response.get("return"):
                metrics["memory_total"] = response["return"].get("base-memory")
            
            # 查询CPU信息
            response = await self.send_command({"execute": "query-cpus"})
            if response.get("return"):
                metrics["cpu_count"] = len(response["return"])
                
        except:
            pass
        
        return metrics
    
    async def send_powerdown(self):
        """发送关机命令"""
        await self.send_command({"execute": "system_powerdown"})

class SSHClient:
    """SSH客户端"""
    
    def __init__(self, config: SSHConfig):
        self.config = config
        self.client = None
        self.connected = False
    
    async def connect(self):
        """连接SSH"""
        import asyncssh
        
        connect_kwargs = {
            "host": self.config.host,
            "port": self.config.port,
            "username": self.config.username,
            "known_hosts": None,
            "connect_timeout": self.config.timeout
        }
        
        if self.config.private_key:
            connect_kwargs["client_keys"] = [self.config.private_key]
        elif self.config.password:
            connect_kwargs["password"] = self.config.password
        
        self.client = await asyncssh.connect(**connect_kwargs)
        self.connected = True
    
    async def disconnect(self):
        """断开SSH连接"""
        if self.client:
            self.client.close()
            await self.client.wait_closed()
            self.connected = False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected and self.client is not None
    
    async def execute_command(self, command: str, timeout: int = None, 
                              environment: Dict[str, str] = None) -> 'SSHResult':
        """执行命令"""
        if not self.connected:
            raise RuntimeError("Not connected")
        
        result = await self.client.run(
            command,
            timeout=timeout or self.config.timeout,
            env=environment
        )
        
        return SSHResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            log_file=None
        )

@dataclass
class SSHResult:
    """SSH执行结果"""
    returncode: int
    stdout: str
    stderr: str
    log_file: Optional[str]

class BMCClient:
    """BMC客户端"""
    
    def __init__(self, config: BMCConfig):
        self.config = config
        self.connection = None
    
    async def connect(self):
        """连接BMC"""
        # 实际实现应使用IPMI或Redfish库
        pass
    
    async def disconnect(self):
        """断开BMC连接"""
        pass
    
    async def ping(self) -> bool:
        """测试BMC连接"""
        # 实际实现
        return True
    
    async def power_on(self):
        """开机"""
        pass
    
    async def power_off(self):
        """关机"""
        pass
    
    async def get_power_state(self) -> str:
        """获取电源状态"""
        return "on"
    
    async def get_sensor_data(self) -> List[Dict[str, Any]]:
        """获取传感器数据"""
        return []
    
    async def execute_sol_command(self, command: str, timeout: int = 300) -> str:
        """通过SOL执行命令"""
        # Serial-over-LAN实现
        pass

class SerialConnection:
    """串口连接"""
    
    def __init__(self, config: SerialConfig):
        self.config = config
        self.serial = None
        self.connected = False
    
    async def connect(self):
        """连接串口"""
        import serial_asyncio
        
        self.serial = await serial_asyncio.open_serial_connection(
            url=self.config.device_path,
            baudrate=self.config.baudrate,
            bytesize=self.config.bytesize,
            parity=self.config.parity,
            stopbits=self.config.stopbits
        )
        self.connected = True
    
    async def disconnect(self):
        """断开串口连接"""
        if self.serial:
            self.serial.close()
            self.connected = False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    async def send_command(self, command: str):
        """发送命令"""
        if not self.connected:
            raise RuntimeError("Not connected")
        
        self.serial.write((command + "\\n").encode())
        await self.serial.drain()
    
    async def read_until_timeout(self, timeout: int) -> str:
        """读取直到超时"""
        import time
        start_time = time.time()
        result = ""
        
        while time.time() - start_time < timeout:
            data = await self.serial.read(1024)
            if data:
                result += data.decode('utf-8', errors='ignore')
            await asyncio.sleep(0.1)
        
        return result
    
    async def wait_for_pattern(self, pattern: str, timeout: int = 30) -> bool:
        """等待特定模式出现"""
        import time
        start_time = time.time()
        buffer = ""
        
        while time.time() - start_time < timeout:
            data = await self.serial.read(1024)
            if data:
                buffer += data.decode('utf-8', errors='ignore')
                if pattern in buffer:
                    return True
            await asyncio.sleep(0.1)
        
        return False

#### 1.3.5 健康检查与故障恢复流程

基于TestEnvironment基类和LogCollector的统一设计，健康检查和故障恢复流程确保测试环境的稳定性和可靠性，支持自动检测、预警和恢复机制。

**健康检查架构**：
```python
class HealthChecker:
    """健康检查管理器"""
    
    def __init__(self, check_interval: int = 30, max_failures: int = 3):
        self.check_interval = check_interval
        self.max_failures = max_failures
        self.environments: Dict[str, TestEnvironment] = {}
        self.failure_counts: Dict[str, int] = {}
        self.alert_callbacks: List[Callable] = []
        self._running = False
        self._check_task = None
    
    def register_environment(self, env: TestEnvironment):
        """注册环境到健康检查"""
        self.environments[env.env_id] = env
        self.failure_counts[env.env_id] = 0
    
    def register_alert_callback(self, callback: Callable[[str, HealthCheckResult], None]):
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    async def start(self):
        """启动健康检查服务"""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._check_loop())
    
    async def stop(self):
        """停止健康检查服务"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
    
    async def _check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._perform_all_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_all_checks(self):
        """执行所有环境健康检查"""
        for env_id, env in self.environments.items():
            try:
                health_result = await env.health_check()
                
                # 处理检查结果
                if health_result.status == HealthStatus.HEALTHY:
                    self.failure_counts[env_id] = 0
                elif health_result.status in [HealthStatus.DEGRADED, HealthStatus.FAILED]:
                    self.failure_counts[env_id] += 1
                    
                    # 触发告警
                    await self._trigger_alerts(env_id, health_result)
                    
                    # 检查是否需要故障恢复
                    if self.failure_counts[env_id] >= self.max_failures:
                        await self._trigger_recovery(env_id, health_result)
                
            except Exception as e:
                print(f"Error checking environment {env_id}: {e}")
                self.failure_counts[env_id] += 1
    
    async def _trigger_alerts(self, env_id: str, health_result: HealthCheckResult):
        """触发告警"""
        for callback in self.alert_callbacks:
            try:
                await callback(env_id, health_result)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    async def _trigger_recovery(self, env_id: str, health_result: HealthCheckResult):
        """触发故障恢复"""
        env = self.environments.get(env_id)
        if not env:
            return
        
        # 尝试自动恢复
        failure_info = {
            "health_result": health_result,
            "failure_count": self.failure_counts[env_id],
            "last_check": datetime.now().isoformat()
        }
        
        recovery_success = await env.recover_from_failure(failure_info)
        
        if recovery_success:
            # 恢复成功，重置失败计数
            self.failure_counts[env_id] = 0
        else:
            # 恢复失败，通知管理员
            await self._notify_administrators(env_id, health_result, recovery_success)
    
    async def _notify_administrators(self, env_id: str, health_result: HealthCheckResult, 
                                    recovery_success: bool):
        """通知管理员"""
        message = f"""
        Environment Alert: {env_id}
        Health Status: {health_result.status.value}
        Message: {health_result.message}
        Recovery Attempt: {'Successful' if recovery_success else 'Failed'}
        Failed Checks: {', '.join(k for k, v in health_result.checks.items() if not v)}
        Metrics: {health_result.metrics}
        """
        
        # 实际实现应通过邮件、短信、Slack等方式通知
        print(f"ADMIN NOTIFICATION: {message}")

# 标准化故障恢复流程图
```mermaid
graph TD
    A[健康检查失败] --> B{失败次数 >= max_failures?}
    B -- 是 --> C[触发故障恢复]
    B -- 否 --> D[记录失败,继续监控]
    
    C --> E[执行 recover_from_failure()]
    E --> F{恢复结果}
    F -- 成功 --> G[重置失败计数,继续测试]
    F -- 失败 --> H[标记环境不可用]
    
    G --> I[发送恢复成功通知]
    H --> J[发送严重告警,人工介入]
    
    D --> K[更新健康状态]
```

**故障恢复策略配置**：
```python
@dataclass
class RecoveryConfig:
    """故障恢复配置"""
    max_attempts: int = 3
    attempt_delay: int = 30  # 恢复尝试间隔（秒）
    escalation_threshold: int = 2  # 升级阈值（失败次数）
    
    # 恢复策略
    strategies: List[str] = field(default_factory=lambda: ["cleanup_setup_start", "full_restart"])
    
    # 通知配置
    notify_on_degraded: bool = True
    notify_on_failure: bool = True
    notify_on_recovery: bool = True
    
    # 通知渠道
    notification_channels: List[str] = field(default_factory=lambda: ["log", "webhook"])
```

**故障恢复成功率统计**：
```python
class RecoveryMetrics:
    """故障恢复指标跟踪"""
    
    def __init__(self):
        self.total_recovery_attempts = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.recovery_durations = []
        self.failure_reasons = {}
    
    def record_recovery_attempt(self, env_id: str, start_time: float):
        """记录恢复尝试"""
        self.total_recovery_attempts += 1
        self._current_recovery_start = start_time
        self._current_recovery_env = env_id
    
    def record_recovery_result(self, success: bool, failure_reason: str = None):
        """记录恢复结果"""
        if success:
            self.successful_recoveries += 1
        else:
            self.failed_recoveries += 1
            if failure_reason:
                self.failure_reasons[failure_reason] = self.failure_reasons.get(failure_reason, 0) + 1
        
        if hasattr(self, '_current_recovery_start'):
            duration = time.time() - self._current_recovery_start
            self.recovery_durations.append(duration)
    
    def get_recovery_rate(self) -> float:
        """获取恢复成功率"""
        if self.total_recovery_attempts == 0:
            return 0.0
        return self.successful_recoveries / self.total_recovery_attempts
```

**故障恢复的持久化状态管理**：
```python
class EnvironmentStateManager:
    """环境状态管理器 - 持久化状态跟踪"""
    
    def __init__(self, state_file: str = "/tmp/env_states.json"):
        self.state_file = state_file
        self.states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        # 加载历史状态
        self._load_states()
    
    async def update_state(self, env_id: str, state: EnvironmentState, 
                          health_status: HealthStatus, metrics: Dict[str, Any]):
        """更新环境状态"""
        async with self._lock:
            self.states[env_id] = {
                "state": state.value,
                "health_status": health_status.value,
                "metrics": metrics,
                "last_update": datetime.now().isoformat(),
                "uptime": self._calculate_uptime(env_id)
            }
            
            await self._save_states()
    
    async def record_failure(self, env_id: str, failure_type: str, details: Dict[str, Any]):
        """记录失败事件"""
        async with self._lock:
            if "failure_history" not in self.states:
                self.states["failure_history"] = []
            
            self.states["failure_history"].append({
                "env_id": env_id,
                "failure_type": failure_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
            
            # 限制历史记录数量
            if len(self.states["failure_history"]) > 1000:
                self.states["failure_history"] = self.states["failure_history"][-500:]
            
            await self._save_states()
    
    def get_state(self, env_id: str) -> Optional[Dict[str, Any]]:
        """获取环境状态"""
        return self.states.get(env_id)
    
    def get_environment_stats(self) -> Dict[str, Any]:
        """获取环境统计信息"""
        total_envs = len([k for k in self.states.keys() if not k.startswith("_")])
        healthy_envs = len([
            env for env in self.states.values() 
            if isinstance(env, dict) and env.get("health_status") == "healthy"
        ])
        
        failure_history = self.states.get("failure_history", [])
        failure_rate = len(failure_history) / max(total_envs, 1)
        
        return {
            "total_environments": total_envs,
            "healthy_environments": healthy_envs,
            "overall_health_rate": healthy_envs / max(total_envs, 1),
            "total_failures": len(failure_history),
            "failure_rate": failure_rate
        }
    
    def _calculate_uptime(self, env_id: str) -> float:
        """计算环境在线时间"""
        # 实际实现应跟踪环境启动和关闭时间
        return 0.0
    
    async def _save_states(self):
        """保存状态到文件"""
        import aiofiles
        async with aiofiles.open(self.state_file, 'w') as f:
            await f.write(json.dumps(self.states, indent=2))
    
    def _load_states(self):
        """从文件加载状态"""
        try:
            with open(self.state_file, 'r') as f:
                self.states = json.load(f)
        except FileNotFoundError:
            self.states = {}
        except:
            self.states = {}

**最佳实践与推荐配置**：

1. **健康检查频率配置**:
   - 正常环境: 每30秒检查一次
   - 关键测试环境: 每10秒检查一次
   - 开发环境: 每60秒检查一次

2. **故障恢复策略优先级**:
   - Level 1: 重新连接（SSH、BMC、串口）
   - Level 2: 服务重启（QEMU重启、应用重启）
   - Level 3: 完整清理重建（cleanup -> setup -> start）
   - Level 4: 物理干预（电源循环、硬件重置）

3. **告警阈值设置**:
   - 降级状态（Degraded）: 单次检查失败
   - 失败状态（Failed）: 连续3次检查失败
   - 需要人工介入: 连续5次检查失败或恢复失败

### 1.4 ResultAnalyzer（结果分析器）

**职责定位**：智能测试结果分析和决策建议引擎

**核心功能**：
- 日志解析和错误分类
- 根因分析和归因
- 趋势分析和模式识别
- 决策建议生成
- 收敛性判断

**接口定义**：
```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    source: str
    message: str
    metadata: Dict[str, Any]

@dataclass
class ErrorPattern:
    pattern_id: str
    pattern_type: str
    description: str
    severity: str
    occurrences: List[LogEntry]
    confidence: float

@dataclass
class RootCause:
    cause_id: str
    description: str
    evidence: List[str]
    confidence: float
    suggested_actions: List[str]

@dataclass
class AnalysisDecision:
    decision_id: str
    action: str
    reasoning: str
    next_steps: List[str]
    confidence: float

class ResultAnalyzer:
    """结果分析器主接口"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_parser = self._init_log_parser()
        self.ai_model = self._init_ai_model()
        self.pattern_matcher = self._init_pattern_matcher()

    async def parse_logs(self, logs: List[str]) -> List[LogEntry]:
        """解析日志并结构化"""
        pass

    async def detect_patterns(self, log_entries: List[LogEntry]) -> List[ErrorPattern]:
        """检测错误模式"""
        pass

    async def analyze_root_causes(self,
                                patterns: List[ErrorPattern],
                                context: Dict[str, Any]) -> List[RootCause]:
        """分析根本原因"""
        pass

    async def make_decision(self,
                           root_causes: List[RootCause],
                           history: List[Dict[str, Any]]) -> AnalysisDecision:
        """生成决策建议"""
        pass

    async def check_convergence(self,
                               iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查收敛性"""
        pass
```

**实现要点**：
- 集成多种日志解析算法（正则、模板、ML）
- 支持增量学习和模式更新
- 提供可解释的决策过程
- 实现自适应阈值和置信度计算

---

## 2. CrewAI Agent系统详细设计

### 2.1 Agent架构概述

基于CrewAI框架的四大核心Agent协作系统，与AGENT_DESIGN.md完全对齐：

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from typing import List, Dict, Any

class AgentSystem:
    """CrewAI Agent系统主控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = self._initialize_agents()
        self.crew = self._initialize_crew()
        self.task_queue = self._initialize_task_queue()
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """初始化所有Agent"""
        return {
            "code_agent": self._create_code_agent(),
            "test_agent": self._create_test_agent(),
            "analysis_agent": self._create_analysis_agent(),
            "kb_agent": self._create_kb_agent()
        }
```

### 2.2 CodeAgent详细设计

**角色定义**：
```
角色：资深固件代码专家
目标：分析C/C++代码，识别问题并生成高质量修改建议
背景：具备深度编译器、固件架构、调试经验
```

**工具定义**：
```python
class CodeAnalysisTool(BaseTool):
    name: str = "代码分析工具"
    description: str = "分析C/C++代码，识别潜在问题和优化点"
    
    def _run(self, file_paths: str, analysis_type: str) -> str:
        # 实现代码分析逻辑
        pass

class CodeModificationTool(BaseTool):
    name: str = "代码修改工具"
    description: str = "生成和应用代码修改建议"
    
    def _run(self, analysis_result: str, requirements: str) -> str:
        # 实现代码修改逻辑
        pass

class StaticAnalysisTool(BaseTool):
    name: str = "静态分析工具"
    description: str = "执行静态代码分析"
    
    def _run(self, code_files: str, rules: str) -> str:
        # 实现静态分析逻辑
        pass

def create_code_agent() -> Agent:
    """创建CodeAgent"""
    return Agent(
        role="资深固件代码专家",
        goal="生成高质量、可应用的C/C++代码修改建议",
        backstory="""你是一位资深的固件开发专家，具备：
        - 10+年C/C++开发经验
        - 深度编译器技术理解
        - 固件架构和调试专家
        - 熟悉多种处理器架构（x86, ARM, RISC-V）
        - 丰富的性能优化和问题诊断经验""",
        tools=[
            CodeAnalysisTool(),
            CodeModificationTool(),
            StaticAnalysisTool(),
            GitTool(),
            BuildTool(),
            AITool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True,
        cache=True
    )
```

### 2.3 TestAgent详细设计

**角色定义**：
```
角色：测试执行专家
目标：管理和执行多环境测试，收集标准化结果
背景：熟悉各种测试框架和硬件环境
```

**工具定义**：
```python
class QEMUControlTool(BaseTool):
    name: str = "QEMU控制工具"
    description: str = "启动和管理QEMU测试环境"
    
    def _run(self, config: str, action: str) -> str:
        # 实现QEMU控制逻辑
        pass

class TestExecutionTool(BaseTool):
    name: str = "测试执行工具"
    description: str = "执行测试用例并收集结果"
    
    def _run(self, test_cases: str, environment: str) -> str:
        # 实现测试执行逻辑
        pass

class HardwareControlTool(BaseTool):
    name: str = "硬件控制工具"
    description: str = "控制目标板和硬件设备"
    
    def _run(self, board_id: str, operation: str) -> str:
        # 实现硬件控制逻辑
        pass

def create_test_agent() -> Agent:
    """创建TestAgent"""
    return Agent(
        role="测试执行专家",
        goal="确保测试环境的可靠性和测试结果的准确性",
        backstory="""你是一位测试执行专家，具备：
        - 丰富的自动化测试经验
        - 熟悉QEMU和各种硬件测试环境
        - 精通多种测试框架（pytest, ctest, gtest等）
        - 硬件调试和故障诊断能力
        - 测试用例设计和优化经验""",
        tools=[
            QEMUControlTool(),
            TestExecutionTool(),
            HardwareControlTool(),
            EnvironmentManager(),
            ResourceMonitor(),
            TestResultCollector()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=True
    )
```

### 2.4 AnalysisAgent详细设计

**角色定义**：
```
角色：智能分析专家
目标：深度分析测试结果，识别根本原因并生成决策建议
背景：具备AI分析和系统诊断专长
```

**工具定义**：
```python
class LogAnalysisTool(BaseTool):
    name: str = "日志分析工具"
    description: str = "智能解析和分析测试日志"
    
    def _run(self, logs: str, analysis_type: str) -> str:
        # 实现日志分析逻辑
        pass

class RootCauseAnalysisTool(BaseTool):
    name: str = "根因分析工具"
    description: str = "基于模式识别进行根本原因分析"
    
    def _run(self, test_results: str, context: str) -> str:
        # 实现根因分析逻辑
        pass

class DecisionMakingTool(BaseTool):
    name: str = "决策制定工具"
    description: str = "基于分析结果制定下一步行动策略"
    
    def _run(self, analysis_results: str, constraints: str) -> str:
        # 实现决策制定逻辑
        pass

def create_analysis_agent() -> Agent:
    """创建AnalysisAgent"""
    return Agent(
        role="智能分析专家",
        goal="提供准确的问题诊断和智能的决策建议",
        backstory="""你是一位AI分析专家，具备：
        - 深度学习和机器学习专长
        - 系统性能和故障诊断经验
        - 数据挖掘和模式识别能力
        - 统计学和概率论基础
        - 复杂系统分析和建模能力""",
        tools=[
            LogAnalysisTool(),
            RootCauseAnalysisTool(),
            DecisionMakingTool(),
            StatisticalAnalyzer(),
            PatternMatcher(),
            TrendAnalyzer()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        memory=True,
        cache=True
    )
```

### 2.5 KBAgent详细设计

**角色定义**：
```
角色：知识库专家
目标：管理知识库，提供RAG增强和经验复用
背景：知识工程和信息检索专家
```

**工具定义**：
```python
class KnowledgeRetrievalTool(BaseTool):
    name: str = "知识检索工具"
    description: str = "从知识库检索相关信息"
    
    def _run(self, query: str, filters: str) -> str:
        # 实现知识检索逻辑
        pass

class KnowledgeStorageTool(BaseTool):
    name: str = "知识存储工具"
    description: str = "将新知识存储到知识库"
    
    def _run(self, knowledge: str, metadata: str) -> str:
        # 实现知识存储逻辑
        pass

class RAGEnhancementTool(BaseTool):
    name: str = "RAG增强工具"
    description: str = "为Agent决策提供RAG增强"
    
    def _run(self, query: str, context: str) -> str:
        # 实现RAG增强逻辑
        pass

def create_kb_agent() -> Agent:
    """创建KBAgent"""
    return Agent(
        role="知识库专家",
        goal="确保知识的高效管理和智能复用",
        backstory="""你是一位知识工程专家，具备：
        - 信息检索和知识图谱专长
        - RAG（检索增强生成）技术经验
        - 语义理解和相似度计算能力
        - 知识组织和分类经验
        - 自然语言处理和文本挖掘专长""",
        tools=[
            KnowledgeRetrievalTool(),
            KnowledgeStorageTool(),
            RAGEnhancementTool(),
            VectorDatabaseTool(),
            SemanticSearchTool(),
            KnowledgeGraphTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=True,
        cache=True
    )
```

### 2.6 Agent协作机制

```python
class AgentOrchestrator:
    """Agent编排器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.crew = self._create_crew()
        self.message_bus = self._init_message_bus()
        self.state_manager = self._init_state_manager()
        
    async def execute_iteration(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行一次完整的迭代"""
        # 1. CodeAgent分析代码并生成修改方案
        code_task = Task(
            description=f"分析代码并生成修改方案：{task['description']}",
            agent=self.agents['code_agent'],
            expected_output="结构化的修改建议和实施方案"
        )
        
        # 2. TestAgent执行测试
        test_task = Task(
            description="执行测试并收集结果",
            agent=self.agents['test_agent'],
            expected_output="标准化的测试结果和日志"
        )
        
        # 3. AnalysisAgent分析结果
        analysis_task = Task(
            description="分析测试结果并制定决策",
            agent=self.agents['analysis_agent'],
            expected_output="决策建议和下一步行动"
        )
        
        # 4. KBAgent管理知识
        kb_task = Task(
            description="将经验存储到知识库",
            agent=self.agents['kb_agent'],
            expected_output="知识库更新确认"
        )
        
        # 执行协作流程
        result = self.crew.kickoff({
            'code_task': code_task,
            'test_task': test_task,
            'analysis_task': analysis_task,
            'kb_task': kb_task
        })
        
        return result
```

---

## 3. LangGraph状态机详细设计

### 3.1 状态机架构

与STATE_MACHINE.md完全对应的LangGraph状态机实现：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from datetime import datetime
import uuid

class IterationState(TypedDict):
    """状态机上下文"""
    iteration_index: int
    max_iterations: int
    goal: str
    repo_snapshot: Dict[str, Any]
    analysis: Optional[Dict[str, Any]]
    patch_plan: Optional[List[Dict[str, Any]]]
    test_plan: Optional[Dict[str, Any]]
    last_build_result: Optional[Dict[str, Any]]
    last_test_result: Optional[Dict[str, Any]]
    error_state: Optional[Dict[str, Any]]
    convergence: Optional[Dict[str, Any]]
    decision_trace: List[Dict[str, Any]]
    artifacts: List[str]

class FirmwareTestStateMachine:
    """固件测试状态机"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = self._build_graph()
        self.code_analyzer = CodeAnalyzer(config)
        self.test_orchestrator = TestOrchestrator(config)
        self.result_analyzer = ResultAnalyzer(config)
        self.code_modifier = CodeModifier(config)
        
    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(IterationState)
        
        # 添加节点
        workflow.add_node("IDLE", self._idle_node)
        workflow.add_node("INIT", self._init_node)
        workflow.add_node("CODE_ANALYSIS", self._code_analysis_node)
        workflow.add_node("PATCH_GENERATION", self._patch_generation_node)
        workflow.add_node("PATCH_APPLY", self._patch_apply_node)
        workflow.add_node("BUILD_SETUP", self._build_setup_node)
        workflow.add_node("BUILD_RUN", self._build_run_node)
        workflow.add_node("TEST_SETUP", self._test_setup_node)
        workflow.add_node("TEST_RUN", self._test_run_node)
        workflow.add_node("RESULT_COLLECTION", self._result_collection_node)
        workflow.add_node("RESULT_ANALYSIS", self._result_analysis_node)
        workflow.add_node("CONVERGENCE_CHECK", self._convergence_check_node)
        workflow.add_node("ERROR_RECOVERY", self._error_recovery_node)
        workflow.add_node("SUCCESS", self._success_node)
        workflow.add_node("FAILURE", self._failure_node)
        workflow.add_node("ABORTED", self._aborted_node)
        
        # 添加边和条件转移
        workflow.add_edge("IDLE", "INIT")
        workflow.add_edge("INIT", "CODE_ANALYSIS")
        
        # CODE_ANALYSIS的分支
        workflow.add_conditional_edges(
            "CODE_ANALYSIS",
            self._code_analysis_condition,
            {
                "continue": "PATCH_GENERATION",
                "error": "ERROR_RECOVERY",
                "abort": "ABORTED"
            }
        )
        
        # PATCH_GENERATION的分支
        workflow.add_conditional_edges(
            "PATCH_GENERATION",
            self._patch_generation_condition,
            {
                "continue": "PATCH_APPLY",
                "error": "ERROR_RECOVERY",
                "abort": "ABORTED"
            }
        )
        
        workflow.add_edge("PATCH_APPLY", "BUILD_SETUP")
        workflow.add_edge("BUILD_SETUP", "BUILD_RUN")
        
        # BUILD_RUN的分支
        workflow.add_conditional_edges(
            "BUILD_RUN",
            self._build_run_condition,
            {
                "success": "TEST_SETUP",
                "error": "ERROR_RECOVERY",
                "abort": "ABORTED"
            }
        )
        
        workflow.add_edge("TEST_SETUP", "TEST_RUN")
        workflow.add_edge("TEST_RUN", "RESULT_COLLECTION")
        workflow.add_edge("RESULT_COLLECTION", "RESULT_ANALYSIS")
        
        # RESULT_ANALYSIS的分支
        workflow.add_conditional_edges(
            "RESULT_ANALYSIS",
            self._result_analysis_condition,
            {
                "continue": "CONVERGENCE_CHECK",
                "error": "ERROR_RECOVERY",
                "abort": "ABORTED"
            }
        )
        
        # CONVERGENCE_CHECK的分支
        workflow.add_conditional_edges(
            "CONVERGENCE_CHECK",
            self._convergence_check_condition,
            {
                "continue_iteration": "CODE_ANALYSIS",
                "success": "SUCCESS",
                "failure": "FAILURE",
                "max_iterations": "FAILURE"
            }
        )
        
        # ERROR_RECOVERY的分支
        workflow.add_conditional_edges(
            "ERROR_RECOVERY",
            self._error_recovery_condition,
            {
                "retry": "CODE_ANALYSIS",
                "rollback": "PATCH_APPLY",
                "give_up": "FAILURE",
                "escalate": "ABORTED"
            }
        )
        
        # 设置入口和出口
        workflow.set_entry_point("IDLE")
        workflow.add_edge("SUCCESS", END)
        workflow.add_edge("FAILURE", END)
        workflow.add_edge("ABORTED", END)
        
        return workflow.compile()
```

### 3.2 核心节点实现

```python
async def _code_analysis_node(self, state: IterationState) -> IterationState:
    """代码分析节点"""
    try:
        # 1. 获取代码文件
        files = await self._get_repo_files(state['repo_snapshot'])
        
        # 2. 执行代码分析
        analysis_result = await self.code_analyzer.analyze_code(
            files=files,
            analysis_type=AnalysisType.SEMANTIC,
            context={
                'goal': state['goal'],
                'test_results': state.get('last_test_result'),
                'error_patterns': state.get('error_state', {}).get('patterns', [])
            }
        )
        
        # 3. 更新状态
        state['analysis'] = analysis_result.__dict__
        state['decision_trace'].append({
            'timestamp': datetime.now().isoformat(),
            'node': 'CODE_ANALYSIS',
            'action': 'completed',
            'result': 'success',
            'details': f"Found {len(analysis_result.issues)} issues"
        })
        
        return state
        
    except Exception as e:
        state['error_state'] = {
            'error_type': 'analysis_error',
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return state

async def _test_run_node(self, state: IterationState) -> IterationState:
    """测试执行节点"""
    try:
        # 1. 准备测试环境
        env_id = f"test_env_{uuid.uuid4().hex[:8]}"
        env_config = {
            'type': 'qemu',  # 或其他环境类型
            'firmware_path': state['repo_snapshot'].get('firmware_path'),
            'test_cases': state['test_plan']['test_cases'],
            'timeout': state['test_plan'].get('timeout', 3600)
        }
        
        # 2. 注册环境
        await self.test_orchestrator.register_environment(
            env_id=env_id,
            env_type=EnvironmentType.QEMU,
            config=env_config
        )
        
        # 3. 执行测试
        test_results = await self.test_orchestrator.execute_test_suite(
            env_id=env_id,
            test_cases=state['test_plan']['test_cases'],
            parallel=state['test_plan'].get('parallel', False)
        )
        
        # 4. 清理环境
        await self.test_orchestrator.cleanup_environment(env_id)
        
        state['last_test_result'] = {
            'results': [result.__dict__ for result in test_results],
            'summary': self._summarize_test_results(test_results),
            'timestamp': datetime.now().isoformat()
        }
        
        state['decision_trace'].append({
            'timestamp': datetime.now().isoformat(),
            'node': 'TEST_RUN',
            'action': 'completed',
            'result': 'success',
            'details': f"Executed {len(test_results)} test cases"
        })
        
        return state
        
    except Exception as e:
        state['error_state'] = {
            'error_type': 'test_execution_error',
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return state
```

### 3.3 条件转移逻辑

```python
def _convergence_check_condition(self, state: IterationState) -> str:
    """收敛检查条件"""
    convergence = state.get('convergence', {})
    decision = convergence.get('decision', {})
    
    # 检查是否达到目标
    if decision.get('action') == 'SUCCESS':
        return 'success'
    
    # 检查是否达到最大迭代次数
    if state['iteration_index'] >= state['max_iterations']:
        return 'max_iterations'
    
    # 检查是否应该继续迭代
    if decision.get('action') in ['CONTINUE', 'APPLY_PATCH', 'RERUN_TEST']:
        return 'continue_iteration'
    
    # 检查是否应该失败
    if decision.get('action') in ['FAILURE', 'ESCALATE']:
        return 'failure'
    
    # 默认继续迭代
    return 'continue_iteration'

def _error_recovery_condition(self, state: IterationState) -> str:
    """错误恢复条件"""
    error_state = state.get('error_state', {})
    error_type = error_state.get('error_type', '')
    recovery_count = error_state.get('recovery_count', 0)
    
    # 如果错误太严重，直接升级
    if error_type in ['security_violation', 'data_corruption']:
        return 'escalate'
    
    # 如果已经尝试恢复多次，回滚或放弃
    if recovery_count >= 3:
        return 'give_up'
    
    # 根据错误类型决定恢复策略
    if error_type in ['build_error', 'test_error']:
        return 'retry'
    elif error_type in ['patch_conflict', 'modification_error']:
        return 'rollback'
    else:
        return 'retry'
```

---

## 4. 知识库系统详细设计

### 4.1 Qdrant + PostgreSQL集成架构

与KNOWLEDGE_SCHEMA.md完全对齐的知识库系统：

```python
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
import uuid

class KnowledgeBase:
    """知识库主控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.qdrant_client = self._init_qdrant()
        self.postgres_engine = self._init_postgres()
        self.Session = sessionmaker(bind=self.postgres_engine)
        self.embedding_model = self._init_embedding_model()
        
    def _init_qdrant(self) -> QdrantClient:
        """初始化Qdrant客户端"""
        return QdrantClient(
            host=self.config['qdrant_host'],
            port=self.config['qdrant_port'],
            api_key=self.config.get('qdrant_api_key')
        )
        
    def _init_postgres(self):
        """初始化PostgreSQL"""
        return create_engine(
            f"postgresql://{self.config['postgres_user']}:{self.config['postgres_password']}@{self.config['postgres_host']}:{self.config['postgres_port']}/{self.config['postgres_db']}"
        )
```

### 4.2 KnowledgeUnit数据模型

**Qdrant Collection Schema**：
```python
def setup_knowledge_collection(self):
    """设置知识库集合"""
    collection_config = {
        "vectors": {
            "size": 1536,  # 嵌入向量维度
            "distance": "Cosine"  # 距离度量
        },
        "payload_schema": {
            "knowledge_unit_id": "keyword",
            "title": "keyword",
            "content_type": "keyword",
            "product_line": "keyword",
            "tags": "keyword",
            "confidence_score": "float",
            "created_at": "datetime",
            "updated_at": "datetime",
            "vector_embedding": "vector"
        }
    }
    
    self.qdrant_client.create_collection(
        collection_name="firmware_knowledge",
        vectors_config=collection_config["vectors"],
        payload_schema=collection_config["payload_schema"]
    )
```

**PostgreSQL ORM模型**：
```python
Base = declarative_base()

class KnowledgeUnitORM(Base):
    """知识单元ORM模型"""
    __tablename__ = "knowledge_units"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_unit_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # code_modification, test_result, issue_resolution
    summary = Column(Text)
    detailed_content = Column(Text)
    code_snippets = Column(JSON)
    modification_details = Column(JSON)
    product_line = Column(String, nullable=False)
    soc_type = Column(String)
    firmware_stack = Column(String)
    chipset = Column(String)
    platform = Column(String)
    test_environment = Column(String)
    test_board = Column(String)
    execution_status = Column(String)
    execution_time = Column(DateTime)
    iterations_count = Column(Integer)
    success_rate = Column(Float)
    tags = Column(JSON)  # 标签列表
    priority = Column(String)
    author = Column(String)
    confidence_score = Column(Float)
    related_units = Column(JSON)  # 相关单元ID列表
    parent_issue = Column(String)
    test_executions = Column(JSON)  # 测试执行ID列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String, default="1.0")
    source = Column(String, default="automated_extraction")
```

### 4.3 RAG检索系统

```python
class RAGRetriever:
    """RAG检索器"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.similarity_threshold = 0.7
        
    async def retrieve_relevant_knowledge(self,
                                        query: str,
                                        product_line: Optional[str] = None,
                                        limit: int = 5) -> List[Dict[str, Any]]:
        """检索相关知识"""
        # 1. 生成查询向量
        query_vector = await self.kb.embedding_model.embed_query(query)
        
        # 2. Qdrant向量检索
        search_filter = {}
        if product_line:
            search_filter["must"] = [{"key": "product_line", "match": {"value": product_line}}]
        
        qdrant_results = self.kb.qdrant_client.search(
            collection_name="firmware_knowledge",
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        # 3. PostgreSQL补充检索
        knowledge_unit_ids = [result.id for result in qdrant_results]
        knowledge_units = self._get_knowledge_units_from_db(knowledge_unit_ids)
        
        # 4. 融合结果
        combined_results = []
        for qdrant_result, ku in zip(qdrant_results, knowledge_units):
            combined_results.append({
                'knowledge_unit': ku.__dict__,
                'similarity_score': qdrant_result.score,
                'qdrant_id': qdrant_result.id
            })
        
        return combined_results
```

---

## 5. 数据模型详细设计

### 5.1 SQLAlchemy ORM定义

**核心数据模型**：
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class TaskModel(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, unique=True, nullable=False, index=True)
    task_type = Column(String, nullable=False)  # code_modification, test_execution, analysis
    description = Column(Text, nullable=False)
    input_data = Column(JSON)
    context = Column(JSON)
    priority = Column(Integer, default=5)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 关联关系
    iterations = relationship("IterationModel", back_populates="task")

class IterationModel(Base):
    """迭代模型"""
    __tablename__ = "iterations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    iteration_id = Column(String, unique=True, nullable=False, index=True)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=False)
    iteration_index = Column(Integer, nullable=False)
    goal = Column(Text, nullable=False)
    max_iterations = Column(Integer, default=10)
    
    # 代码分析
    repo_snapshot = Column(JSON)
    code_analysis = Column(JSON)
    patch_plan = Column(JSON)
    
    # 构建和测试
    build_result = Column(JSON)
    test_plan = Column(JSON)
    test_results = Column(JSON)
    
    # 分析和决策
    error_state = Column(JSON)
    convergence = Column(JSON)
    decision_trace = Column(JSON)
    artifacts = Column(JSON)
    
    # 状态
    status = Column(String, default="running")  # running, success, failed, aborted
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # 关联关系
    task = relationship("TaskModel", back_populates="iterations")
    code_modifications = relationship("CodeModificationModel", back_populates="iteration")
    test_executions = relationship("TestExecutionModel", back_populates="iteration")

class CodeModificationModel(Base):
    """代码修改模型"""
    __tablename__ = "code_modifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    modification_id = Column(String, unique=True, nullable=False, index=True)
    iteration_id = Column(String, ForeignKey("iterations.iteration_id"), nullable=False)
    
    # 修改详情
    target_files = Column(JSON, nullable=False)  # 文件列表
    changes = Column(JSON, nullable=False)  # 具体修改
    risk_level = Column(String)  # low, medium, high, critical
    patch_content = Column(Text)  # Git patch格式
    applied = Column(Boolean, default=False)
    
    # 验证结果
    build_status = Column(String)  # success, failed, skipped
    validation_results = Column(JSON)
    
    # 审计
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime)
    
    # 关联关系
    iteration = relationship("IterationModel", back_populates="code_modifications")

class TestExecutionModel(Base):
    """测试执行模型"""
    __tablename__ = "test_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String, unique=True, nullable=False, index=True)
    iteration_id = Column(String, ForeignKey("iterations.iteration_id"), nullable=False)
    
    # 环境信息
    environment_type = Column(String, nullable=False)  # qemu, target_board, bmc
    environment_config = Column(JSON)
    
    # 测试信息
    test_cases = Column(JSON, nullable=False)
    parallel_execution = Column(Boolean, default=False)
    
    # 执行结果
    results = Column(JSON)
    artifacts = Column(JSON)
    logs = Column(Text)
    
    # 状态和时间
    status = Column(String, default="pending")  # pending, running, success, failed, timeout
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # 关联关系
    iteration = relationship("IterationModel", back_populates="test_executions")
```

### 5.2 数据访问层

```python
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """获取数据库会话"""
        return self.Session()

class TaskRepository:
    """任务数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """创建任务"""
        session = self.db.get_session()
        try:
            task = TaskModel(
                task_id=task_data['task_id'],
                task_type=task_data['task_type'],
                description=task_data['description'],
                input_data=task_data.get('input_data'),
                context=task_data.get('context', {}),
                priority=task_data.get('priority', 5)
            )
            session.add(task)
            session.commit()
            return task.task_id
        finally:
            session.close()
            
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        session = self.db.get_session()
        try:
            task = session.query(TaskModel).filter(
                TaskModel.task_id == task_id
            ).first()
            return task.__dict__ if task else None
        finally:
            session.close()
```

---

## 6. API规范详细设计

### 6.1 FastAPI应用结构

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="AI驱动固件智能测试系统API",
    description="固件代码修改、测试执行和智能分析的RESTful API",
    version="2.0.0"
)

# 安全认证
security = HTTPBearer()

class TaskRequest(BaseModel):
    """任务请求模型"""
    task_type: str = Field(..., description="任务类型")
    description: str = Field(..., description="任务描述")
    repository_url: Optional[str] = Field(None, description="代码仓库URL")
    target_commit: Optional[str] = Field(None, description="目标提交")
    patch_content: Optional[str] = Field(None, description="补丁内容")
    test_profile: Dict[str, Any] = Field(default_factory=dict, description="测试配置")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="约束条件")
    max_iterations: int = Field(10, description="最大迭代次数")

class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime]

class IterationResponse(BaseModel):
    """迭代响应模型"""
    iteration_id: str
    iteration_index: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    artifacts: List[str]

class TestResultResponse(BaseModel):
    """测试结果响应模型"""
    execution_id: str
    environment_type: str
    status: str
    results: Dict[str, Any]
    artifacts: List[str]
    execution_time: float
```

### 6.2 核心API路由

```python
@app.post("/api/v2/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """创建新任务"""
    task_id = str(uuid.uuid4())
    
    # 验证请求
    if task_request.task_type not in ['code_modification', 'test_execution', 'analysis']:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    # 创建任务记录
    task_data = {
        'task_id': task_id,
        'task_type': task_request.task_type,
        'description': task_request.description,
        'repository_url': task_request.repository_url,
        'target_commit': task_request.target_commit,
        'patch_content': task_request.patch_content,
        'test_profile': task_request.test_profile,
        'constraints': task_request.constraints,
        'max_iterations': task_request.max_iterations
    }
    
    # 存储到数据库
    await task_repository.create_task(task_data)
    
    # 添加后台任务
    background_tasks.add_task(process_task_async, task_id, task_request)
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        created_at=datetime.utcnow(),
        estimated_completion=None
    )

@app.get("/api/v2/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str):
    """获取任务详情"""
    task = await task_repository.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取迭代记录
    iterations = await iteration_repository.get_iterations_by_task(task_id)
    
    return {
        'task': task,
        'iterations': iterations,
        'current_iteration': iterations[-1] if iterations else None
    }

@app.get("/api/v2/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务实时状态"""
    task = await task_repository.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取当前活跃迭代
    current_iteration = await iteration_repository.get_current_iteration(task_id)
    
    # 获取环境状态
    environments = await environment_repository.get_active_environments(task_id)
    
    return {
        'task_id': task_id,
        'status': task['status'],
        'progress': {
            'current_iteration': current_iteration['iteration_index'] if current_iteration else 0,
            'total_iterations': task.get('max_iterations', 10),
            'estimated_completion': task.get('estimated_completion')
        },
        'environments': environments,
        'last_updated': datetime.utcnow().isoformat()
    }
```

### 6.3 知识库API

```python
@app.get("/api/v2/knowledge/search")
async def search_knowledge(
    query: str,
    product_line: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 10
):
    """搜索知识库"""
    try:
        results = await knowledge_ops.rag_retriever.retrieve_relevant_knowledge(
            query=query,
            product_line=product_line,
            limit=limit
        )
        
        return {
            'query': query,
            'filters': {
                'product_line': product_line,
                'content_type': content_type
            },
            'results': results,
            'total': len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")

@app.post("/api/v2/knowledge")
async def add_knowledge_unit(knowledge_data: Dict[str, Any]):
    """添加知识单元"""
    try:
        knowledge_unit_id = await knowledge_ops.add_knowledge_unit(knowledge_data)
        return {
            'knowledge_unit_id': knowledge_unit_id,
            'status': 'added',
            'created_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add knowledge: {str(e)}")

@app.get("/api/v2/knowledge/{knowledge_unit_id}")
async def get_knowledge_unit(knowledge_unit_id: str):
    """获取知识单元详情"""
    # 从Qdrant获取
    qdrant_result = await knowledge_ops.get_from_qdrant(knowledge_unit_id)
    
    # 从PostgreSQL获取
    sql_result = await knowledge_ops.get_from_postgres(knowledge_unit_id)
    
    if not qdrant_result and not sql_result:
        raise HTTPException(status_code=404, detail="Knowledge unit not found")
    
    return {
        'qdrant_data': qdrant_result,
        'sql_data': sql_result,
        'retrieved_at': datetime.utcnow().isoformat()
    }
```

---

## 7. 配置和策略详细设计

### 7.1 环境变量配置

```python
from pydantic import BaseSettings, Field
from typing import Dict, Any, Optional, List
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "AI Firmware Test System"
    app_version: str = "2.0.0"
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Qdrant向量数据库配置
    qdrant_host: str = Field("localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(6333, env="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field("firmware_knowledge", env="QDRANT_COLLECTION")
    
    # 大模型API配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")
    embedding_model: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    chat_model: str = Field("gpt-4", env="CHAT_MODEL")
    
    # 内网模型API配置
    intranet_api_url: Optional[str] = Field(None, env="INTRANET_API_URL")
    intranet_api_key: Optional[str] = Field(None, env="INTRANET_API_KEY")
    
    # GitLab配置
    gitlab_url: str = Field(..., env="GITLAB_URL")
    gitlab_token: str = Field(..., env="GITLAB_TOKEN")
    gitlab_project_id: str = Field(..., env="GITLAB_PROJECT_ID")
    
    # Redmine配置
    redmine_url: str = Field(..., env="REDMINE_URL")
    redmine_key: str = Field(..., env="REDMINE_KEY")
    redmine_project_id: str = Field(..., env="REDMINE_PROJECT_ID")
    
    # 测试环境配置
    qemu_config: Dict[str, Any] = Field(default_factory=dict, env="QEMU_CONFIG")
    target_board_config: Dict[str, Any] = Field(default_factory=dict, env="TARGET_BOARD_CONFIG")
    bmc_config: Dict[str, Any] = Field(default_factory=dict, env="BMC_CONFIG")
    
    # 执行策略配置
    max_concurrent_tasks: int = Field(5, env="MAX_CONCURRENT_TASKS")
    max_iterations_per_task: int = Field(10, env="MAX_ITERATIONS_PER_TASK")
    default_timeout: int = Field(3600, env="DEFAULT_TIMEOUT")
    retry_attempts: int = Field(3, env="RETRY_ATTEMPTS")
    
    # 安全配置
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    allowed_hosts: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    
    # 存储配置
    artifacts_storage_path: str = Field("/tmp/artifacts", env="ARTIFACTS_STORAGE_PATH")
    max_artifacts_size_gb: int = Field(10, env="MAX_ARTIFACTS_SIZE_GB")
    cleanup_interval_hours: int = Field(24, env="CLEANUP_INTERVAL_HOURS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 全局配置实例
settings = Settings()
```

### 7.2 启动策略配置

```python
class StartupStrategy:
    """启动策略管理器"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.startup_sequence = [
            "database",
            "redis",
            "qdrant",
            "external_services",
            "agent_system",
            "api_server"
        ]
        
    async def initialize_system(self) -> bool:
        """初始化整个系统"""
        try:
            # 1. 初始化数据库
            await self._init_database()
            
            # 2. 初始化Redis（可选：仅在启用缓存加速时）
            if self.config.get("cache_enabled"):
                await self._init_redis()
            
            # 3. 初始化Qdrant
            await self._init_qdrant()
            
            # 4. 初始化外部服务
            await self._init_external_services()
            
            # 5. 初始化Agent系统
            await self._init_agent_system()
            
            # 6. 启动API服务器
            await self._init_api_server()
            
            return True
            
        except Exception as e:
            print(f"System initialization failed: {e}")
            await self._cleanup_failed_startup()
            return False
```

---

## 8. 集成服务设计 (Layer 4 Service Layer)

本章节详细定义系统与外部第三方服务的集成方案，涵盖 Redmine、GitLab、大模型 API 以及通用服务治理策略，确保系统在复杂外部依赖下的稳定性与一致性。

### 8.1 Redmine 集成模块

Redmine 集成模块负责将系统的测试任务、缺陷分析与外部工单系统同步，实现测试过程的可追溯性。

#### 8.1.1 REST API 调用规范

系统统一采用 Redmine REST API v3 进行交互，所有请求需带上 `X-Redmine-API-Key`。

**核心接口定义与数据模型**：

```python
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field
from datetime import datetime

class RedmineCustomField(BaseModel):
    id: int
    value: Any

class RedmineIssue(BaseModel):
    id: Optional[int]
    subject: str = Field(..., description="工单标题")
    description: str = Field(..., description="工单详细描述")
    project_id: int = Field(..., description="项目ID")
    status_id: int = Field(default=1, description="状态ID")
    priority_id: int = Field(default=2, description="优先级ID")
    tracker_id: int = Field(default=1, description="跟踪器ID")
    assigned_to_id: Optional[int] = None
    category_id: Optional[int] = None
    fixed_version_id: Optional[int] = None
    custom_fields: List[RedmineCustomField] = []
    parent_issue_id: Optional[int] = None

class RedmineJournal(BaseModel):
    notes: str
    private_notes: bool = False

class RedmineClient:
    """Redmine API 封装客户端 - 增强版"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json"
        }

    async def get_issue(self, issue_id: int) -> Dict[str, Any]:
        """获取工单详情，包含变更记录"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/issues/{issue_id}.json?include=journals,attachments,watchers",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["issue"]

    async def create_issue(self, issue: RedmineIssue) -> int:
        """创建工单，支持父子工单关联"""
        payload = {"issue": issue.dict(exclude_none=True)}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/issues.json",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()["issue"]["id"]

    async def update_issue(self, issue_id: int, updates: Dict[str, Any], notes: str = None):
        """更新工单状态及备注，支持追加变更记录"""
        payload = {"issue": updates}
        if notes:
            payload["issue"]["notes"] = notes
            
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/issues/{issue_id}.json",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

    async def upload_attachment(self, issue_id: int, file_content: bytes, filename: str, description: str = ""):
        """上传附件并关联至工单 - 增加描述字段"""
        # 1. 上传文件获取 token
        async with httpx.AsyncClient() as client:
            upload_resp = await client.post(
                f"{self.base_url}/uploads.json",
                headers={**self.headers, "Content-Type": "application/octet-stream"},
                content=file_content
            )
            upload_resp.raise_for_status()
            token = upload_resp.json()["upload"]["token"]
            
            # 2. 关联附件到工单
            payload = {
                "issue": {
                    "uploads": [
                        {
                            "token": token, 
                            "filename": filename, 
                            "description": description,
                            "content_type": "application/octet-stream"
                        }
                    ]
                }
            }
            await client.put(
                f"{self.base_url}/issues/{issue_id}.json",
                headers=self.headers,
                json=payload
            )

    async def list_projects(self) -> List[Dict[str, Any]]:
        """获取所有可用项目列表"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/projects.json", headers=self.headers)
            response.raise_for_status()
            return response.json()["projects"]


#### 8.1.2 数据映射与状态同步策略

**状态映射细节 (State Mapping Details)**：

| 内部 TaskState | Redmine Status ID | 状态转换触发条件 |
| :--- | :--- | :--- |
| **INITIALIZING** | 1 (New) | 任务被 Agent 接管，生成初始分析计划 |
| **ANALYZING** | 2 (In Progress) | CodeAgent 开始对代码库执行静态扫描或 LLM 理解 |
| **PATCH_GENERATING** | 2 (In Progress) | CodeModifier 正在根据分析结论生成补丁 |
| **TESTING** | 2 (In Progress) | TestAgent 正在配置环境或执行测试用例 |
| **WAITING_APPROVAL** | 4 (Feedback) | 高风险补丁生成，等待人工在 Redmine 进行“通过/拒绝”操作 |
| **COMPLETED** | 3 (Resolved) | 测试通过，补丁已成功合并 |
| **FAILED** | 6 (Rejected) | 多次重试后无法解决问题，或人工在 Redmine 标记为拒绝 |

**双向同步机制与交互流程**：

```mermaid
sequenceDiagram
    participant Agent as Agent System
    participant RS as RedmineService
    participant RM as Redmine API
    participant User as Developer

    Agent->>RS: update_task_status(Task_01, TESTING)
    RS->>RM: PUT /issues/123.json (status_id: 2, notes: "Start testing...")
    
    Note over RM, User: User checks issue in Redmine
    
    User->>RM: Update Status to "Resolved" (status_id: 3)
    
    loop Every 5 Minutes
        RS->>RM: GET /issues/123.json
        RM-->>RS: Return status_id: 3
        RS->>Agent: trigger_event(EXTERNAL_RESOLVE)
        Agent->>Agent: Stop iteration and Cleanup
    end
```

#### 8.1.3 冲突解决与幂等性保障

1. **乐观锁机制**：在更新 Redmine 时检查 `lock_version` (如支持) 或比较 `updated_on` 时间戳，防止 Agent 覆盖人工手动修改。
2. **幂等创建**：在本地数据库存储 `redmine_issue_id`。创建前先查询，若已存在则执行更新。
3. **附件冗余清理**：当补丁被重新生成时，在 Redmine 记录中标记旧补丁为“已过时 (Obsolete)”，而不是直接删除。

---

### 8.2 GitLab CI 集成模块

GitLab 集成模块负责代码管理及自动化测试流水线的触发。

#### 8.2.1 Webhook 监听、安全解析与任务路由

系统需要处理多种 GitLab 事件，并确保请求来源合法。

```python
import hmac
import hashlib

class GitLabWebhookManager:
    def __init__(self, secret_token: str):
        self.secret_token = secret_token

    def verify_token(self, x_gitlab_token: str) -> bool:
        """校验 Webhook Token"""
        return hmac.compare_digest(x_gitlab_token, self.secret_token)

    async def parse_and_route(self, request: Request):
        if not self.verify_token(request.headers.get("X-Gitlab-Token")):
            raise HTTPException(status_code=403, detail="Invalid token")
            
        payload = await request.json()
        event_type = request.headers.get("X-Gitlab-Event")
        
        if event_type == "Push Hook":
            # 路由至代码变更分析逻辑
            return await self._route_push_event(payload)
        elif event_type == "Merge Request Hook":
            # 路由至 MR 质量门禁逻辑
            return await self._route_mr_event(payload)
        elif event_type == "Pipeline Hook":
            # 路由至测试结果回填逻辑
            return await self._route_pipeline_event(payload)

    async def _route_pipeline_event(self, payload: Dict[str, Any]):
        """处理流水线状态变更通知"""
        pipeline_id = payload["object_attributes"]["id"]
        status = payload["object_attributes"]["status"]
        # 通知 TestAgent 流水线已完成
        return {"type": "PIPELINE_UPDATE", "id": pipeline_id, "status": status}
```

#### 8.2.2 动态 CI 流水线触发与环境参数注入

通过注入特定的 `CI_JOB_TOKEN` 和自定义变量，实现流水线的高度可定制化。

```python
class GitLabCIClient:
    """GitLab CI 交互客户端"""
    
    async def trigger_test_pipeline(self, 
                                   project_id: int, 
                                   branch: str, 
                                   agent_params: Dict[str, str]) -> int:
        """
        触发测试流水线
        :param agent_params: 包含测试环境配置、Agent ID 等
        """
        project = self.gl.projects.get(project_id)
        # 构造注入变量
        vars = [
            {'key': 'AGENT_DRIVEN_TEST', 'value': 'true'},
            {'key': 'TEST_TARGET_ARCH', 'value': agent_params.get('arch', 'x86_64')},
            {'key': 'SIMULATION_TIME', 'value': agent_params.get('timeout', '3600')}
        ]
        
        pipeline = project.pipelines.create({
            'ref': branch,
            'variables': vars
        })
        return pipeline.id

    async def get_job_artifacts(self, project_id: int, job_id: int):
        """下载特定的 Job 产物（如测试报告、QEMU 日志）"""
        project = self.gl.projects.get(project_id)
        job = project.jobs.get(job_id)
        with open(f"artifacts_{job_id}.zip", "wb") as f:
            job.artifacts(streamed=True, action=f.write)
```

#### 8.2.3 构建结果回写与评论功能

Agent 可以在 MR 中自动发表评论，告知测试进度和分析结论。

```python
    async def post_mr_comment(self, project_id: int, mr_iid: int, body: str):
        """在 Merge Request 中发表 Agent 分析评论"""
        project = self.gl.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.notes.create({'body': body})
```

---

### 8.3 统一 HTTP 客户端与重试策略

为了应对外部服务（Redmine, GitLab, LLM API）的网络抖动，系统构建了带有容错机制的 HTTP 客户端。

#### 8.3.1 增强型指数退避重试 (Exponential Backoff with Jitter)

简单的重试可能导致“惊群效应”，引入抖动（Jitter）可以平衡负载。

```python
import random
import asyncio

async def retry_with_jitter(func, max_retries=5, base_delay=1.0):
    for i in range(max_retries):
        try:
            return await func()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            if i == max_retries - 1:
                raise e
            # 计算延迟: base_delay * 2^i + random jitter
            delay = base_delay * (2 ** i) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

#### 8.3.2 错误分类处理与服务隔离

1. **连接隔离 (Connection Pooling)**：为不同的服务配置独立的连接池。
   ```python
   llm_limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
   gitlab_limits = httpx.Limits(max_connections=50, max_keepalive_connections=10)
   ```
2. **超时分类 (Timeout Strategies)**：
   - **Redmine**: 10s (通常响应快)
   - **GitLab Pipeline**: 30s (触发可能慢)
   - **LLM API**: 120s (生成过程长)

---

### 8.4 大模型 API 抽象层

LLM 抽象层通过标准接口隔离各厂商差异，并提供 Token 计算与并发治理能力。

#### 8.4.1 LLMProvider 基类与能力发现

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    def __init__(self, model_name: str, config: Dict[str, Any]):
        self.model_name = model_name
        self.config = config

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        pass

    def count_tokens(self, text: str) -> int:
        """默认实现，子类可覆盖（如使用 tiktoken）"""
        return len(text) // 4 
```

#### 8.4.2 供应商实现细节

- **OpenAIProvider**: 使用 `openai` 官方 SDK，支持 `gpt-4-turbo` 和 `gpt-3.5-turbo`。
- **InternalVLLMProvider**: 对接内网 `vLLM` 部署的 `Llama-3-70B`，通过 `v1/chat/completions` 接口交互。
- **MockProvider**: 用于本地 CI 测试，返回预定义的模拟输出。

#### 8.4.3 并发限流、优先级队列与配额管理

针对内网资源受限场景，实现优先级调度：

```python
class PriorityLLMQueue:
    def __init__(self):
        self.queues = {
            "HIGH": asyncio.Queue(),  # CodeAgent 修改逻辑
            "NORMAL": asyncio.Queue(), # TestAgent 解析日志
            "LOW": asyncio.Queue()     # KBAgent 向量化
        }

    async def get_next_task(self):
        # 按照优先级顺序检查队列
        for p in ["HIGH", "NORMAL", "LOW"]:
            if not self.queues[p].empty():
                return await self.queues[p].get()
        return None
```

---

### 8.5 故障转移、降级策略与自愈能力

#### 8.5.1 多层级降级矩阵 (Degradation Matrix)

| 故障场景 | 核心受损功能 | 降级方案 |
| :--- | :--- | :--- |
| **LLM API 宕机** | 修改建议生成、日志深度分析 | 切换至备用模型（如从 GPT-4 降级至本地开源模型）；切换至本地静态规则引擎 (Clang-Tidy) |
| **GitLab 无法访问** | 代码同步、CI 触发 | 使用本地缓存的旧版本代码执行实验；排队等待直到恢复 |
| **Redmine 宕机** | 任务跟踪、审批流 | 切换至本地嵌入式数据库 (SQLite) 记录状态，恢复后重放 |
| **QEMU 环境耗尽** | 测试执行 | 任务进入等待队列；自动释放 2 小时以上的僵尸环境 |

#### 8.5.2 断路器模式 (Circuit Breaker) 实现

```python
from enum import Enum

class CBState(Enum):
    CLOSED = "closed"   # 正常
    OPEN = "open"       # 熔断
    HALF_OPEN = "half"  # 尝试恢复

class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.state = CBState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._last_failure_time = 0

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CBState.OPEN
            self._last_failure_time = asyncio.get_event_loop().time()

    def can_execute(self) -> bool:
        if self.state == CBState.CLOSED:
            return True
        if self.state == CBState.OPEN:
            if asyncio.get_event_loop().time() - self._last_failure_time > self.reset_timeout:
                self.state = CBState.HALF_OPEN
                return True
            return False
        return True # HALF_OPEN 状态允许尝试
```

#### 8.5.3 离线恢复与自愈流程 (Self-healing)

1. **状态对齐 (State Reconciliation)**：系统重启后，首先与 GitLab 和 Redmine 进行状态对齐。若 GitLab CI 已完成而系统未记录，自动触发 `ResultAnalyzer`。
2. **重试队列持久化**：所有待重试的任务均存储在持久化消息队列中，防止进程异常退出导致任务丢失。

---

## 总结

本详细设计文档（DETAILED_DESIGN_V2.md）与所有已有文档保持完整一致，提供了：

1. **核心模块详细设计**：CodeAnalyzer、CodeModifier、TestOrchestrator、ResultAnalyzer的完整实现规格
2. **CrewAI Agent系统设计**：与AGENT_DESIGN.md对齐的四大Agent实现
3. **LangGraph状态机设计**：与STATE_MACHINE.md对应的完整状态机实现
4. **知识库系统设计**：与KNOWLEDGE_SCHEMA.md对齐的Qdrant+PostgreSQL架构
5. **数据模型设计**：SQLAlchemy ORM完整定义
6. **API规范设计**：FastAPI路由完整实现
7. **配置策略设计**：环境变量、启动策略、部署配置
8. **集成服务设计**：Redmine、GitLab、大模型 API 集成及故障降级策略

每个模块都提供了详细的接口定义、实现要点、技术规格和完成标准，为Phase 2-6的工程实现提供了精确的技术指导。

文档确保了与REQUIREMENTS.md的18点需求、ARCHITECTURE_V2.md的系统架构、AGENT_DESIGN.md的Agent设计、STATE_MACHINE.md的状态机、KNOWLEDGE_SCHEMA.md的知识库schema以及WORK_PLAN_V2.md的工作计划的完全一致性。
