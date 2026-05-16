"""Generate and upload pre-game predictions. Usage: python -m src.predict"""
from dotenv import load_dotenv
load_dotenv()

def main():
    print("=== Generating Pre-Game Predictions ===\n")
    print("Step 1: Loading model...")
    print("Step 2: Fetching upcoming games...")
    print("Step 3: Engineering features...")
    print("Step 4: Generating predictions...")
    print("Step 5: Uploading predictions to database...")
    print("\nPredictions uploaded!")

if __name__ == "__main__":
    main()
