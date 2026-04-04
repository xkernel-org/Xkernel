"""Tests for src/config.py — TOML config loading."""
import os
import tempfile
import pytest
from src.config import load_config, load_configs, TunableConfig


def _write_toml(content):
    """Write TOML content to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix='.toml')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


class TestSingleTunable:
    """Test single-tunable TOML format."""

    def test_basic_load(self):
        path = _write_toml('''
kernel_dir = "/tmp/test-kernel"
name = "TEST_CONST"
description = "Test constant"

[source]
file = "mm/test.c"
original = "#define TEST_CONST 128"
modified = ["#define TEST_CONST 32", "#define TEST_CONST 64"]
values = [128, 32, 64]
''')
        try:
            kernel_dir, config = load_config(path)
            assert kernel_dir == "/tmp/test-kernel"
            assert config.name == "TEST_CONST"
            assert config.description == "Test constant"
            assert config.file == "mm/test.c"
            assert config.values == (128, 32, 64)
            assert len(config.modified) == 2
            assert config.safe_spans is None
        finally:
            os.unlink(path)

    def test_with_safe_spans(self):
        path = _write_toml('''
kernel_dir = "/tmp"
name = "WITH_SS"
description = "Test with safe spans"

[source]
file = "net/ipv4/tcp.c"
original = "x >> 3"
modified = ["x >> 2", "x >> 1"]
values = [3, 2, 1]

[[safe_spans]]
function = "tcp_func"
start_offset = "0x10"
end_offset = "0x90"

[[safe_spans]]
function = "tcp_func2"
start_offset = "0x20"
end_offset = "0xa0"
''')
        try:
            kernel_dir, config = load_config(path)
            assert config.safe_spans is not None
            assert len(config.safe_spans) == 2
            assert config.safe_spans[0] == ("tcp_func", "0x10", "0x90")
            assert config.safe_spans[1] == ("tcp_func2", "0x20", "0xa0")
        finally:
            os.unlink(path)

    def test_missing_kernel_dir_error(self):
        path = _write_toml('''
name = "DEFAULT_DIR"
description = "No kernel_dir specified"

[source]
file = "mm/test.c"
original = "x"
modified = ["y", "z"]
values = [1, 2, 3]
''')
        try:
            import os
            env_backup = os.environ.pop('KERNEL_DIR', None)
            try:
                with pytest.raises(ValueError, match="Kernel source directory not specified"):
                    load_config(path)
            finally:
                if env_backup is not None:
                    os.environ['KERNEL_DIR'] = env_backup
        finally:
            os.unlink(path)

    def test_env_kernel_dir_override(self):
        path = _write_toml('''
kernel_dir = "/tmp/toml-dir"
name = "ENV_TEST"
description = "Test env override"

[source]
file = "mm/test.c"
original = "x"
modified = ["y", "z"]
values = [1, 2, 3]
''')
        try:
            import os
            old = os.environ.get('KERNEL_DIR')
            os.environ['KERNEL_DIR'] = "/tmp"
            try:
                kernel_dir, config = load_config(path)
                assert kernel_dir == "/tmp"
            finally:
                if old is not None:
                    os.environ['KERNEL_DIR'] = old
                else:
                    os.environ.pop('KERNEL_DIR', None)
        finally:
            os.unlink(path)


class TestMultiTunable:
    """Test multi-tunable TOML format ([[tunables]])."""

    def test_multi_load(self):
        path = _write_toml('''
kernel_dir = "/tmp/multi"

[[tunables]]
name = "CONST_A"
description = "First constant"
file = "a.c"
original = "A 1"
modified = ["A 2", "A 3"]
values = [1, 2, 3]

[[tunables]]
name = "CONST_B"
description = "Second constant"
file = "b.c"
original = "B 10"
modified = ["B 20", "B 30"]
values = [10, 20, 30]
''')
        try:
            kernel_dir, configs = load_configs(path)
            assert kernel_dir == "/tmp/multi"
            assert len(configs) == 2
            assert configs[0].name == "CONST_A"
            assert configs[1].name == "CONST_B"
            assert configs[0].values == (1, 2, 3)
            assert configs[1].values == (10, 20, 30)
        finally:
            os.unlink(path)


class TestValidation:
    """Test error handling for invalid configs."""

    def test_missing_name(self):
        path = _write_toml('''
kernel_dir = "/tmp"
description = "Missing name"

[source]
file = "x.c"
original = "a"
modified = ["b", "c"]
values = [1, 2, 3]
''')
        try:
            with pytest.raises(ValueError, match="name"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_wrong_modified_count(self):
        path = _write_toml('''
kernel_dir = "/tmp"
name = "BAD"
description = "Wrong modified count"

[source]
file = "x.c"
original = "a"
modified = ["b"]
values = [1, 2, 3]
''')
        try:
            with pytest.raises(ValueError, match="modified"):
                load_config(path)
        finally:
            os.unlink(path)

    def test_wrong_values_count(self):
        path = _write_toml('''
kernel_dir = "/tmp"
name = "BAD"
description = "Wrong values count"

[source]
file = "x.c"
original = "a"
modified = ["b", "c"]
values = [1, 2]
''')
        try:
            with pytest.raises(ValueError, match="values"):
                load_config(path)
        finally:
            os.unlink(path)


class TestRealConfigs:
    """Test loading actual config files from the repo."""

    @pytest.fixture
    def project_root(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_shrink_batch_toml(self, project_root):
        path = os.path.join(project_root, 'tunables', 'shrink_batch.toml')
        if not os.path.exists(path):
            pytest.skip("shrink_batch.toml not found")
        kernel_dir, config = load_config(path)
        assert config.name == "SHRINK_BATCH"
        assert config.values == (128, 32, 64)
        assert config.file == "mm/shrinker.c"

    def test_all_toml(self, project_root):
        path = os.path.join(project_root, 'tunables', 'all.toml')
        if not os.path.exists(path):
            pytest.skip("all.toml not found")
        kernel_dir, configs = load_configs(path)
        assert len(configs) >= 9
        names = {c.name for c in configs}
        assert "SHRINK_BATCH" in names
        assert "tcp_cubic" in names

    def test_frozen_dataclass(self, project_root):
        path = os.path.join(project_root, 'tunables', 'shrink_batch.toml')
        if not os.path.exists(path):
            pytest.skip("shrink_batch.toml not found")
        _, config = load_config(path)
        with pytest.raises(AttributeError):
            config.name = "mutated"
