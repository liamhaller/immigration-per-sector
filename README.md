# Greenmantle Data Science Template

## Quick Start
1. **Set up uv (if already installed)** `uv venv --seed`
2. **Activate venv**: `source .venv/bin/activate` (On Windows: `.venv\Scripts\activate`)
3. **Install dependencies**: `uv sync`
4. **Run the example pipeline**: `uv run main.py` and select option 1
5. **Check timestamped outputs** in `output/` and `Output/logs/`
6. **Modify existing modules** or add new ones following the established patterns

# Setup

## 1. Install uv (if not already installed)
**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative:** Install via pip
```bash
pip install uv
```

## 2. Create New Project from Template

**Use GitHub's "Use this template" button - don't clone this repository directly.**

```bash
# After creating your new repository from the template
git clone <your-new-repository-url>
cd your-project-name

# Create virtual environment with pip/setuptools for compatibility
uv venv --seed
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies (creates uv.lock if it doesn't exist)
uv sync

# Note: Only the Tools/ folder is installed as an importable package.
# All reusable utility functions should be placed in Tools/
```

## 3. Managing Dependencies

### Adding/removing Dependencies
```bash
# Add a new dependency (updates pyproject.toml and uv.lock)
uv add pandas numpy matplotlib

# Add from specific sources
uv add "requests>=2.25.0"
uv add git+https://github.com/user/repo.git
```

```bash
# Remove dependencies
uv remove pandas matplotlib

```

### Syncing Dependencies
```bash
# Install/update all dependencies from uv.lock
# Run this after cloning or when uv.lock changes
uv sync

# Update all dependencies to latest compatible versions
uv sync --upgrade
```

**Key Points:**
- `uv add/remove` automatically updates both `pyproject.toml` and `uv.lock`
- `uv sync` installs exact versions from `uv.lock` for reproducible environments
- `uv sync --upgrade` updates dependencies to latest compatible versions (useful when starting new projects from template)
- Always commit both `pyproject.toml` and `uv.lock` to version control

# Using This Template
## 1. Path Management
The template includes centralized path management through `Tools/path_management.py`. Always use this standard import pattern:

```python
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import raw_data_dir, processed_data_dir, data_dir, get_logger

logger = get_logger(__name__)
```

Example usage:
```python
import pandas as pd
from Tools import raw_data_dir, processed_data_dir

# Save raw API response
raw_file = raw_data_dir / "census_trade_2024.csv"
raw_df.to_csv(raw_file)

# Save processed data
cleaned_file = processed_data_dir / "trade_cleaned.csv"
processed_df.to_csv(cleaned_file)
```

## 2. Logging
All scripts (excluding quarto analysis) should use the centralized logging system:

```python
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import get_logger

logger = get_logger(__name__)

# Now use logger.info(), logger.error(), etc.
logger.info("Starting analysis...")
```

## 3. Saving Analysis
Use `AnalysisSession` for organized, timestamped outputs:

```python
from Tools import create_analysis_session

# Create session at module level
session = create_analysis_session("my_analysis")

# Save files to organized directory
session.dir  # Returns: Output/my_analysis/2025-08-13_15-30-45/
chart_path = session.dir / "my_chart.png"
plt.savefig(chart_path)
```

## 4. Module Loading (main.py)
The pipeline system uses `importlib.util.spec_from_file_location()` instead of standard imports:

```python
# Instead of: import DataProcessing.my_module
# Use robust loading:
import importlib.util
spec = importlib.util.spec_from_file_location(
    "my_module",
    project_root / "DataProcessing" / "my_module.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.main()
```
- This is to avoid conflicts when template is used in larger projects (ORACLE)


# Resources
**U.S. Census**
-  [Trade API](https://www.census.gov/foreign-trade/api_tool.html)
-  [Buisness & Industry](https://www.census.gov/econ_datasets/ ) 
**Bureau of Labor Statistics**
- [Survey data (flat files)](https://download.bls.gov/pub/time.series/) 
- [Economic Indicators (manufacturing, trade, wholesale)](https://www.census.gov/econ_datasets/ ) 
**Official Japan Statistics e-Stat** 
- [E-Stat](https://www.e-stat.go.jp/en/stat-search/database?page=1&query=export&layout=dataset)


