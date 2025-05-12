import pickle
import os
from app.ml.training_engine import VulnLearnAIEngine

def load_model_and_vectorizer(model_path, vectorizer_path):
    with open(model_path, "rb") as model_file:
        classifier = pickle.load(model_file)
    with open(vectorizer_path, "rb") as vectorizer_file:
        vectorizer = pickle.load(vectorizer_file)
    return classifier, vectorizer

def test_logic_update():
    sample_inputs = [
        "Critical vulnerability in web application allowing remote code execution",
        "Reflected XSS vulnerability in the search bar of the application",
        "Buffer overflow in file upload module leading to arbitrary code execution",
        "SQL injection in login form allowing attackers to bypass authentication",
        "Low severity issue with improper error handling in API responses"
    ]

    # Paths to the latest model and vectorizer before training
    model_dir = "data/model"
    models = sorted([f for f in os.listdir(model_dir) if f.startswith("classifier_")])
    vectorizers = sorted([f for f in os.listdir(model_dir) if f.startswith("vectorizer_")])

    if not models or not vectorizers:
        print("No existing models found. Please train the model first.")
        return

    # Load the latest model and vectorizer before training
    classifier_before, vectorizer_before = load_model_and_vectorizer(
        os.path.join(model_dir, models[-1]), os.path.join(model_dir, vectorizers[-1])
    )

    # Make predictions before training
    print("Predictions before training:")
    for input_text in sample_inputs:
        X_before = vectorizer_before.transform([input_text])
        prediction_before = classifier_before.predict(X_before)
        print(f"Input: {input_text}\nPrediction: {prediction_before[0]}\n")

    # Train the model
    engine = VulnLearnAIEngine()
    engine.train_model()

    # Load the latest model and vectorizer after training
    models = sorted([f for f in os.listdir(model_dir) if f.startswith("classifier_")])
    vectorizers = sorted([f for f in os.listdir(model_dir) if f.startswith("vectorizer_")])
    classifier_after, vectorizer_after = load_model_and_vectorizer(
        os.path.join(model_dir, models[-1]), os.path.join(model_dir, vectorizers[-1])
    )

    # Make predictions after training
    print("Predictions after training:")
    for input_text in sample_inputs:
        X_after = vectorizer_after.transform([input_text])
        prediction_after = classifier_after.predict(X_after)
        print(f"Input: {input_text}\nPrediction: {prediction_after[0]}\n")

if __name__ == "__main__":
    test_logic_update()
