import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
from app.core.config import settings

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    crops = ['Tomato', 'Onion', 'Potato', 'Wheat', 'Rice']
    regions = ['Nashik', 'Pune', 'Mumbai', 'Nagpur', 'Aurangabad']
    
    data = []
    for _ in range(num_samples):
        crop = np.random.choice(crops)
        region = np.random.choice(regions)
        horizon = np.random.randint(1, 30)
        
        # Simulate some logic for demand
        base_demand = np.random.randint(1, 100)
        if crop == 'Tomato' and horizon < 7:
            base_demand += 50
        elif region == 'Mumbai':
            base_demand += 30
            
        if base_demand > 100:
            level = 'HIGH'
        elif base_demand > 50:
            level = 'MEDIUM'
        else:
            level = 'LOW'
            
        data.append({
            'crop_encoded': crops.index(crop),
            'region_encoded': regions.index(region),
            'horizon_days': horizon,
            'demand_level': level
        })
        
    return pd.DataFrame(data)

def train_model():
    print("Generating synthetic dataset...")
    df = generate_synthetic_data(2000)
    
    X = df[['crop_encoded', 'region_encoded', 'horizon_days']]
    y = df['demand_level']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest model...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    os.makedirs(settings.models_dir, exist_ok=True)
    model_path = os.path.join(settings.models_dir, "demand_rf_model.joblib")
    
    print(f"Saving model to {model_path}...")
    joblib.dump(clf, model_path)
    print("Training complete.")

if __name__ == "__main__":
    # Ensure this runs nicely when called directly
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    train_model()
