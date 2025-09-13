"""
  Simple Timestamped Analysis Session Template

  Bare bones infrastructure for saving analysis outputs to timestamped folders.
  """

from pathlib import Path
from datetime import datetime

class AnalysisSession:
    """
    Simple timestamped session directory manager.
    
    Usage:
    ------
    with AnalysisSession('my_analysis') as session:
        # Save anything you want to session.dir
        fig.savefig(session.dir / 'my_plot.png')
        df.to_csv(session.dir / 'my_data.csv')
        
        # Or use the simple save method
        session.save('results.txt', my_content)
    """

    def __init__(self, analysis_name, base_output_path='output'):
        self.analysis_name = analysis_name
        self.base_output_path = Path(base_output_path)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.dir = self.base_output_path / analysis_name / self.timestamp
        self._created = False

    def _ensure_dir(self):
        """Create the session directory if it doesn't exist."""
        if not self._created:
            self.dir.mkdir(parents=True, exist_ok=True)
            print(f"Analysis session: {self.timestamp}")
            print(f"Results will be saved to: {self.dir}")
            self._created = True

    def save(self, filename, content):
        """
        Simple save method for text/string content.
        
        Parameters:
        -----------
        filename : str
            Name of file to save
        content : str
            Content to write to file
        """
        self._ensure_dir()
        filepath = self.dir / filename
        with open(filepath, 'w') as f:
            f.write(str(content))
        print(f"Saved: {filepath}")
        return filepath

    def __enter__(self):
        self._ensure_dir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._created:
            print(f"Analysis session completed: {self.dir}")

# Convenience function
def create_analysis_session(analysis_name, base_output_path='output'):
    """Create a new timestamped analysis session."""
    session = AnalysisSession(analysis_name, base_output_path)
    session._ensure_dir()  # Create directory immediately
    return session

"""
# Example usage
if __name__ == "__main__":
    import pandas as pd
    import matplotlib.pyplot as plt

    with AnalysisSession('example_analysis') as session:
        # Create some data and plot
        df = pd.DataFrame({'x': [1,2,3,4], 'y': [2,4,1,3]})

        fig, ax = plt.subplots()
        ax.plot(df['x'], df['y'])
        ax.set_title('Example Plot')

        # Save directly to session.dir (you handle the specifics)
        fig.savefig(session.dir / 'plot.png', dpi=300, bbox_inches='tight')
        df.to_csv(session.dir / 'data.csv', index=False)

        # Or use the simple save helper for text content
        results_summary = f"Analysis completed with {len(df)} data points"
        session.save('summary.txt', results_summary)

        plt.close(fig)
"""