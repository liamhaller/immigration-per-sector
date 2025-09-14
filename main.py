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


def run_immigration_analysis_pipeline():
    """
    Immigration Growth Analysis Pipeline.

    This pipeline analyzes the relationship between immigration workforce
    composition and economic growth across industries using Census PUMS
    and BLS data. Follows the standard 3-Step structure:

    1. Data Collection (Census PUMS and BLS API calls)
    2. Data Processing (process PUMS → process BLS → join → create analysis datasets)
    3. Analysis and Output (visualizations and correlation analysis)
    """

    logger.info("=" * 80)
    logger.info("IMMIGRATION GROWTH ANALYSIS PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: Data Collection
        logger.info("Step 1: Data Collection")
        logger.info("-" * 40)

        # Import Census PUMS API call module
        logger.info("Downloading Census PUMS immigration data...")
        pums_path = importlib.util.spec_from_file_location(
            "census_pums_immigration",
            project_root / "APICalls" / "census_pums_immigration.py"
        )
        pums_module = importlib.util.module_from_spec(pums_path)
        pums_path.loader.exec_module(pums_module)
        pums_module.main()

        # Import BLS API call module
        logger.info("Downloading BLS employment and earnings data...")
        bls_path = importlib.util.spec_from_file_location(
            "example_bls",
            project_root / "APICalls" / "example_bls.py"
        )
        bls_module = importlib.util.module_from_spec(bls_path)
        bls_path.loader.exec_module(bls_module)
        bls_module.main()

        # Step 2: Data Processing
        logger.info("Step 2: Data Processing")
        logger.info("-" * 40)

        # Process PUMS immigration data
        logger.info("Processing PUMS immigration data...")
        process_pums_path = importlib.util.spec_from_file_location(
            "process_pums_immigration",
            project_root / "DataProcessing" / "process_pums_immigration.py"
        )
        process_pums_module = importlib.util.module_from_spec(process_pums_path)
        process_pums_path.loader.exec_module(process_pums_module)
        process_pums_module.main()

        # Process BLS data
        logger.info("Processing BLS employment and earnings data...")
        process_bls_path = importlib.util.spec_from_file_location(
            "process_bls_ppi",
            project_root / "DataProcessing" / "process_bls_ppi.py"
        )
        process_bls_module = importlib.util.module_from_spec(process_bls_path)
        process_bls_path.loader.exec_module(process_bls_module)
        process_bls_module.main()

        # Join PUMS and BLS NAICS codes
        logger.info("Joining PUMS and BLS NAICS codes...")
        join_path = importlib.util.spec_from_file_location(
            "join_pums_bls_naics",
            project_root / "DataProcessing" / "join_pums_bls_naics.py"
        )
        join_module = importlib.util.module_from_spec(join_path)
        join_path.loader.exec_module(join_module)
        join_module.main()

        # Create employment and earnings analysis datasets
        logger.info("Creating employment and earnings analysis datasets...")
        analysis_data_path = importlib.util.spec_from_file_location(
            "create_employment_earnings_immigration_analysis",
            project_root / "DataProcessing" / "create_employment_earnings_immigration_analysis.py"
        )
        analysis_data_module = importlib.util.module_from_spec(analysis_data_path)
        analysis_data_path.loader.exec_module(analysis_data_module)
        analysis_data_module.main()

        # Step 3: Analysis
        logger.info("Step 3: Analysis")
        logger.info("-" * 40)

        # Run immigration growth analysis and create visualizations
        logger.info("Creating immigration growth analysis and visualizations...")
        analysis_path = importlib.util.spec_from_file_location(
            "immigration_growth_analysis",
            project_root / "Analysis" / "immigration_growth_analysis.py"
        )
        analysis_module = importlib.util.module_from_spec(analysis_path)
        analysis_path.loader.exec_module(analysis_module)
        analysis_module.main()

        logger.info("=" * 80)
        logger.info("IMMIGRATION GROWTH ANALYSIS PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Output files saved to:")
        logger.info("  • Raw data: Data/raw/")
        logger.info("  • Processed data: Data/processed/")
        logger.info("  • Analysis results: output/immigration_growth_analysis/[timestamp]/")
        logger.info("  • Charts: Employment growth, earnings growth, and correlation analysis")

        return True

    except Exception as e:
        logger.error("=" * 80)
        logger.error("IMMIGRATION GROWTH ANALYSIS PIPELINE FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error("Please check the error message above and try again.")
        return False





def show_pipeline_menu():
    """Display available pipeline options."""
    print("\n" + "=" * 60)
    print("IMMIGRATION GROWTH ANALYSIS PIPELINE")
    print("=" * 60)
    print("Available Options:")
    print("1. Run Immigration Analysis")
    print("0. Exit")
    print("-" * 60)


def get_user_choice():
    """Get and validate user menu choice."""
    while True:
        try:
            choice = input("Please select an option (0-1): ").strip()
            if choice in ['0', '1']:
                return choice
            else:
                print("Invalid choice. Please enter 0 or 1.")
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

    print("Welcome to the Immigration Growth Analysis Pipeline")

    while True:
        show_pipeline_menu()
        choice = get_user_choice()

        if choice == '0':
            print("\nGoodbye!")
            return 0

        elif choice == '1':
            print("\nRunning Immigration Growth Analysis Pipeline...")
            success = run_immigration_analysis_pipeline()
            if success:
                print("\nImmigration analysis pipeline completed successfully!")
                print("Check output/immigration_growth_analysis/[timestamp]/ for results")
            else:
                print("\nImmigration analysis pipeline failed. Check error messages above.")

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
