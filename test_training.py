from app.ml.training_engine import VulnLearnAIEngine

def test_training():
    engine = VulnLearnAIEngine()
    try:
        result = engine.train_model()
        print("Training completed successfully.")
        print("Validation Accuracy:", result["validation_accuracy"])
        print("Training Samples:", result["training_samples"])
    except ValueError as e:
        print("Error during training:", e)
    except Exception as e:
        print("Unexpected error:", e)

if __name__ == "__main__":
    test_training()
