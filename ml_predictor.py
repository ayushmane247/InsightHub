import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    classification_report, accuracy_score,
    mean_squared_error, r2_score
)

# 🔍 Determine if task is classification or regression
def is_classification(target_series):
    return target_series.dtype == "object" or len(target_series.unique()) < 15

# 🧹 Preprocess dataset
def preprocess_data(df, target_column):
    df = df.dropna(subset=[target_column])
    df = df.dropna(axis=1, thresh=int(0.7 * len(df)))  # Drop columns with >30% missing
    df = df.dropna()  # Drop rows with any missing values

    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Convert categorical features
    X_encoded = pd.get_dummies(X, drop_first=True)

    return X_encoded, y

# 🤖 Train Random Forest model
def train_model(X, y, classification=True):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier() if classification else RandomForestRegressor()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return model, X_test, y_test, y_pred

# 📊 Show prediction results
def show_metrics(y_test, y_pred, classification=True):
    st.subheader("📈 Prediction Results")

    if classification:
        st.write("### Classification Report:")
        st.text(classification_report(y_test, y_pred))
        st.metric("Accuracy", f"{accuracy_score(y_test, y_pred) * 100:.2f}%")
    else:
        st.write("### Regression Metrics:")
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        st.metric("MSE", f"{mse:.2f}")
        st.metric("R² Score", f"{r2:.2f}")

    # Show Actual vs Predicted
    st.write("### Predicted vs Actual:")
    results = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})
    st.dataframe(results.reset_index(drop=True))

# 🌟 Main ML interface (renamed to ml_predict)
def ml_predict(data):
    st.header("🧠 Machine Learning Prediction")

    if data is None or data.empty:
        st.warning("Please upload and preprocess a dataset first.")
        return

    target_column = st.selectbox("🎯 Select Target Variable", options=data.columns)

    if st.button("🚀 Train Model"):
        try:
            classification = is_classification(data[target_column])
            X, y = preprocess_data(data, target_column)
            _, X_test, y_test, y_pred = train_model(X, y, classification)
            show_metrics(y_test, y_pred, classification)
        except Exception as e:
            st.error(f"❌ Failed to train model: {e}")
