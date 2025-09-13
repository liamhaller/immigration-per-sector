from pathlib import Path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Tools import create_analysis_session

# Create analysis session using convenience function
session = create_analysis_session('example_analysis')

# AnalysisSession creates timestamped output directories for organizing analysis results
# Use session.dir to save files directly: df.to_csv(session.dir / 'data.csv'), fig.savefig(session.dir / 'plot.png')
# Use session.save() for text content: session.save('summary.txt', results_text) -- avoid opening/closing files
# All outputs are saved to output/analysis_name/YYYY-MM-DD_HH-MM-SS/