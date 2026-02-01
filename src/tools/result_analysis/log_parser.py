"""
Log Parser

Multi-format log parser for test output and system logs.
"""

import re
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import LogEntry


class LogParser:
    """多格式日志解析器"""

    # 常见日志格式正则
    PATTERNS = {
        'syslog': r'(?P<timestamp>\w+\s+\d+\s+[\d:]+)\s+(?P<host>\S+)\s+(?P<source>\S+):\s+(?P<message>.*)',
        'json': None,  # JSON直接解析
        'kernel': r'\[\s*(?P<timestamp>[\d.]+)\]\s+(?P<message>.*)',
        'gcc': r'(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<level>\w+):\s+(?P<message>.*)',
        'pytest': r'(?P<timestamp>[\d\-:.\s]+)\s+(?P<level>\w+)\s+\[(?P<source>[^\]]+)\]\s+(?P<message>.*)',
    }

    # 日志级别映射
    LEVEL_MAP = {
        'DEBUG': 'DEBUG',
        'INFO': 'INFO',
        'WARNING': 'WARNING',
        'WARN': 'WARNING',
        'ERROR': 'ERROR',
        'ERR': 'ERROR',
        'FATAL': 'FATAL',
        'CRITICAL': 'CRITICAL',
        'PANIC': 'FATAL',
    }

    def __init__(self):
        self._compiled_patterns: Dict[str, re.Pattern] = {}

    def parse(
        self,
        content: str,
        format_hint: Optional[str] = None
    ) -> List[LogEntry]:
        """
        解析日志内容

        Args:
            content: 日志内容
            format_hint: 格式提示 (json, syslog, kernel, gcc, pytest)

        Returns:
            List[LogEntry]: 解析后的日志条目
        """
        if not content or not content.strip():
            return []

        entries = []
        lines = content.splitlines()

        for line in lines:
            if not line.strip():
                continue

            entry = self._parse_line(line, format_hint)
            if entry:
                entries.append(entry)

        return entries

    def _parse_line(
        self,
        line: str,
        format_hint: Optional[str] = None
    ) -> Optional[LogEntry]:
        """解析单行日志"""
        try:
            # 检测格式
            format_type = format_hint or self._detect_format(line)

            if format_type == 'json':
                return self._parse_json_line(line)
            elif format_type == 'gcc':
                return self._parse_gcc_line(line)
            else:
                return self._parse_with_regex(line, format_type)

        except Exception as e:
            # 解析失败时返回通用条目
            return LogEntry(
                timestamp=self._get_timestamp(),
                level='INFO',
                source='unknown',
                message=line
            )

    def _detect_format(self, line: str) -> str:
        """自动检测日志格式"""
        # 检查JSON
        if line.strip().startswith('{'):
            return 'json'

        # 检查kernel dmesg格式
        if re.match(r'\[\s*[\d.]+\]', line):
            return 'kernel'

        # 检查GCC输出格式
        if re.match(r'\S+:\d+:\d+:', line):
            return 'gcc'

        # 检查pytest格式
        if re.match(r'\d{4}-\d{2}-\d{2}', line) or '::' in line:
            return 'pytest'

        return 'syslog'

    def _parse_json_line(self, line: str) -> Optional[LogEntry]:
        """解析JSON格式日志"""
        try:
            data = json.loads(line.strip())
            return LogEntry(
                timestamp=data.get('timestamp', self._get_timestamp()),
                level=data.get('level', 'INFO'),
                source=data.get('source', data.get('logger', 'json')),
                message=data.get('message', data.get('msg', str(data))),
                context=data
            )
        except json.JSONDecodeError:
            return None

    def _parse_gcc_line(self, line: str) -> Optional[LogEntry]:
        """解析GCC编译错误格式"""
        match = re.match(
            r'(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<level>\w+):\s+(?P<message>.*)',
            line
        )
        if match:
            groups = match.groupdict()
            return LogEntry(
                timestamp=self._get_timestamp(),
                level=self._normalize_level(groups.get('level', 'ERROR')),
                source=groups.get('file', 'gcc'),
                message=groups.get('message', ''),
                context={
                    'line': groups.get('line'),
                    'column': groups.get('col'),
                    'file': groups.get('file')
                }
            )
        return None

    def _parse_with_regex(self, line: str, format_type: str) -> Optional[LogEntry]:
        """使用正则表达式解析"""
        pattern = self.PATTERNS.get(format_type, self.PATTERNS['syslog'])
        if not pattern:
            return LogEntry(
                timestamp=self._get_timestamp(),
                level='INFO',
                source='unknown',
                message=line
            )

        match = re.match(pattern, line)
        if match:
            groups = match.groupdict()
            return LogEntry(
                timestamp=groups.get('timestamp', self._get_timestamp()),
                level=self._normalize_level(groups.get('level', 'INFO')),
                source=groups.get('source', groups.get('host', format_type)),
                message=groups.get('message', line)
            )

        return LogEntry(
            timestamp=self._get_timestamp(),
            level='INFO',
            source=format_type,
            message=line
        )

    def _normalize_level(self, level: str) -> str:
        """规范化日志级别"""
        return self.LEVEL_MAP.get(level.upper(), 'INFO')

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()

    def extract_errors(self, entries: List[LogEntry]) -> List[LogEntry]:
        """提取错误日志"""
        error_levels = {'ERROR', 'FATAL', 'CRITICAL', 'PANIC'}
        return [e for e in entries if e.level.upper() in error_levels]

    def extract_warnings(self, entries: List[LogEntry]) -> List[LogEntry]:
        """提取警告日志"""
        warning_levels = {'WARNING', 'WARN'}
        return [e for e in entries if e.level.upper() in warning_levels]

    def filter_by_source(self, entries: List[LogEntry], source: str) -> List[LogEntry]:
        """按来源过滤日志"""
        return [e for e in entries if source.lower() in e.source.lower()]

    def group_by_level(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """按级别分组日志"""
        groups: Dict[str, List[LogEntry]] = {}
        for entry in entries:
            level = entry.level.upper()
            if level not in groups:
                groups[level] = []
            groups[level].append(entry)
        return groups
