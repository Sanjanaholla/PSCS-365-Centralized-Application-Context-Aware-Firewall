import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Tuple

# --- Configuration ---
RANDOM_SEED = 42
N_SAMPLES = 1000
ANOMALY_FRACTION = 0.03


def generate_mock_network_data() -> pd.DataFrame:
    """Generates a synthetic dataset for network traffic analysis."""
    print("Generating synthetic network data...")

    # Generate 'Normal' Data
    normal_duration = np.random.normal(loc=15, scale=5, size=int(N_SAMPLES * (1 - ANOMALY_FRACTION)))
    normal_size = np.random.normal(loc=1500, scale=200, size=int(N_SAMPLES * (1 - ANOMALY_FRACTION)))
    normal_ports = np.random.choice([80, 443, 22, 53, 3389], size=int(N_SAMPLES * (1 - ANOMALY_FRACTION)))

    normal_data = pd.DataFrame({
        'connection_duration': normal_duration.clip(min=1),
        'packet_size': normal_size.clip(min=500),
        'port_number': normal_ports
    })

    # Generate 'Anomalous' Data
    anomaly_duration = np.random.uniform(low=100, high=500, size=int(N_SAMPLES * ANOMALY_FRACTION))
    anomaly_size = np.random.uniform(low=5000, high=15000, size=int(N_SAMPLES * ANOMALY_FRACTION))
    anomaly_ports = np.random.choice(np.arange(1024, 65535), size=int(N_SAMPLES * ANOMALY_FRACTION))

    anomaly_data = pd.DataFrame({
        'connection_duration': anomaly_duration,
        'packet_size': anomaly_size,
        'port_number': anomaly_ports
    })

    data = pd.concat([normal_data, anomaly_data], ignore_index=True).sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    return data


def train_and_detect_anomalies(df: pd.DataFrame) -> Tuple[pd.DataFrame, IsolationForest, StandardScaler]:
    """Trains the Isolation Forest model and performs anomaly detection. Returns results, model, and scaler."""
    features = ['connection_duration', 'packet_size', 'port_number']
    X = df[features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"Data scaled. Total samples: {len(X_scaled)}")

    print("Training Isolation Forest model...")
    model = IsolationForest(
        n_estimators=100,
        contamination=ANOMALY_FRACTION,
        max_samples='auto',
        random_state=RANDOM_SEED,
        verbose=0
    )

    model.fit(X_scaled)
    print("Training complete.")

    anomaly_scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)

    results_df = df.copy()
    results_df['anomaly_score'] = anomaly_scores
    results_df['is_anomaly'] = np.where(predictions == -1, 'Anomaly', 'Normal')

    return results_df, model, scaler


def display_results(results_df: pd.DataFrame):
    """Prints a summary and details of the detected anomalies."""
    print("\n" + "=" * 50)
    print("   ISOLATION FOREST ANOMALY DETECTION RESULTS")
    print("=" * 50)

    anomaly_count = results_df['is_anomaly'].value_counts().get('Anomaly', 0)
    normal_count = results_df['is_anomaly'].value_counts().get('Normal', 0)

    print(f"Total Samples Analyzed: {len(results_df)}")
    print(f"Detected Anomalies (-1): {anomaly_count}")
    print(f"Detected Normal Traffic (+1): {normal_count}")

    print("\nTop 5 Most Anomalous Samples (Lowest Score):")
    top_anomalies = results_df.sort_values(by='anomaly_score').head(5)

    print(top_anomalies[['connection_duration', 'packet_size', 'port_number', 'anomaly_score', 'is_anomaly']].to_string(index=False))


if __name__ == "__main__":
    network_data = generate_mock_network_data()
    analysis_results, iforest_model, scaler = train_and_detect_anomalies(network_data)
    display_results(analysis_results)

    print("The trained model can be saved and integrated into the FastAPI service for real-time scoring.")

    # Ensure models directory exists at project root
    models_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(models_dir, exist_ok=True)

    import joblib
    # Save model and scaler in the models/ folder at project root
    joblib.dump(iforest_model, os.path.join(models_dir, "iforest.joblib"))
    joblib.dump(scaler, os.path.join(models_dir, "scaler.joblib"))
    print(f"Model and scaler saved in {models_dir}/")


data_dir = os.path.join(os.getcwd(), "data")
os.makedirs(data_dir, exist_ok=True)

csv_path = os.path.join(data_dir, "network_dataset.csv")
network_data.to_csv(csv_path, index=False)

print(f"Dataset saved at: {csv_path}")


