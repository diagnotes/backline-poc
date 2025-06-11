import pandas as pd
import boto3
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
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
        print(f"Error: Training or validation data not found in S3")
        raise
    else:
        raise e

# Load data (no header, as saved in preprocess_csvs.py)
train_data = pd.read_csv(train_local, header=None)
val_data = pd.read_csv(val_local, header=None)

# Split features and target
X_train = train_data.iloc[:, 1:]  # All columns except first (escalation_to)
y_train = train_data.iloc[:, 0]   # First column (escalation_to)
X_val = val_data.iloc[:, 1:]
y_val = val_data.iloc[:, 0]

# Train Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate on validation set
y_pred = model.predict(X_val)
print("Classification Report:")
print(classification_report(y_val, y_pred))

# Save model locally
model_local = os.path.join(data_dir, 'model.joblib')
joblib.dump(model, model_local)
print(f"Saved model to {model_local}")

# Upload model to S3
model_s3_key = 'model/model.joblib'
s3.upload_file(model_local, bucket, model_s3_key)
print(f"Uploaded model to s3://{bucket}/{model_s3_key}")