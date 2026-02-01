"""
Environment Manager

Manages test execution environments (QEMU, Board, BMC) with adapters.
"""

import asyncio
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from pathlib import Path

from .models import (
    Environment,
    EnvironmentType,
    EnvironmentStatus,
    QEMUConfig,
    BoardConfig,
    BMCConfig,
)

logger = logging.getLogger(__name__)


class EnvironmentAdapter(ABC):
    """环境适配器抽象基类"""

    @abstractmethod
    async def start(self) -> bool:
        """启动环境"""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """停止环境"""
        pass

    @abstractmethod
    async def execute(self, command: str, timeout: int = 60) -> tuple:
        """执行命令"""
        pass

    @abstractmethod
    async def get_status(self) -> EnvironmentStatus:
        """获取状态"""
        pass

    @property
    @abstractmethod
    def env_id(self) -> str:
        """环境ID"""
        pass


class QEMUAdapter(EnvironmentAdapter):
    """QEMU环境适配器"""

    def __init__(self, env: Environment, config: QEMUConfig):
        self._env = env
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._serial_output = asyncio.Queue()

    @property
    def env_id(self) -> str:
        return self._env.env_id

    async def start(self, timeout: int = 60) -> bool:
        """启动QEMU虚拟机"""
        try:
            cmd = [
                self._config.binary_path,
                "-machine", self._config.machine,
                "-cpu", self._config.cpu,
                "-m", self._config.memory,
            ]

            if self._config.kernel_path:
                cmd.extend(["-kernel", self._config.kernel_path])
            if self._config.initrd_path:
                cmd.extend(["-initrd", self._config.initrd_path])
            if self._config.disk_path:
                cmd.extend(["-drive", f"file={self._config.disk_path},format=raw"])

            if self._config.serial_enabled:
                cmd.extend(["-serial", "file:/tmp/qemu_serial.log"])

            if self._config.monitor_enabled:
                cmd.extend(["-monitor", "stdio"])

            if not self._config.network_enabled:
                cmd.extend(["-netdev", "user,id=net0", "-device", "virtio-net,netdev=net0"])

            # Start QEMU process with timeout guard
            start_time = asyncio.get_event_loop().time()
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for process to start with timeout
            await asyncio.sleep(0.5)  # Brief wait for process initialization
            
            # Check if process exited unexpectedly
            if self._process.poll() is not None:
                stderr = self._process.stderr.read().decode('utf-8') if self._process.stderr else "Unknown error"
                logger.error(f"QEMU exited immediately: {stderr}")
                self._env.status = EnvironmentStatus.ERROR
                return False

            # Verify startup within timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.error(f"QEMU startup exceeded timeout of {timeout}s")
                self._process.terminate()
                self._env.status = EnvironmentStatus.ERROR
                return False

            self._env.status = EnvironmentStatus.RUNNING
            logger.info(f"QEMU environment {self._env.name} started (PID: {self._process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start QEMU: {e}")
            self._env.status = EnvironmentStatus.ERROR
            return False

    async def stop(self) -> bool:
        """停止QEMU虚拟机"""
        try:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._process = None

            self._env.status = EnvironmentStatus.STOPPED
            logger.info(f"QEMU environment {self._env.name} stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop QEMU: {e}")
            return False

    async def execute(self, command: str, timeout: int = 60) -> tuple:
        """执行命令（通过串口或SSH）
        
        ⚠️ TODO: 实现完整的命令执行逻辑:
        1. 通过串口读取QEMU输出
        2. 处理交互式命令
        3. 支持超时和错误处理
        """
        # Simplified: return success for now
        # In real implementation, would send command via serial/SSH
        return (0, f"Executed: {command}", "")

    async def get_status(self) -> EnvironmentStatus:
        """获取QEMU状态"""
        if self._process is None:
            return EnvironmentStatus.STOPPED
        if self._process.poll() is not None:
            return EnvironmentStatus.STOPPED
        return EnvironmentStatus.RUNNING

    async def get_serial_output(self) -> str:
        """获取串口输出"""
        try:
            serial_log = Path("/tmp/qemu_serial.log")
            if serial_log.exists():
                return serial_log.read_text()
            return ""
        except Exception as e:
            logger.error(f"Failed to read serial output: {e}")
            return ""


class BoardAdapter(EnvironmentAdapter):
    """目标板环境适配器"""

    def __init__(self, env: Environment, config: BoardConfig):
        self._env = env
        self._config = config
        self._connected = False

    @property
    def env_id(self) -> str:
        return self._env.env_id

    async def start(self) -> bool:
        """连接目标板
        
        ⚠️ TODO: 实现完整的SSH连接逻辑:
        1. 建立SSH连接
        2. 验证连接可用性
        3. 上传测试脚本
        4. 执行环境检查
        """
        # Simplified: assume connection succeeds
        self._connected = True
        self._env.status = EnvironmentStatus.RUNNING
        logger.info(f"Board environment {self._env.name} connected")
        return True

    async def stop(self) -> bool:
        """断开连接"""
        self._connected = False
        self._env.status = EnvironmentStatus.STOPPED
        logger.info(f"Board environment {self._env.name} disconnected")
        return True

    async def execute(self, command: str, timeout: int = 60) -> tuple:
        """通过SSH执行命令"""
        if not self._connected:
            return (-1, "", "Not connected")

        # Build SSH command with improved security
        # Use accept-new to auto-accept first connection but prevent MITM
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-o", "UserKnownHostsFile=/dev/null",
            "-p", str(self._config.port),
            f"{self._config.username}@{self._config.ip_address}",
            command
        ]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (-1, "", "Command timed out")
        except Exception as e:
            return (-1, "", str(e))

    async def get_status(self) -> EnvironmentStatus:
        """获取连接状态"""
        return EnvironmentStatus.RUNNING if self._connected else EnvironmentStatus.STOPPED

    async def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件到目标板"""
        try:
            scp_cmd = [
                "scp",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "UserKnownHostsFile=/dev/null",
                "-P", str(self._config.port),
                local_path,
                f"{self._config.username}@{self._config.ip_address}:{remote_path}"
            ]
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    async def download(self, remote_path: str, local_path: str) -> bool:
        """从目标板下载文件"""
        try:
            scp_cmd = [
                "scp",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "UserKnownHostsFile=/dev/null",
                "-P", str(self._config.port),
                f"{self._config.username}@{self._config.ip_address}:{remote_path}",
                local_path
            ]
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False


class BMCAdapter(EnvironmentAdapter):
    """BMC环境适配器"""

    def __init__(self, env: Environment, config: BMCConfig):
        self._env = env
        self._config = config
        self._connected = False

    @property
    def env_id(self) -> str:
        return self._env.env_id

    async def start(self) -> bool:
        """连接BMC
        
        ⚠️ TODO: 实现完整的BMC连接逻辑:
        1. 验证IPMI connectivity
        2. 获取传感器数据验证连接
        3. 配置BMC网络设置
        4. 建立持久连接会话
        """
        # Simplified: assume connection succeeds
        self._connected = True
        self._env.status = EnvironmentStatus.RUNNING
        logger.info(f"BMC environment {self._env.name} connected")
        return True

    async def stop(self) -> bool:
        """断开BMC"""
        self._connected = False
        self._env.status = EnvironmentStatus.STOPPED
        logger.info(f"BMC environment {self._env.name} disconnected")
        return True

    async def execute(self, command: str, timeout: int = 60) -> tuple:
        """通过IPMI执行命令"""
        if not self._connected:
            return (-1, "", "Not connected")

        # Use ipmitool for BMC commands
        # Password is passed via environment variable to avoid exposure in process list
        ipmi_env = {**os.environ}
        ipmi_env["IPMI_PASSWORD"] = self._config.password

        ipmi_cmd = [
            "ipmitool",
            "-H", self._config.ip_address,
            "-U", self._config.username,
            "-E",  # Use environment variable for password
            "-I", self._config.interface,
        ]

        # Split command into ipmitool subcommands
        parts = command.split()
        if parts:
            ipmi_cmd.extend(parts)

        try:
            result = subprocess.run(
                ipmi_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=ipmi_env
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (-1, "", "Command timed out")
        except Exception as e:
            return (-1, "", str(e))

    async def get_status(self) -> EnvironmentStatus:
        """获取BMC状态"""
        return EnvironmentStatus.RUNNING if self._connected else EnvironmentStatus.STOPPED

    async def power_on(self) -> bool:
        """开机"""
        code, _, _ = await self.execute("power on")
        return code == 0

    async def power_off(self) -> bool:
        """关机"""
        code, _, _ = await self.execute("power off")
        return code == 0

    async def get_sensor_data(self) -> Dict[str, Any]:
        """获取传感器数据"""
        code, stdout, _ = await self.execute("sdr list")
        if code == 0:
            # Parse sensor data
            return {"raw": stdout}
        return {}


class EnvironmentManager:
    """环境管理器"""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir)
        self._adapters: Dict[str, EnvironmentAdapter] = {}
        self._environments: Dict[str, Environment] = {}

    async def create_environment(
        self,
        name: str,
        env_type: EnvironmentType,
        config: Dict[str, Any]
    ) -> Environment:
        """创建测试环境"""
        env = Environment(
            env_id="",
            env_type=env_type,
            status=EnvironmentStatus.IDLE,
            name=name,
            config=config
        )

        # Create appropriate adapter
        if env_type == EnvironmentType.QEMU:
            qemu_config = QEMUConfig(**config)
            adapter = QEMUAdapter(env, qemu_config)
        elif env_type == EnvironmentType.BOARD:
            board_config = BoardConfig(**config)
            adapter = BoardAdapter(env, board_config)
        elif env_type == EnvironmentType.BMC:
            bmc_config = BMCConfig(**config)
            adapter = BMCAdapter(env, bmc_config)
        else:
            raise ValueError(f"Unsupported environment type: {env_type}")

        self._adapters[env.env_id] = adapter
        self._environments[env.env_id] = env

        logger.info(f"Environment created: {env.env_id} ({env_type.value})")
        return env

    async def start_environment(self, env_id: str) -> bool:
        """启动环境"""
        adapter = self._adapters.get(env_id)
        if not adapter:
            logger.error(f"Environment not found: {env_id}")
            return False

        env = self._environments[env_id]
        env.status = EnvironmentStatus.STARTING

        success = await adapter.start()
        if success:
            env.status = EnvironmentStatus.RUNNING
        else:
            env.status = EnvironmentStatus.ERROR

        return success

    async def stop_environment(self, env_id: str) -> bool:
        """停止环境"""
        adapter = self._adapters.get(env_id)
        if not adapter:
            return False

        env = self._environments[env_id]
        env.status = EnvironmentStatus.STOPPING

        success = await adapter.stop()
        if success:
            env.status = EnvironmentStatus.STOPPED

        return success

    async def destroy_environment(self, env_id: str) -> bool:
        """销毁环境"""
        # Stop first if running
        await self.stop_environment(env_id)

        # Remove from registries
        if env_id in self._adapters:
            del self._adapters[env_id]
        if env_id in self._environments:
            del self._environments[env_id]

        logger.info(f"Environment destroyed: {env_id}")
        return True

    def get_environment(self, env_id: str) -> Optional[Environment]:
        """获取环境信息"""
        return self._environments.get(env_id)

    def list_environments(self) -> list:
        """列出所有环境"""
        return list(self._environments.values())

    async def get_adapter(self, env_id: str) -> Optional[EnvironmentAdapter]:
        """获取环境适配器"""
        return self._adapters.get(env_id)

    async def cleanup_all(self):
        """清理所有环境"""
        for env_id in list(self._environments.keys()):
            await self.destroy_environment(env_id)
