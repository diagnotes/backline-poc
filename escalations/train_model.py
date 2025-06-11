import pandas as pd
import boto3
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from botocore.exceptions import ClientError

# Initialize S3 client
s3 = boto3.client('s3')
bucket = 'escalation-poc'
data_dir = 'escalations/data'

# Create data directory
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Download training and validation data
train_s3_key = 'data/train/train.csv'
val_s3_key = 'data/validation/validation.csv'
train_local = os.path.join(data_dir, 'train.csv')
val_local = os.path.join(data_dir, 'validation.csv')

try:
    s3.download_file(bucket, train_s3_key, train_local)
    print(f"Downloaded s3://{bucket}/{train_s3_key} to {train_local}")
    s3.download_file(bucket, val_s3_key, val_local)
    print(f"Downloaded s3://{bucket}/{val_s3_key} to {val_local}")
except ClientError as e:
    if e.response['Error']['Code'] == '404':
        print(f"Error: Data not found in S3")
        raise
    else:
        raise e

# Load data
train_data = pd.read_csv(train_local, header=None)
val_data = pd.read_csv(val_local, header=None)

# Split features and target
X_train = train_data.iloc[:, 1:]
y_train = train_data.iloc[:, 0]
X_val = val_data.iloc[:, 1:]
y_val = val_data.iloc[:, 0]

# Check number of samples and class distribution
n_samples = len(y_train)
class_counts = y_train.value_counts()
print(f"Number of training samples: {n_samples}")
print(f"Number of validation samples: {len(y_val)}")
print(f"Training class distribution:\n{class_counts}")
print(f"Validation class distribution:\n{y_val.value_counts()}")

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')

# Try cross-validation with stratified KFold
min_samples_per_class = class_counts.min()
cv = min(5, n_samples, min_samples_per_class)
if cv >= 2:
    try:
        skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
        scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='f1_weighted')
        print("Cross-Validation F1 Scores:", scores)
        print("Mean F1 Score:", scores.mean())
        print("Standard Deviation:", scores.std())
    except ValueError as e:
        print(f"Cross-validation failed: {e}")
        cv = 1
else:
    print("Too few samples or class members for cross-validation")

# Train final model
model.fit(X_train, y_train)

# Evaluate on validation set
if len(y_val) > 0:
    y_pred = model.predict(X_val)
    print("Classification Report:")
    print(classification_report(y_val, y_pred, zero_division=0))
else:
    print("No validation data available")

# Save model
model_local = os.path.join(data_dir, 'model.job')
joblib.dump(model, model_local)
print(f"Saved model to {model_local}")

# Upload to S3
model_s3_key = 'model/model.job'
s3.upload_file(model_local, bucket, model_s3_key)
print(f"Uploaded to s3://{bucket}/{model_s3_key}")