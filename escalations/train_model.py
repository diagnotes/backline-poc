import pandas as pd
import boto3
import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from imblearn.over_sampling import SMOTE

s3 = boto3.client('s3')
bucket = 'escalation-poc'
data_dir = 'escalations/data'

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

train_local = os.path.join(data_dir, 'train.csv')
val_local = os.path.join(data_dir, 'validation.csv')
s3.download_file(bucket, 'data/train/train.csv', train_local)
print(f"Downloaded to {train_local}")
s3.download_file(bucket, 'data/validation/validation.csv', val_local)
print(f"Downloaded to {val_local}")

train_data = pd.read_csv(train_local, header=None)
val_data = pd.read_csv(val_local, header=None)

X_train = train_data.iloc[:, 1:].values.astype(np.float64)
y_train = train_data.iloc[:, 0].values.astype(np.int64)
X_val = val_data.iloc[:, 1:].values.astype(np.float64)
y_val = val_data.iloc[:, 0].values.astype(np.int64)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

selector = SelectKBest(f_classif, k=9)
X_train = selector.fit_transform(X_train, y_train)
X_val = selector.transform(X_val)
print(f"Selected feature indices: {selector.get_support(indices=True)}")

smote = SMOTE(random_state=42, k_neighbors=5)
X_train, y_train = smote.fit_resample(X_train, y_train)
print(f"After SMOTE, samples: {len(y_train)}")
print(f"SMOTE class distribution:\n{pd.Series(y_train).value_counts()}")

print(f"Training samples: {len(X_train)}")
print(f"Validation samples: {len(X_val)}")
print(f"Training classes:\n{pd.Series(y_train).value_counts()}")
print(f"Validation classes:\n{pd.Series(y_val).value_counts()}")

model = RandomForestClassifier(n_estimators=200, max_depth=7, min_samples_split=3, random_state=42, class_weight='balanced')
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='f1_weighted')
print("Cross-Validation F1:", scores)
print("Mean F1:", scores.mean())

model.fit(X_train, y_train)
y_pred = model.predict(X_val)
print("Predicted:", y_pred)
print("True:", y_val)
print("Classification Report:")
print(classification_report(y_val, y_pred, zero_division=0))

model_local = os.path.join(data_dir, 'model.job')
scaler_local = os.path.join(data_dir, 'scaler.job')
selector_local = os.path.join(data_dir, 'selector.job')
joblib.dump(model, model_local)
joblib.dump(scaler, scaler_local)
joblib.dump(selector, selector_local)
print(f"Saved model to {model_local}")
print(f"Saved scaler to {scaler_local}")
print(f"Saved selector to {selector_local}")

s3.upload_file(model_local, bucket, 'model/model.job')
s3.upload_file(scaler_local, bucket, 'model/scaler.job')
s3.upload_file(selector_local, bucket, 'model/selector.job')
print(f"Uploaded to s3://{bucket}/model/")