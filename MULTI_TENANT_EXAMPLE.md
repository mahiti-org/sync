# Multi-Tenant and Role-Based Access Control Example

## 🏥 **Healthcare Scenario: Multiple Hospitals**

Imagine you have 3 hospitals using the same sync system:

- **City General Hospital** (city-general)
- **Riverside Medical Center** (riverside-medical)  
- **Community Health Clinic** (community-health)

Each hospital has different users with different roles and access levels.

## 👥 **User Roles and Permissions**

### **Role Hierarchy:**
1. **ADMIN** - Full access to all data
2. **DOCTOR** - Can push/pull patient data, treatments, but can't delete
3. **NURSE** - Can push/pull patient visits, treatments, limited access
4. **LAB_TECH** - Can push/pull lab investigations only
5. **PHARMACIST** - Can push/pull medicine disbursed data
6. **READ_ONLY** - Can only pull data, no push access

## 🚀 **Setup Commands**

### **1. Create Organizations**
```bash
python manage.py setup_organizations --action create_org --org-name "City General Hospital" --org-slug city-general
python manage.py setup_organizations --action create_org --org-name "Riverside Medical Center" --org-slug riverside-medical
python manage.py setup_organizations --action create_org --org-name "Community Health Clinic" --org-slug community-health
```

### **2. Add Users to Organizations**
```bash
# Add doctors to City General Hospital
python manage.py setup_organizations --action add_user --username dr_smith --org-slug city-general --role DOCTOR
python manage.py setup_organizations --action add_user --username dr_jones --org-slug city-general --role DOCTOR

# Add nurses to Riverside Medical Center
python manage.py setup_organizations --action add_user --username nurse_wilson --org-slug riverside-medical --role NURSE
python manage.py setup_organizations --action add_user --username nurse_brown --org-slug riverside-medical --role NURSE

# Add lab tech to Community Health Clinic
python manage.py setup_organizations --action add_user --username lab_tech_garcia --org-slug community-health --role LAB_TECH
```

### **3. Setup Complete Healthcare System**
```bash
python manage.py setup_organizations --action setup_healthcare
```

## 📊 **How It Works**

### **1. User Authentication & Organization Context**

When a user logs in, they get their organization context:

```python
# POST /api/sync/auth/token/
{
    "username": "dr_smith",
    "password": "password123"
}

# Response includes organization info
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "dr_smith",
        "email": "dr.smith@citygeneral.com"
    },
    "organizations": [
        {
            "id": 1,
            "name": "City General Hospital",
            "slug": "city-general",
            "role": "DOCTOR"
        }
    ]
}
```

### **2. PUSH API with Multi-Tenant Permissions**

**Scenario:** Dr. Smith pushes patient data to City General Hospital

```python
# POST /api/sync/push/
# Headers: Authorization: Bearer <token>

{
    "data": [
        {
            "_model": "healthcare.Patient",
            "name": "John Doe",
            "age": 45,
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1
        },
        {
            "_model": "healthcare.PatientVisit",
            "patient_id": 1,
            "visit_date": "2024-01-15",
            "symptoms": "Chest pain",
            "diagnosis": "Angina"
        }
    ]
}
```

**What happens:**
1. ✅ System checks: Is Dr. Smith in City General Hospital? **YES**
2. ✅ System checks: Does DOCTOR role have push permission for `healthcare.Patient`? **YES**
3. ✅ System checks: Does DOCTOR role have push permission for `healthcare.PatientVisit`? **YES**
4. ✅ System adds organization context: `organization: 1` (City General Hospital)
5. ✅ Data is saved with organization filter
6. ✅ User sync metadata is updated

**Response:**
```json
{
    "status": "success",
    "success_count": 2,
    "error_count": 0,
    "processed_models": {
        "healthcare.Patient": {"created": 1, "updated": 0},
        "healthcare.PatientVisit": {"created": 1, "updated": 0}
    },
    "processing_time": 0.045
}
```

### **3. PULL API with Role-Based Data Filtering**

**Scenario:** Dr. Smith pulls patient data from City General Hospital

```python
# POST /api/sync/pull/
# Headers: Authorization: Bearer <token>

{
    "models": {
        "healthcare.Patient": "2024-01-14T10:00:00Z",
        "healthcare.PatientVisit": "2024-01-14T10:00:00Z"
    },
    "batch_size": 100
}
```

**What happens:**
1. ✅ System checks: Is Dr. Smith in City General Hospital? **YES**
2. ✅ System checks: Does DOCTOR role have pull permission? **YES**
3. ✅ System applies organization filter: `organization=1`
4. ✅ System applies role filters:
   - Department filter: `department='CARDIOLOGY'` (Dr. Smith's department)
   - Assigned patients filter: `assigned_doctor_id=1` (Dr. Smith's patients)
5. ✅ System returns only filtered data

**Response:**
```json
{
    "data": [
        {
            "_model": "healthcare.Patient",
            "id": 1,
            "name": "John Doe",
            "age": 45,
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1,
            "organization": 1
        },
        {
            "_model": "healthcare.PatientVisit",
            "id": 1,
            "patient_id": 1,
            "visit_date": "2024-01-15",
            "symptoms": "Chest pain",
            "diagnosis": "Angina",
            "organization": 1
        }
    ],
    "metadata": {
        "healthcare.Patient": {
            "count": 1,
            "last_sync": "2024-01-15T10:30:00Z",
            "user_last_sync": "2024-01-14T10:00:00Z"
        },
        "healthcare.PatientVisit": {
            "count": 1,
            "last_sync": "2024-01-15T10:30:00Z",
            "user_last_sync": "2024-01-14T10:00:00Z"
        }
    },
    "batch_info": {
        "batch_size": 100,
        "total_records": 2
    }
}
```

## 🔒 **Permission Examples**

### **Example 1: Nurse Wilson (Riverside Medical Center)**

**Permissions:**
- ✅ Can push/pull `healthcare.PatientVisit`
- ✅ Can push/pull `healthcare.PatientTreatment`
- ❌ Cannot access `healthcare.LabInvestigation` (LAB_TECH only)
- ❌ Cannot delete any records

**Data Filter:**
- Only sees patients assigned to her: `assigned_nurse_id = 2`

### **Example 2: Lab Tech Garcia (Community Health Clinic)**

**Permissions:**
- ✅ Can push/pull `healthcare.LabInvestigation`
- ❌ Cannot access `healthcare.Patient` (read-only)
- ❌ Cannot access `healthcare.MedicineDisbursed` (PHARMACIST only)

**Data Filter:**
- Only sees lab investigations from Community Health Clinic: `organization = 3`

### **Example 3: Read-Only User**

**Permissions:**
- ✅ Can pull all data (read-only)
- ❌ Cannot push any data
- ❌ Cannot create/update/delete

## 🏗️ **Database Structure**

### **Organizations Table:**
```sql
SELECT * FROM sb_sync_organization;
```

| id | name | slug | is_active |
|----|------|------|-----------|
| 1 | City General Hospital | city-general | true |
| 2 | Riverside Medical Center | riverside-medical | true |
| 3 | Community Health Clinic | community-health | true |

### **User Organizations Table:**
```sql
SELECT * FROM sb_sync_user_organization;
```

| user_id | organization_id | role | is_active |
|---------|-----------------|------|-----------|
| 1 | 1 | DOCTOR | true |
| 2 | 2 | NURSE | true |
| 3 | 3 | LAB_TECH | true |

### **Model Permissions Table:**
```sql
SELECT * FROM sb_sync_model_permission WHERE organization_id = 1;
```

| organization_id | role | model_name | can_push | can_pull | can_create | can_update | can_delete |
|----------------|------|------------|----------|----------|------------|------------|------------|
| 1 | DOCTOR | healthcare.Patient | true | true | true | true | false |
| 1 | DOCTOR | healthcare.PatientVisit | true | true | true | true | false |
| 1 | NURSE | healthcare.Patient | false | true | false | false | false |
| 1 | READ_ONLY | healthcare.Patient | false | true | false | false | false |

### **Data Filters Table:**
```sql
SELECT * FROM sb_sync_data_filter WHERE organization_id = 1;
```

| organization_id | role | model_name | filter_name | filter_condition |
|----------------|------|------------|-------------|------------------|
| 1 | DOCTOR | healthcare.Patient | department_filter | {"field": "department", "operator": "exact", "value": "CARDIOLOGY"} |
| 1 | NURSE | healthcare.Patient | assigned_patients | {"field": "assigned_nurse_id", "operator": "exact", "value": 1} |

## 🔄 **Sync Metadata Per User/Organization**

### **User Sync Metadata Table:**
```sql
SELECT * FROM sb_sync_user_sync_metadata WHERE user_id = 1;
```

| user_id | organization_id | model_name | last_sync | total_synced |
|---------|-----------------|------------|-----------|--------------|
| 1 | 1 | healthcare.Patient | 2024-01-15 10:30:00 | 150 |
| 1 | 1 | healthcare.PatientVisit | 2024-01-15 10:30:00 | 300 |
| 1 | 1 | healthcare.PatientTreatment | 2024-01-15 10:30:00 | 200 |

## 🚨 **Error Scenarios**

### **1. Unauthorized Access**
```python
# User tries to access model they don't have permission for
{
    "status": "error",
    "error": "User dr_smith does not have pull permission for healthcare.LabInvestigation in City General Hospital",
    "error_count": 1
}
```

### **2. Wrong Organization**
```python
# User tries to access data from different organization
{
    "status": "error", 
    "error": "User is not associated with any organization",
    "context": {"user_id": 1}
}
```

### **3. Role-Based Filtering**
```python
# Doctor tries to see all patients but only gets their department's patients
{
    "data": [
        # Only CARDIOLOGY patients returned
    ],
    "metadata": {
        "healthcare.Patient": {
            "count": 25,  # Only 25 patients (from their department)
            "filter_applied": "department_filter"
        }
    }
}
```

## 🎯 **Key Benefits**

1. **🔒 Data Isolation**: Each hospital only sees their own data
2. **👥 Role-Based Access**: Different roles have different permissions
3. **📊 Granular Control**: Can filter data by department, assigned staff, etc.
4. **🔄 Per-User Sync Tracking**: Each user has their own sync history
5. **⚡ Performance**: Cached permissions and filtered queries
6. **🛡️ Security**: Multi-layer permission checking
7. **📈 Scalability**: Supports unlimited organizations and users

## 🚀 **Usage in Real Healthcare**

```python
# Hospital A (City General) - Dr. Smith
POST /api/sync/push/
{
    "data": [
        {
            "_model": "healthcare.Patient",
            "name": "John Doe",
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1
        }
    ]
}
# ✅ Success - Dr. Smith has permission

# Hospital B (Riverside) - Nurse Wilson  
POST /api/sync/pull/
{
    "models": {"healthcare.Patient": "2024-01-14T10:00:00Z"}
}
# ✅ Success - Nurse Wilson gets only her assigned patients

# Hospital C (Community) - Lab Tech Garcia
POST /api/sync/push/
{
    "data": [
        {
            "_model": "healthcare.LabInvestigation",
            "patient_id": 5,
            "test_type": "BLOOD_TEST",
            "results": "Normal"
        }
    ]
}
# ✅ Success - Lab Tech has permission for lab investigations
```

This multi-tenant system ensures that each hospital's data is completely isolated while allowing role-based access within each organization! 🏥🔒 