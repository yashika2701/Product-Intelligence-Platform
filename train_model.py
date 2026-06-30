import sqlite3
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, classification_report

def train():
    print("Connecting to marketplace.db...")
    conn = sqlite3.connect("marketplace.db")
    
    # Feature extraction SQL query
    # Extracts sessions where items were added to the cart,
    # capturing the session details, discount, past purchase count,
    # and whether the device is iOS (is_ios = 1) or not (is_ios = 0).
    query = """
        SELECT 
            s.session_id,
            s.session_duration,
            COUNT(CASE WHEN e.event_type = 'View Product' THEN 1 END) as num_products_viewed,
            COUNT(CASE WHEN e.event_type = 'Add To Cart' THEN 1 END) as items_added_to_cart,
            s.discount_coupon_applied,
            (
                SELECT COUNT(*) 
                FROM orders o 
                WHERE o.user_id = s.user_id 
                  AND o.order_date < s.session_date
            ) as past_purchases_count,
            CASE WHEN s.device_type = 'iOS' THEN 1 ELSE 0 END as is_ios,
            CASE WHEN COUNT(CASE WHEN e.event_type = 'Purchase' THEN 1 END) > 0 THEN 0 ELSE 1 END as abandoned
        FROM sessions s
        LEFT JOIN events e ON s.session_id = e.session_id
        GROUP BY s.session_id, s.session_duration, s.discount_coupon_applied, s.user_id, s.session_date, s.device_type
        HAVING COUNT(CASE WHEN e.event_type = 'Add To Cart' THEN 1 END) > 0;
    """
    
    print("Loading training features from database...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Extracted {len(df)} sessions with shopping carts.")
    
    # Define features and target label
    feature_cols = [
        'session_duration', 
        'num_products_viewed', 
        'items_added_to_cart', 
        'past_purchases_count', 
        'discount_coupon_applied',
        'is_ios'
    ]
    
    X = df[feature_cols]
    y = df['abandoned']
    
    print("\nFeature Matrix Sample:")
    print(X.head())
    print("\nTarget Label Distribution (1 = Abandoned, 0 = Purchased):")
    print(y.value_counts(normalize=True))
    
    # Split train/test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Define sklearn pipeline
    print("\nInitializing Random Forest Pipeline...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100, 
            max_depth=6, 
            random_state=42, 
            class_weight='balanced'
        ))
    ])
    
    # Fit model
    print("Fitting model to training split...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print("            MODEL PERFORMANCE METRICS")
    print("="*50)
    print(f"Accuracy Score: {acc*100:.2f}%")
    print(f"F1-Score      : {f1*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Enforce quality thresholds specified in the non-functional requirements
    assert acc >= 0.80, f"Validation failure: Accuracy {acc:.2f} is below the 80% threshold."
    assert f1 >= 0.80, f"Validation failure: F1-score {f1:.2f} is below the 80% threshold."
    print("[SUCCESS] Quality thresholds satisfied (Accuracy & F1-score >= 80%).")
    
    # Serialize model pipeline
    print("\nSaving model pipeline to cart_model.pkl...")
    with open("cart_model.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    print("Model serialized and saved successfully!")

if __name__ == "__main__":
    train()
