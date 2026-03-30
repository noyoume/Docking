"""Configuration loading from environment variables and .env files."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # Required paths
    complexes_dir: Path = field(default_factory=lambda: Path("."))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    adfr_python: Path = field(default_factory=lambda: Path("python"))
    adfr_prep_receptor: Path = field(default_factory=lambda: Path("prepare_receptor4.py"))

    # Docking parameters
    exhaustiveness: int = 8
    num_modes: int = 10
    num_runs: int = 10
    vina_cpu: int = 0
    energy_range: float = 5.0
    vina_timeout: int = 600
    grid_padding: float = 3.0
    max_grid_size: float = 126.0

    # Production features
    skip_existing: bool = True
    fail_log: str = "failures.csv"

    @classmethod
    def from_env(cls) -> "Config":
        """Build Config from VINADOCK_* environment variables."""
        def _path(key, default=""):
            return Path(os.environ.get(key, default))

        def _int(key, default):
            return int(os.environ.get(key, default))

        def _float(key, default):
            return float(os.environ.get(key, default))

        def _bool(key, default):
            val = os.environ.get(key, str(default)).lower()
            return val in ("true", "1", "yes")

        cfg = cls(
            complexes_dir=_path("VINADOCK_COMPLEXES_DIR", "."),
            output_dir=_path("VINADOCK_OUTPUT_DIR", "output"),
            adfr_python=_path("VINADOCK_ADFR_PYTHON", "python"),
            adfr_prep_receptor=_path("VINADOCK_ADFR_PREP_RECEPTOR", "prepare_receptor4.py"),
            exhaustiveness=_int("VINADOCK_EXHAUSTIVENESS", 8),
            num_modes=_int("VINADOCK_NUM_MODES", 10),
            num_runs=_int("VINADOCK_NUM_RUNS", 10),
            vina_cpu=_int("VINADOCK_VINA_CPU", 0),
            energy_range=_float("VINADOCK_ENERGY_RANGE", 5.0),
            vina_timeout=_int("VINADOCK_VINA_TIMEOUT", 600),
            grid_padding=_float("VINADOCK_GRID_PADDING", 3.0),
            max_grid_size=_float("VINADOCK_MAX_GRID_SIZE", 126.0),
            skip_existing=_bool("VINADOCK_SKIP_EXISTING", True),
            fail_log=os.environ.get("VINADOCK_FAIL_LOG", "failures.csv"),
        )
        return cfg

    def validate(self):
        """Check that required paths exist."""
        errors = []
        if not self.complexes_dir.is_dir():
            errors.append(f"VINADOCK_COMPLEXES_DIR not found: {self.complexes_dir}")
        if not self.adfr_python.exists():
            errors.append(f"VINADOCK_ADFR_PYTHON not found: {self.adfr_python}")
        if not self.adfr_prep_receptor.exists():
            errors.append(f"VINADOCK_ADFR_PREP_RECEPTOR not found: {self.adfr_prep_receptor}")
        if errors:
            raise ValueError("\n".join(errors))


def load_env_file(path: str):
    """Read a .env file and update os.environ."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ[key] = value
