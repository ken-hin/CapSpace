"""Model training entrypoint.

Run as a script (``python -m src.training.train``) to execute the full training
pipeline: pull historical data, engineer features, split into train/test, fit
the model, evaluate it, and log results to MLflow. Currently a scaffold that
prints each pipeline step; the steps are placeholders to be implemented.
"""
from dotenv import load_dotenv

# Load environment variables (e.g. DATABASE_URL, MLflow tracking URI) from .env.
load_dotenv()

def main():
    """Run the end-to-end training pipeline.

    Walks through data pull, feature engineering, train/test split, model fit,
    evaluation, and MLflow logging. The body is currently a stub that prints each
    step.
    """
    print("=== Sports Analytics ML Training Pipeline ===\n")
    print("Step 1: Pulling historical data...")
    print("Step 2: Engineering features...")
    print("Step 3: Splitting data...")
    print("Step 4: Training model...")
    print("Step 5: Evaluating model...")
    print("Step 6: Logging results to MLflow...")
    print("\nTraining complete!")

if __name__ == "__main__":
    # Allow running this module directly as a script.
    main()
