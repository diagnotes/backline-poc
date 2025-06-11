import pandas as pd
import boto3
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
bucket = 'escalation-poc'
data_dir = 'escalations/data'

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

tasks_local = os.path.join(data_dir, 'tasks.csv')
if not os.path.exists(tasks_local):
    tasks_data = pd.DataFrame([
        {'task_id': 1, 'task_type': 'medication', 'deadline': '2025-06-12T18:00:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 2, 'task_type': 'vitals', 'deadline': '2025-06-12T18:05:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 3, 'task_type': 'charting', 'deadline': '2025-06-11T17:10:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 4, 'task_type': 'medication', 'deadline': '2025-06-11T17:15:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 5, 'task_type': 'vitals', 'deadline': '2025-06-11T17:20:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 6, 'task_type': 'charting', 'deadline': '2025-06-12T18:25:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 7, 'task_type': 'medication', 'deadline': '2025-06-11T17:30:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 8, 'task_type': 'vitals', 'deadline': '2025-06-11T17:35:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 9, 'task_type': 'charting', 'deadline': '2025-06-12T18:40:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 10, 'task_type': 'medication', 'deadline': '2025-06-11T17:45:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 11, 'task_type': 'vitals', 'deadline': '2025-06-12T18:50:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 12, 'task_type': 'charting', 'deadline': '2025-06-11T17:55:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 13, 'task_type': 'medication', 'deadline': '2025-06-11T18:00:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 14, 'task_type': 'vitals', 'deadline': '2025-06-11T18:05:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 15, 'task_type': 'charting', 'deadline': '2025-06-12T19:00:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 16, 'task_type': 'medication', 'deadline': '2025-06-11T18:15:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 17, 'task_type': 'vitals', 'deadline': '2025-06-11T18:20:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 18, 'task_type': 'charting', 'deadline': '2025-06-11T18:25:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 19, 'task_type': 'medication', 'deadline': '2025-06-12T18:30:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 20, 'task_type': 'vitals', 'deadline': '2025-06-11T18:35:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 21, 'task_type': 'medication', 'deadline': '2025-06-11T18:40:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 22, 'task_type': 'vitals', 'deadline': '2025-06-12T18:45:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 23, 'task_type': 'charting', 'deadline': '2025-06-11T18:50:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 24, 'task_type': 'medication', 'deadline': '2025-06-11T18:55:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 25, 'task_type': 'vitals', 'deadline': '2025-06-12T19:00:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 26, 'task_type': 'charting', 'deadline': '2025-06-11T19:05:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 27, 'task_type': 'medication', 'deadline': '2025-06-11T19:10:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 28, 'task_type': 'vitals', 'deadline': '2025-06-12T19:15:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 29, 'task_type': 'charting', 'deadline': '2025-06-11T19:20:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 30, 'task_type': 'medication', 'deadline': '2025-06-11T19:25:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 31, 'task_type': 'medication', 'deadline': '2025-06-11T19:30:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 32, 'task_type': 'vitals', 'deadline': '2025-06-12T19:35:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 33, 'task_type': 'charting', 'deadline': '2025-06-11T19:40:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 34, 'task_type': 'medication', 'deadline': '2025-06-11T19:45:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 35, 'task_type': 'vitals', 'deadline': '2025-06-12T19:50:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 36, 'task_type': 'charting', 'deadline': '2025-06-11T19:55:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 37, 'task_type': 'medication', 'deadline': '2025-06-11T20:00:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 38, 'task_type': 'vitals', 'deadline': '2025-06-12T20:05:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 39, 'task_type': 'charting', 'deadline': '2025-06-11T20:10:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 40, 'task_type': 'medication', 'deadline': '2025-06-11T20:15:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 41, 'task_type': 'vitals', 'deadline': '2025-06-12T20:20:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 42, 'task_type': 'charting', 'deadline': '2025-06-11T20:25:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 43, 'task_type': 'medication', 'deadline': '2025-06-11T20:30:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 44, 'task_type': 'vitals', 'deadline': '2025-06-12T20:35:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 45, 'task_type': 'charting', 'deadline': '2025-06-11T20:40:00', 'assigned_nurse': 'Eve_Davis', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 46, 'task_type': 'medication', 'deadline': '2025-06-11T20:45:00', 'assigned_nurse': 'Frank_Miller', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 47, 'task_type': 'vitals', 'deadline': '2025-06-12T20:50:00', 'assigned_nurse': 'David_Brown', 'status': 'pending', 'escalation_to': 'None'},
        {'task_id': 48, 'task_type': 'charting', 'deadline': '2025-06-11T20:55:00', 'assigned_nurse': 'Bob_Smith', 'status': 'pending', 'escalation_to': 'David_Brown'},
        {'task_id': 49, 'task_type': 'medication', 'deadline': '2025-06-11T21:00:00', 'assigned_nurse': 'Carol_Williams', 'status': 'pending', 'escalation_to': 'Carol_Williams'},
        {'task_id': 50, 'task_type': 'vitals', 'deadline': '2025-06-12T21:05:00', 'assigned_nurse': 'Alice_Johnson', 'status': 'pending', 'escalation_to': 'None'},
    ])
    tasks_data.to_csv(tasks_local, index=False)
    print(f"Created {tasks_local}")

schedules_local = os.path.join(data_dir, 'schedules.csv')
rules_local = os.path.join(data_dir, 'rules.csv')
users_local = os.path.join(data_dir, 'users.csv')

tasks = pd.read_csv(tasks_local)
schedules = pd.read_csv(schedules_local)
rules = pd.read_csv(rules_local)
users = pd.read_csv(users_local)

data = tasks.merge(schedules, left_on='assigned_nurse', right_on='user_id', how='left')
data = data.merge(users, left_on='assigned_nurse', right_on='user_id', how='left')

current_time = pd.Timestamp.now(tz='UTC')
data['deadline_missed'] = pd.to_datetime(data['deadline'], utc=True) < current_time
data['nurse_unavailable'] = data['availability'].apply(lambda x: 1 if x == 0 else 0)
data['time_since_deadline'] = (current_time - pd.to_datetime(data['deadline'], utc=True)).dt.total_seconds() / 60
data['missed_2min'] = data['time_since_deadline'].apply(lambda x: 1 if x > 2 else 0)
data['missed_5min'] = data['time_since_deadline'].apply(lambda x: 1 if x > 5 else 0)
data['task_type_medication'] = data['task_type'].apply(lambda x: 1 if x == 'medication' else 0)
data['task_type_vitals'] = data['task_type'].apply(lambda x: 1 if x == 'vitals' else 0)
data['deadline_hour'] = pd.to_datetime(data['deadline'], utc=True).dt.hour
data['nurse_experience'] = data['role'].apply(lambda x: 1 if x in ['charge_nurse', 'supervisor'] else 0)
data['is_supervisor'] = data['assigned_nurse'].apply(lambda x: 1 if x == 'Carol_Williams' else 0)
data['is_charge_nurse'] = data['assigned_nurse'].apply(lambda x: 1 if x == 'David_Brown' else 0)

le_task = LabelEncoder()
le_nurse = LabelEncoder()
le_role = LabelEncoder()
le_target = LabelEncoder()
data['task_type'] = le_task.fit_transform(data['task_type'])
data['assigned_nurse'] = le_nurse.fit_transform(data['assigned_nurse'])
data['role'] = le_role.fit_transform(data['role'].fillna('None'))
data['escalation_to'] = le_target.fit_transform(data['escalation_to'].fillna('None'))

features = [
    'task_type', 'deadline_missed', 'nurse_unavailable', 'missed_2min', 'missed_5min',
    'task_type_medication', 'task_type_vitals', 'deadline_hour', 'assigned_nurse',
    'role', 'nurse_experience', 'is_supervisor', 'is_charge_nurse'
]
X = data[features]
y = data['escalation_to']

print("Feature summary:")
print(X.describe())
print("Target distribution:")
print(y.value_counts())
print("Missing values:")
print(X.isna().sum())

selector = SelectKBest(f_classif, k=9)
selector.fit(X, y)
selected_indices = selector.get_support(indices=True)
selected_features = [features[i] for i in selected_indices]
print(f"Selected features: {selected_features}")
print(f"Feature scores: {selector.scores_}")

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
train_data = pd.concat([y_train.reset_index(drop=True), X_train.reset_index(drop=True)], axis=1)
val_data = pd.concat([y_val.reset_index(drop=True), X_val.reset_index(drop=True)], axis=1)
train_data.to_csv(os.path.join(data_dir, 'train.csv'), index=False, header=False)
val_data.to_csv(os.path.join(data_dir, 'validation.csv'), index=False, header=False)

s3.upload_file(os.path.join(data_dir, 'train.csv'), bucket, 'data/train/train.csv')
s3.upload_file(os.path.join(data_dir, 'validation.csv'), bucket, 'data/validation/validation.csv')
print(f"Uploaded data to s3://{bucket}/data/")