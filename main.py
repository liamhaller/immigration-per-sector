"""
Data Science Pipeline Template

Main entry point for running various data analysis pipelines.
Add your own pipelines by following the example pattern below.
"""

from pathlib import Path
import sys
from datetime import datetime
import importlib.util # Use absoulte paths to avoid conflicts in larger projects (ORACLE)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from Tools import get_logger

logger = get_logger(__name__)


def run_example_pipeline():
    """
    BLS PPI Analysis Pipeline.

    This pipeline demonstrates the standard 3-Step structure:
    1. Data Collection (BLS API calls)
    2. Data Processing (filter and clean PPI data)
    3. Analysis and Output (top 5 NAICS with largest PPI increases)
    """

    logger.info("=" * 80)
    logger.info("BLS PPI ANALYSIS PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: Data Collection
        logger.info("Step 1: Data Collection")
        logger.info("-" * 40)

        # Import BLS API call module
        bls_path = importlib.util.spec_from_file_location(
            "example_bls",                               # Name
            project_root / "APICalls" / "example_bls.py" # Location
        )
        bls_module = importlib.util.module_from_spec(bls_path)
        bls_path.loader.exec_module(bls_module)
        bls_module.main()

        # Step 2: Data Processing
        logger.info("Step 2: Data Processing")
        logger.info("-" * 40)
        # Import BLS processing module
        processor_path = importlib.util.spec_from_file_location(
            "process_bls_ppi",                                      # Name
            project_root / "DataProcessing" / "process_bls_ppi.py"  # Location
        )
        processor_module = importlib.util.module_from_spec(processor_path)
        processor_path.loader.exec_module(processor_module)
        processor_module.main()

        # Step 3: Analysis
        logger.info("Step 3: Analysis")
        logger.info("-" * 40)
        # Import PPI analysis module
        analysis_path = importlib.util.spec_from_file_location(
            "ppi_increase_analysis",
            project_root / "Analysis" / "ppi_increase_analysis.py"
        )
        analysis_module = importlib.util.module_from_spec(analysis_path)
        analysis_path.loader.exec_module(analysis_module)
        analysis_module.main()

        logger.info("=" * 80)
        logger.info("BLS PPI PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Output files saved to:")
        logger.info("  • Raw data: Data/raw/pc/")
        logger.info("  • Processed data: Data/processed/three_digit_ppi.csv")
        logger.info("  • Analysis results: output/ppi_increase_analysis/[timestamp]/")

        return True

    except Exception as e:
        logger.error("=" * 80)
        logger.error("BLS PPI PIPELINE FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error("Please check the error message above and try again.")
        return False


def run_quarto_report():
    """
    Generate Quarto PDF Report.

    Runs the self-contained Quarto notebook that executes the full pipeline
    and generates a publication-ready PDF report with charts and tables.
    """

    logger.info("=" * 80)
    logger.info("QUARTO REPORT GENERATION")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        import subprocess
        import os

        # Change to Chartbook directory
        chartbook_dir = project_root / "Chartbook"
        original_dir = os.getcwd()
        os.chdir(chartbook_dir)

        logger.info("Rendering Quarto notebook to PDF...")
        result = subprocess.run([
            "uv", "run", "quarto", "render", "example_chartbook.qmd", "--to", "pdf"
        ], capture_output=True, text=True, cwd=chartbook_dir)

        # Change back to original directory
        os.chdir(original_dir)

        if result.returncode == 0:
            logger.info("=" * 80)
            logger.info("QUARTO REPORT COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("PDF report generated:")
            logger.info(f"  • {chartbook_dir / 'example_chartbook.pdf'}")
            return True
        else:
            logger.error("Quarto rendering failed:")
            logger.error(result.stderr)
            return False

    except Exception as e:
        logger.error("=" * 80)
        logger.error("QUARTO REPORT FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return False


def show_pipeline_menu():
    """Display available pipeline options."""
    print("\n" + "=" * 60)
    print("DATA SCIENCE ANALYSIS PIPELINES")
    print("=" * 60)
    print("Available Analysis Options:")
    print("1. Example Pipeline (demonstrates template structure)")
    print("2. Generate Chartbook")
    print("0. Exit")
    print("-" * 60)


def get_user_choice():
    """Get and validate user menu choice."""
    while True:
        try:
            choice = input("Please select an option (0-2): ").strip()
            if choice in ['0', '1', '2']:
                return choice
            else:
                print("Invalid choice. Please enter 0, 1, or 2.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return '0'
        except EOFError:
            print("\n\nExiting...")
            return '0'


def main():
    """
    Main entry point for the data science pipeline system.

    Provides an interactive menu for selecting different pipeline types.
    """

    # Ensure we're in the correct directory
    project_root = Path(__file__).parent
    if project_root != Path.cwd():
        import os
        os.chdir(project_root)

    print("Welcome to the [Project Name] Pipeline")

    while True:
        show_pipeline_menu()
        choice = get_user_choice()

        if choice == '0':
            print("\nGoodbye!")
            return 0

        elif choice == '1':
            print("\nRunning Example Pipeline...")
            success = run_example_pipeline()
            if success:
                print("\nExample pipeline completed successfully!")
            else:
                print("\nExample pipeline failed. Check error messages above.")

        elif choice == '2':
            print("\nGenerating Quarto Report...")
            success = run_quarto_report()
            if success:
                print("\nQuarto report generated successfully!")
                print("Check Chartbook/example_chartbook.pdf")
            else:
                print("\nQuarto report generation failed. Check error messages above.")

        # Ask if user wants to run another pipeline
        while True:
            continue_choice = input("\nWould you like to run another analysis? (y/n): ").strip().lower()
            if continue_choice in ['y', 'yes']:
                break
            elif continue_choice in ['n', 'no']:
                print("\nGoodbye!")
                return 0 if success else 1
            else:
                print("Please enter 'y' for yes or 'n' for no.")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
