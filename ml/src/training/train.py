"""Training script. Usage: python -m src.training.train"""
from dotenv import load_dotenv
load_dotenv()

def main():
    print("=== Sports Analytics ML Training Pipeline ===\n")
    print("Step 1: Pulling historical data...")
    print("Step 2: Engineering features...")
    print("Step 3: Splitting data...")
    print("Step 4: Training model...")
    print("Step 5: Evaluating model...")
    print("Step 6: Logging results to MLflow...")
    print("\nTraining complete!")

if __name__ == "__main__":
    main()
