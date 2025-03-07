import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
import os
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../train_model.log"),
        logging.StreamHandler()
    ]
)

def load_data(file_path: str) -> tuple:
    """Load and validate the training data from a CSV file."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Training data file not found at {full_path}")
        data = pd.read_csv(full_path)
        if 'text' not in data.columns or 'is_important' not in data.columns:
            raise ValueError("CSV file must contain 'text' and 'is_important' columns")
        if not pd.api.types.is_numeric_dtype(data['is_important']):
            data['is_important'] = data['is_important'].astype(int)
        logging.info(f"Loaded {len(data)} records from {full_path}")
        return data['text'].values, data['is_important'].values
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def train_model(X: np.ndarray, y: np.ndarray) -> tuple:
    """Train a logistic regression model with TF-IDF features and perform cross-validation."""
    try:
        vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        X_tfidf = vectorizer.fit_transform(X)
        logging.info("TF-IDF vectorization completed")

        X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.1, random_state=42)
        logging.info(f"Data split: {X_train.shape[0]} training samples, {X_test.shape[0]} test samples")

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)
        logging.info("Model training completed")

        y_pred = model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        logging.info(f"Test set accuracy: {test_accuracy:.4f}")
        logging.info("Classification Report:\n" + classification_report(y_test, y_pred, zero_division=0))

        class_counts = Counter(y)
        min_class_size = min(class_counts.values())
        cv_folds = min(5, min_class_size)
        logging.info(f"Using {cv_folds} folds for cross-validation (min class size: {min_class_size})")
        cv_scores = cross_val_score(model, X_tfidf, y, cv=cv_folds)
        logging.info(f"Cross-validation scores: {cv_scores}")
        logging.info(f"Mean CV score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        return model, vectorizer
    except Exception as e:
        logging.error(f"Error during model training: {str(e)}")
        raise

def save_model(model, vectorizer, model_path: str, vectorizer_path: str) -> None:
    """Save the trained model and vectorizer to disk."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_full_path = os.path.join(script_dir, model_path)
        vectorizer_full_path = os.path.join(script_dir, vectorizer_path)
        joblib.dump(model, model_full_path)
        joblib.dump(vectorizer, vectorizer_full_path)
        logging.info(f"Model saved to {model_full_path}")
        logging.info(f"Vectorizer saved to {vectorizer_full_path}")
    except Exception as e:
        logging.error(f"Error saving model or vectorizer: {str(e)}")
        raise

def main():
    """Main function to orchestrate the training process."""
    data_file = "training_data.csv"
    model_file = "ml_model.joblib"
    vectorizer_file = "tfidf_vectorizer.joblib"

    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml"), exist_ok=True)

    X, y = load_data(data_file)
    model, vectorizer = train_model(X, y)
    save_model(model, vectorizer, model_file, vectorizer_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Training process failed: {str(e)}")
        exit(1)