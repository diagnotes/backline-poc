import pandas as pd
import boto3
import io
import os
import hashlib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Initialize S3 client
s3 = boto3.client('s3')
bucket = 'escalation-poc'

# Check if file exists in S3
def file_exists_s3(bucket, key):
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        return 'Contents' in response and len(response['Contents']) > 0
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise e

# Get S3 object's ETag
def get_s3_etag(bucket, key):
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        if 'Contents' in response and len(response['Contents']) > 0:
            return response['Contents'][0].get('ETag', '').strip('"')
        return None
    except ClientError:
        return None

# Function to compute MD5 hash of a file
def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# Create local data directory if it doesn't exist
data_dir = 'escalations/data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created local directory {data_dir}")

# Define local CSV paths
tasks_local = os.path.join(data_dir, 'tasks.csv')
schedules_local = os.path.join(data_dir, 'schedules.csv')
rules_local = os.path.join(data_dir, 'rules.csv')
users_local = os.path.join(data_dir, 'users.csv')

if not os.path.exists(tasks_local):
    tasks_data = pd.DataFrame([
        {'task_id': 1, 'task_type': 'medication', 'deadline': '2025-06-11T17:00:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 2, 'task_type': 'vitals', 'deadline': '2025-06-11T17:05:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 3, 'task_type': 'charting', 'deadline': '2025-06-11T17:10:00', 'assigned_nurse': 'David_Brown', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
        {'task_id': 4, 'task_type': 'medication', 'deadline': '2025-06-11T17:15:00', 'assigned_nurse': 'Bob_Smith', 'status': 'escalated', 'escalation_to': 'David_Brown'},
        {'task_id': 5, 'task_type': 'vitals', 'deadline': '2025-06-11T17:20:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
        {'task_id': 6, 'task_type': 'charting', 'deadline': '2025-06-11T17:25:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 7, 'task_type': 'medication', 'deadline': '2025-06-11T17:30:00', 'assigned_nurse': 'Eve_Davis', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
        {'task_id': 8, 'task_type': 'vitals', 'deadline': '2025-06-11T17:35:00', 'assigned_nurse': 'David_Brown', 'status': 'escalated', 'escalation_to': 'David_Brown'},
        {'task_id': 9, 'task_type': 'charting', 'deadline': '2025-06-11T17:40:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 10, 'task_type': 'medication', 'deadline': '2025-06-11T17:45:00', 'assigned_nurse': 'Bob_Smith', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
        {'task_id': 11, 'task_type': 'vitals', 'deadline': '2025-06-11T17:50:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 12, 'task_type': 'charting', 'deadline': '2025-06-11T17:55:00', 'assigned_nurse': 'Eve_Davis', 'status': 'escalated', 'escalation_to': 'David_Brown'},
        {'task_id': 13, 'task_type': 'medication', 'deadline': '2025-06-11T18:00:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
        {'task_id': 14, 'task_type': 'vitals', 'deadline': '2025-06-11T18:05:00', 'assigned_nurse': 'Bob_Smith', 'status': 'escalated', 'escalation_to': 'David_Brown'},
        {'task_id': 15, 'task_type': 'charting', 'deadline': '2025-06-11T18:10:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': ''},
        {'task_id': 16, 'task_type': 'medication', 'deadline': '2025-06-11T18:15:00', 'assigned_nurse': 'Carol_Williams', 'status': 'escalated', 'escalation_to': 'Carol_Williams'},
    ])
    tasks_data.to_csv(tasks_local, index=False)
    print(f"Created local file {tasks_local}")

if not os.path.exists(schedules_local):
    schedules_data = pd.DataFrame([
        {'user_id': 'Alice_Johnson', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T08:00:00', 'shift_end': '2025-06-11T16:00:00', 'availability': 1},
        {'user_id': 'Bob_Smith', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T12:00:00', 'shift_end': '2025-06-11T20:00:00', 'availability': 1},
        {'user_id': 'Carol_Williams', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T16:00:00', 'shift_end': '2025-06-12T00:00:00', 'availability': 1},
        {'user_id': 'David_Brown', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T08:00:00', 'shift_end': '2025-06-11T20:00:00', 'availability': 1},
        {'user_id': 'Eve_Davis', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T10:00:00', 'shift_end': '2025-06-11T18:00:00', 'availability': 0},
        {'user_id': 'Frank_Miller', 'shift_date': '2025-06-11', 'shift_start': '2025-06-11T14:00:00', 'shift_end': '2025-06-11T22:00:00', 'availability': 1},
    ])
    schedules_data.to_csv(schedules_local, index=False)
    print(f"Created local file {schedules_local}")

if not os.path.exists(users_local):
    users_data = pd.DataFrame([
        {'user_id': 'Alice_Johnson', 'first_name': 'Alice', 'last_name': 'Johnson', 'role': 'floor_nurse'},
        {'user_id': 'Bob_Smith', 'first_name': 'Bob', 'last_name': 'Smith', 'role': 'floor_nurse'},
        {'user_id': 'Carol_Williams', 'first_name': 'Carol', 'last_name': 'Williams', 'role': 'supervisor'},
        {'user_id': 'David_Brown', 'first_name': 'David', 'last_name': 'Brown', 'role': 'charge_nurse'},
        {'user_id': 'Eve_Davis', 'first_name': 'Eve', 'last_name': 'Davis', 'role': 'floor_nurse'},
        {'user_id': 'Frank_Miller', 'first_name': 'Frank', 'last_name': 'Miller', 'role': 'floor_nurse'},
    ])
    users_data.to_csv(users_local, index=False)
    print(f"Created local file {users_local}")

if not os.path.exists(rules_local):
    rules_data = pd.DataFrame([
        {'rule_id': 1, 'rule_text': 'If task is not completed in 2 minutes, escalate to the charge nurse'},
        {'rule_id': 2, 'rule_text': 'If nurse is unavailable, escalate to the supervisor'},
        {'rule_id': 3, 'rule_text': 'If task type is medication and not completed in 5 minutes, escalate to the charge nurse'}
    ])
    rules_data.to_csv(rules_local, index=False)
    print(f"Created local file {rules_local}")

# Upload CSV files to S3 only if changed or missing
s3_keys = {
    tasks_local: 'data/tasks.csv',
    schedules_local: 'data/schedules.csv',
    rules_local: 'data/rules.csv',
    users_local: 'data/users.csv'
}

for local_file, s3_key in s3_keys.items():
    local_md5 = compute_md5(local_file)
    s3_etag = get_s3_etag(bucket, s3_key)
    if not file_exists_s3(bucket, s3_key) or local_md5 != s3_etag:
        s3.upload_file(local_file, bucket, s3_key)
        print(f"Uploaded {local_file} to s3://{bucket}/{s3_key} (changed or missing)")
    else:
        print(f"s3://{bucket}/{s3_key} is up-to-date (no changes)")

# Download CSVs from S3
for s3_key in s3_keys.values():
    local_file = os.path.join(data_dir, os.path.basename(s3_key))
    s3.download_file(bucket, s3_key, local_file)
    print(f"Downloaded s3://{bucket}/{s3_key} to {local_file}")

# Load data
tasks = pd.read_csv(tasks_local)
schedules = pd.read_csv(schedules_local)
rules = pd.read_csv(rules_local)
users = pd.read_csv(users_local)

# Join tasks with schedules and users
data = tasks.merge(schedules, left_on='assigned_nurse', right_on='user_id', how='left')
data = data.merge(users, left_on='assigned_nurse', right_on='user_id', how='left', suffixes=('', '_assigned'))

# Add rule-based features
current_time = pd.Timestamp.now(tz='UTC')
data['nurse_unavailable'] = data['availability'].apply(lambda x: 1 if x == 0 else 0)
data['deadline_missed'] = pd.to_datetime(data['deadline'], utc=True) < current_time
data['task_type_medication'] = data['task_type'].apply(lambda x: 1 if x == 'medication' else 0)

# Parse time-based rules
data['time_since_deadline'] = (current_time - pd.to_datetime(data['deadline'], utc=True)).dt.total_seconds() / 60  # in minutes
data['missed_2min'] = data['time_since_deadline'].apply(lambda x: 1 if x > 2 else 0)
data['missed_5min'] = data['time_since_deadline'].apply(lambda x: 1 if x > 5 else 0)

# Add role-based features
data['is_floor_nurse'] = data['role'].apply(lambda x: 1 if x == 'floor_nurse' else 0)
data['is_supervisor'] = data['role'].apply(lambda x: 1 if x == 'supervisor' else 0)
data['is_charge_nurse'] = data['role'].apply(lambda x: 1 if x == 'charge_nurse' else 0)

# Add full_name feature
data['full_name'] = data['first_name'] + ' ' + data['last_name']

# Encode categorical variables
le_task = LabelEncoder()
le_nurse = LabelEncoder()
le_target = LabelEncoder()
le_role = LabelEncoder()
le_name = LabelEncoder()

data['task_type'] = le_task.fit_transform(data['task_type'])
data['assigned_nurse'] = le_nurse.fit_transform(data['assigned_nurse'])
data['role'] = le_role.fit_transform(data['role'].fillna('None'))
data['full_name'] = le_name.fit_transform(data['full_name'].fillna('None'))
data['escalation_to'] = data['escalation_to'].fillna('None')
data['escalation_to'] = le_target.fit_transform(data['escalation_to'])

# Convert datetime to numerical features
data['deadline_hour'] = pd.to_datetime(data['deadline'], utc=True).dt.hour
data['shift_start_hour'] = pd.to_datetime(data['shift_start'], utc=True).dt.hour
data['shift_end_hour'] = pd.to_datetime(data['shift_end'], utc=True).dt.hour

# Select features and target
features = [
    'task_type', 'deadline_hour', 'assigned_nurse', 'shift_start_hour', 'shift_end_hour',
    'availability', 'nurse_unavailable', 'deadline_missed', 'task_type_medication',
    'missed_2min', 'missed_5min', 'is_floor_nurse', 'is_supervisor', 'is_charge_nurse', 'full_name'
]
X = data[features]
y = data['escalation_to']

# Split data
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Save training and validation data
train_data = pd.concat([y_train, X_train], axis=1)
val_data = pd.concat([y_val, X_val], axis=1)
train_data.to_csv(os.path.join(data_dir, 'train.csv'), index=False, header=False)
val_data.to_csv(os.path.join(data_dir, 'validation.csv'), index=False, header=False)

# Upload to S3
s3.upload_file(os.path.join(data_dir, 'train.csv'), bucket, 'data/train/train.csv')
s3.upload_file(os.path.join(data_dir, 'validation.csv'), bucket, 'data/validation/validation.csv')
print(f"Uploaded training and validation data to s3://{bucket}/data/train/ and s3://{bucket}/data/validation/")