import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# ===============================
# Load dataset
# ===============================
df = pd.read_csv("satcom_training_dataset.csv")

# ===============================
# Selected physics + geometry features
# (DO NOT randomly change order later)
# ===============================
FEATURES = [
    "orbit_type_enc",
    "sat_altitude_km",
    "distance_km",
    "distance_log",
    "elevation",
    "sin_elevation",
    "cos_elevation",
    "doppler_hz",
    "fspl_db",
    "atm_loss_db",
    "rx_power_dbm",
    "rx_margin",
    "gs_lat",
    "gs_lon"
]

LABEL = "visible"

X = df[FEATURES]
y = df[LABEL]

# ===============================
# Train / Test split
# ===============================
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# ===============================
# Train model
# ===============================
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=5,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

model.fit(X_train, y_train)

# ===============================
# Evaluate
# ===============================
y_pred = model.predict(X_test)

print("\nModel Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# ===============================
# Save artifacts
# ===============================
joblib.dump(model, "visibility_model.pkl")
joblib.dump(FEATURES, "model_features.pkl")

print("\n✅ Model saved as visibility_model.pkl")
print("✅ Feature list saved as model_features.pkl")

