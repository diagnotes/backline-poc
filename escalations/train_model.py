import pandas as pd
import boto3
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from botocore.exceptions import ClientError

# Initialize S3 client
s3 = boto3.client('s3')
bucket = 'escalation-poc'
data_dir = 'data'

# Create data directory
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Download training data
train_s3_key = 'data/train/train.csv'
train_local = os.path.join(data_dir, 'train.csv')
try:
    s3.download_file(bucket, train_s3_key, train_local)
    print(f"Downloaded s3://{bucket}/{train_s3_key} to {train_local}")
except ClientError as e:
    if e.response['Error']['Code'] == '404':
        print(f"Error: Training data not found in S3")
        raise
    else:
        raise e

# Load data
data = pd.read_csv(train_local, header=None)
X = data.iloc[:, 1:]  # Features
y = data.iloc[:, 0]   # Target

# Check number of samples
n_samples = len(y)
print(f"Number of training samples: {n_samples}")

# Adjust cross-validation folds
cv = min(3, n_samples)  # Use 2 folds if n_samples < 3
if n_samples < 2:
    print("Error: Too few samples for cross-validation")
    exit(1)

# Train with cross-validation
model = RandomForestClassifier(n_estimators=100, random_state=42)
scores = cross_val_score(model, X, y, cv=cv, scoring='f1_weighted')
print("Cross-Validation F1 Scores:", scores)
print("Mean F1 Score:", scores.mean())
print("Standard Deviation:", scores.std())

# Train final model
model.fit(X, y)

# Save model
model_local = os.path.join(data_dir, 'model.job')
joblib.dump(model, model_local)
print(f"Saved model to {model_local}")

# Upload to S3
model_s3_key = 'model/model.job'
s3.upload_file(model_local, bucket, model_s3_key)
print(f"Uploaded to s3://{bucket}/{model_s3_key}")