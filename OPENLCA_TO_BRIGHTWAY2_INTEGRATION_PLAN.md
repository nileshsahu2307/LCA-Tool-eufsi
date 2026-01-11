# OpenLCA to Brightway2 Integration Plan
## Transferring Custom Processes and Linking to ecoinvent

**Project**: EUFSI LCA Tool Enhancement
**Objective**: Import custom textile processes from OpenLCA into Brightway2 and link them with ecoinvent background data
**Date**: January 11, 2026

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Phase 1: Preparation & Export](#phase-1-preparation--export)
3. [Phase 2: Brightway2 Setup](#phase-2-brightway2-setup)
4. [Phase 3: Database Import](#phase-3-database-import)
5. [Phase 4: Linking & Validation](#phase-4-linking--validation)
6. [Phase 5: Integration into EUFSI Tool](#phase-5-integration-into-eufsi-tool)
7. [Phase 6: Testing & Optimization](#phase-6-testing--optimization)
8. [Technical Architecture](#technical-architecture)
9. [Risk Mitigation](#risk-mitigation)
10. [Timeline Estimate](#timeline-estimate)

---

## Prerequisites

### What You Need Before Starting

#### 1. OpenLCA Setup
- ✅ OpenLCA installed with your custom textile processes
- ✅ ecoinvent database imported in OpenLCA (version 3.9.1 recommended)
- ✅ Custom processes validated and working in OpenLCA
- ✅ List of all custom processes you want to transfer

#### 2. ecoinvent License & Files
- ✅ Valid ecoinvent license
- ✅ ecoinvent 3.9.1 dataset files (`.spold` format from ecoinvent.org)
- ✅ OR ecoinvent already in OpenLCA (to export as JSON-LD)

#### 3. Python Environment
- ✅ Python 3.9 or 3.10 (Brightway2 compatibility)
- ✅ Virtual environment for testing
- ✅ Storage: ~10-15 GB free space for databases

#### 4. Access & Credentials
- ✅ Local development environment (your Windows machine)
- ✅ Access to deploy to Render.com (for production)

---

## Phase 1: Preparation & Export

**Duration**: 1-2 hours
**Objective**: Export your custom processes from OpenLCA in the correct format

### Step 1.1: Inventory Your Custom Processes

**In OpenLCA:**
1. Open your OpenLCA database
2. Go to **Processes** folder
3. Create a document listing all custom processes:
   - Process name
   - Process UUID
   - What it represents (e.g., "Organic cotton spinning - India")
   - Dependencies on ecoinvent processes

**Example inventory:**
```
Custom Processes Inventory
==========================
1. Organic cotton fiber production - India
   - UUID: abc-123-def-456
   - Inputs: Pesticides, Water, Land use
   - Outputs: Organic cotton fiber
   - ecoinvent links: Uses "market for pesticide" from ecoinvent

2. Yarn spinning - Renewable energy - China
   - UUID: xyz-789-ghi-012
   - Inputs: Cotton fiber, Electricity (renewable)
   - Outputs: Cotton yarn
   - ecoinvent links: Uses "electricity, from wind" from ecoinvent

[... etc ...]
```

### Step 1.2: Export Custom Processes Only

**Option A: Export Custom Processes Separately (Recommended)**

1. In OpenLCA, create a **new empty database**
2. Name it: `EUFSI_Custom_Textile_Processes`
3. **Right-click** on each custom process → **Copy**
4. **Paste** into the new database
5. Verify all processes are copied

**Export the custom database:**
1. Right-click on `EUFSI_Custom_Textile_Processes` database
2. Select **Export** → **JSON-LD**
3. Choose location: `C:\Users\niles\Desktop\exports\`
4. Filename: `eufsi_custom_processes_jsonld.zip`
5. **Export as ZIP archive**: ✅ Yes
6. Click **Finish**

**Expected output:**
```
C:\Users\niles\Desktop\exports\
└── eufsi_custom_processes_jsonld.zip (5-50 MB depending on process count)
```

---

**Option B: Export Entire Database (Not Recommended)**

If you want to export everything including ecoinvent:
1. Right-click on your main database
2. Export → JSON-LD
3. **Warning**: This will be 5-10 GB and take 30+ minutes
4. Only use if you need exact OpenLCA configuration

---

### Step 1.3: Verify Export

**Extract and inspect the ZIP file:**
```
eufsi_custom_processes_jsonld.zip
├── processes/
│   ├── abc-123-def-456.json (Organic cotton fiber)
│   ├── xyz-789-ghi-012.json (Yarn spinning)
│   └── ...
├── flows/
│   ├── flow-123.json
│   └── ...
├── flow_properties/
└── unit_groups/
```

**Check JSON structure:**
Open one process file (e.g., `abc-123-def-456.json`) and verify:
- Process name is correct
- Exchanges (inputs/outputs) are listed
- UUIDs are present
- References to ecoinvent processes have correct UUIDs

---

## Phase 2: Brightway2 Setup

**Duration**: 2-3 hours
**Objective**: Set up Brightway2 environment and import ecoinvent

### Step 2.1: Create Brightway2 Environment

**On your local machine (Windows):**

```bash
# Create a new Python virtual environment
cd C:\Users\niles\Desktop\
python -m venv brightway_env

# Activate the environment
brightway_env\Scripts\activate

# Install Brightway2 and dependencies
pip install brightway2
pip install bw2io
pip install bw2data
pip install bw2calc
pip install pandas
pip install jupyter  # Optional, for testing
```

**Verify installation:**
```python
python
>>> import brightway2 as bw
>>> bw.__version__
'2.4.6'  # or similar
>>> exit()
```

---

### Step 2.2: Initialize Brightway2 Project

```python
import brightway2 as bw

# Create a new project for EUFSI
bw.projects.set_current("EUFSI_LCA_Tool")

# Check project location
print(bw.projects.dir)
# Output: C:\Users\niles\AppData\Local\pylca\Brightway3\EUFSI_LCA_Tool.XXX\
```

**What this does:**
- Creates isolated database directory
- Stores all databases in this project
- Prevents conflicts with other projects

---

### Step 2.3: Import ecoinvent into Brightway2

**Method A: Import from ecoinvent.org download (Recommended)**

```python
import brightway2 as bw
from bw2io.importers import SingleOutputEcospold2Importer

# Set project
bw.projects.set_current("EUFSI_LCA_Tool")

# Import ecoinvent 3.9.1 cutoff
# Replace with your actual path to unzipped ecoinvent files
ecoinvent_path = "C:/Users/niles/Desktop/ecoinvent_391_cutoff/datasets"

print("Starting ecoinvent import... (this takes 15-30 minutes)")
ei = SingleOutputEcospold2Importer(
    ecoinvent_path,
    "ecoinvent_391_cutoff"
)

# Apply strategies (linking, allocation, etc.)
ei.apply_strategies()

# Check for unlinked exchanges
print(f"Unlinked exchanges: {len(ei.unlinked)}")
if len(ei.unlinked) > 0:
    print("First 5 unlinked:")
    for exc in ei.unlinked[:5]:
        print(f"  - {exc}")

# Write to database (takes 10-20 minutes)
print("Writing database...")
ei.write_database()

print("✅ ecoinvent imported successfully!")
print(f"Database name: {ei.db_name}")
print(f"Activities: {len(bw.Database('ecoinvent_391_cutoff'))}")
```

**Expected output:**
```
Starting ecoinvent import...
Extracting XML data from 21238 datasets
Applying strategies...
Linked 99.8% of exchanges
Unlinked exchanges: 42
Writing database...
✅ ecoinvent imported successfully!
Database name: ecoinvent_391_cutoff
Activities: 21238
```

**Time estimate**: 20-40 minutes depending on your computer

---

**Method B: Import ecoinvent from OpenLCA export (Alternative)**

If you already have ecoinvent in OpenLCA and want to export it:

```python
from bw2io.importers import JSONLDImporter

# Export ecoinvent from OpenLCA as JSON-LD first
# Then import:
ei = JSONLDImporter(
    "C:/Users/niles/Desktop/exports/ecoinvent_391_from_openlca.zip",
    "ecoinvent_391_cutoff"
)
ei.apply_strategies()
ei.write_database()
```

**Warning**: This is slower and less reliable than Method A.

---

### Step 2.4: Verify ecoinvent Import

```python
import brightway2 as bw

# List all databases
print("Databases:", list(bw.databases))
# Output: ['ecoinvent_391_cutoff', 'biosphere3']

# Test a search
cotton_activities = bw.Database('ecoinvent_391_cutoff').search('cotton fiber')
print(f"Found {len(cotton_activities)} cotton fiber activities")

# Print first result
if cotton_activities:
    activity = cotton_activities[0]
    print(f"Name: {activity['name']}")
    print(f"Location: {activity.get('location', 'Unknown')}")
    print(f"Unit: {activity.get('unit', 'Unknown')}")
```

**Expected output:**
```
Databases: ['ecoinvent_391_cutoff', 'biosphere3']
Found 12 cotton fiber activities
Name: cotton fiber production
Location: GLO
Unit: kilogram
```

---

## Phase 3: Database Import

**Duration**: 1-2 hours
**Objective**: Import your custom OpenLCA processes into Brightway2

### Step 3.1: Import Custom Processes

```python
import brightway2 as bw
from bw2io.importers import JSONLDImporter

# Ensure you're in the right project
bw.projects.set_current("EUFSI_LCA_Tool")

# Import your custom processes
print("Importing custom EUFSI textile processes...")
custom_imp = JSONLDImporter(
    "C:/Users/niles/Desktop/exports/eufsi_custom_processes_jsonld.zip",
    "eufsi_textile_custom"
)

# Apply strategies
custom_imp.apply_strategies()

# Statistics
print(f"Total activities: {len(custom_imp.data)}")
print(f"Unlinked exchanges: {len(custom_imp.unlinked)}")

# Write database (fast, only your custom processes)
print("Writing database...")
custom_imp.write_database()

print("✅ Custom processes imported!")
print(f"Database name: {custom_imp.db_name}")
```

**Expected output:**
```
Importing custom EUFSI textile processes...
Total activities: 15
Unlinked exchanges: 23
Writing database...
✅ Custom processes imported!
Database name: eufsi_textile_custom
```

---

### Step 3.2: Inspect Imported Processes

```python
import brightway2 as bw

# List all databases
print("All databases:", list(bw.databases))
# Output: ['ecoinvent_391_cutoff', 'biosphere3', 'eufsi_textile_custom']

# Inspect custom database
db = bw.Database('eufsi_textile_custom')
print(f"\nTotal custom processes: {len(db)}")

# List all processes
print("\nCustom processes:")
for activity in db:
    print(f"  - {activity['name']} ({activity.get('location', 'Unknown')})")
```

**Expected output:**
```
All databases: ['ecoinvent_391_cutoff', 'biosphere3', 'eufsi_textile_custom']

Total custom processes: 15

Custom processes:
  - Organic cotton fiber production (IN)
  - Yarn spinning - Renewable energy (CN)
  - Fabric dyeing - Zero liquid discharge (BD)
  - [... etc ...]
```

---

## Phase 4: Linking & Validation

**Duration**: 2-4 hours
**Objective**: Link custom processes to ecoinvent background data

### Step 4.1: Automatic Linking

Brightway2 will attempt to automatically link your custom processes to ecoinvent:

```python
import brightway2 as bw

# Relink the custom database
db = bw.Database('eufsi_textile_custom')
db.process()

print("Relinking complete. Checking results...")
```

**What `db.process()` does:**
1. Searches for matching activities by UUID
2. Searches by name + unit + category
3. Links technosphere exchanges to ecoinvent
4. Updates internal references

---

### Step 4.2: Identify Unlinked Exchanges

```python
import brightway2 as bw

unlinked_report = []

for activity in bw.Database('eufsi_textile_custom'):
    for exc in activity.technosphere():
        # Check if exchange points to itself (not linked to ecoinvent)
        if exc.input[0] == 'eufsi_textile_custom':
            unlinked_report.append({
                'process': activity['name'],
                'exchange': exc.get('name', 'Unknown'),
                'amount': exc.get('amount', 0),
                'unit': exc.get('unit', 'Unknown')
            })

print(f"Total unlinked exchanges: {len(unlinked_report)}")
print("\nUnlinked exchanges:")
for item in unlinked_report[:10]:  # Show first 10
    print(f"  Process: {item['process']}")
    print(f"    → Missing: {item['exchange']} ({item['amount']} {item['unit']})")
    print()
```

**Expected output:**
```
Total unlinked exchanges: 8

Unlinked exchanges:
  Process: Organic cotton fiber production
    → Missing: market for electricity, renewable (100 kWh)

  Process: Yarn spinning - Renewable energy
    → Missing: market for natural gas, CN (50 MJ)

  [... etc ...]
```

---

### Step 4.3: Manual Linking

For unlinked exchanges, manually link them to ecoinvent:

```python
import brightway2 as bw

# Example: Link "market for electricity, renewable" to ecoinvent

# 1. Find your custom process
organic_cotton = bw.Database('eufsi_textile_custom').get('Organic cotton fiber production')

# 2. Search for matching ecoinvent activity
eco_electricity = bw.Database('ecoinvent_391_cutoff').search('electricity, renewable', filter={'location': 'IN'})

print(f"Found {len(eco_electricity)} matches")
for i, act in enumerate(eco_electricity[:5]):
    print(f"{i}: {act['name']} - {act.get('location', 'Unknown')}")

# 3. Select the correct match (e.g., index 2)
correct_match = eco_electricity[2]

# 4. Find the unlinked exchange and relink it
for exc in organic_cotton.technosphere():
    if 'electricity, renewable' in exc.get('name', '').lower():
        print(f"Relinking: {exc['name']}")
        exc.input = correct_match.key
        exc.save()
        print("✅ Linked successfully!")
```

**Repeat for all unlinked exchanges.**

---

### Step 4.4: Automated Relinking Script

Create a reusable script for common patterns:

```python
import brightway2 as bw

def relink_by_search(custom_db_name, ecoinvent_db_name, search_patterns):
    """
    Automatically relink exchanges based on search patterns.

    search_patterns = [
        ('electricity, renewable', 'market for electricity', {'location': 'IN'}),
        ('natural gas', 'market for natural gas', {'location': 'CN'}),
    ]
    """
    custom_db = bw.Database(custom_db_name)
    ecoinvent_db = bw.Database(ecoinvent_db_name)

    relinked = 0
    failed = []

    for activity in custom_db:
        for exc in activity.technosphere():
            # Check if unlinked
            if exc.input[0] == custom_db_name:
                exc_name = exc.get('name', '').lower()

                # Try each pattern
                for pattern, eco_search, filters in search_patterns:
                    if pattern.lower() in exc_name:
                        # Search ecoinvent
                        matches = ecoinvent_db.search(eco_search, filter=filters)
                        if matches:
                            exc.input = matches[0].key
                            exc.save()
                            relinked += 1
                            print(f"✅ Linked: {exc['name']} → {matches[0]['name']}")
                            break
                        else:
                            failed.append((activity['name'], exc['name'], pattern))

    print(f"\n✅ Relinked: {relinked} exchanges")
    print(f"❌ Failed: {len(failed)} exchanges")

    if failed:
        print("\nFailed exchanges:")
        for proc, exc, pattern in failed:
            print(f"  {proc} → {exc} (pattern: {pattern})")

    return relinked, failed

# Usage
patterns = [
    ('electricity', 'market for electricity', {}),
    ('natural gas', 'market for natural gas', {}),
    ('diesel', 'market for diesel', {}),
    ('water', 'market for water', {}),
]

relink_by_search('eufsi_textile_custom', 'ecoinvent_391_cutoff', patterns)
```

---

### Step 4.5: Validation

```python
import brightway2 as bw
from bw2calc import LCA

# Test LCA with a custom process
custom_db = bw.Database('eufsi_textile_custom')
test_activity = custom_db.random()  # Pick random process

print(f"Testing LCA for: {test_activity['name']}")

# Run LCA
lca = LCA({test_activity: 1})
lca.lci()
lca.lcia()

print(f"✅ LCA Score: {lca.score}")

# If this works without errors, linking is successful!
```

**Expected output:**
```
Testing LCA for: Organic cotton fiber production
✅ LCA Score: 2.45 kg CO2 eq
```

**If you get errors:**
- `KeyError`: Unlinked exchange still exists
- `ValueError`: Invalid inventory data
- Review and fix the problematic exchanges

---

## Phase 5: Integration into EUFSI Tool

**Duration**: 3-5 hours
**Objective**: Integrate the Brightway2 databases into your FastAPI backend

### Step 5.1: Package Database for Deployment

**Export databases to portable format:**

```python
import brightway2 as bw
import bw2io

bw.projects.set_current("EUFSI_LCA_Tool")

# Backup the project
bw2io.backup_project_directory("EUFSI_LCA_Tool")

# This creates a backup file at:
# C:\Users\niles\AppData\Local\pylca\Brightway3\backups\
# EUFSI_LCA_Tool.{timestamp}.tar.gz
```

**Copy this backup file to your project:**
```
C:\Users\niles\OneDrive\Desktop\LCA-Tool-eufsi-main\LCA-Tool-eufsi-main\backend\data\
└── EUFSI_LCA_Tool.backup.tar.gz
```

---

### Step 5.2: Update Backend to Load Databases

**File: `backend/brightway_setup.py` (new file)**

```python
import brightway2 as bw
import bw2io
import os
from pathlib import Path

def initialize_brightway():
    """
    Initialize Brightway2 databases for EUFSI LCA Tool.
    Run this once on deployment or when databases need updating.
    """
    project_name = "EUFSI_LCA_Tool"

    # Check if project already exists
    if project_name in bw.projects:
        print(f"✅ Project '{project_name}' already exists")
        bw.projects.set_current(project_name)
        print(f"Databases: {list(bw.databases)}")
        return

    # Restore from backup
    backup_file = Path(__file__).parent / "data" / "EUFSI_LCA_Tool.backup.tar.gz"

    if backup_file.exists():
        print(f"Restoring project from backup: {backup_file}")
        bw2io.restore_project_directory(backup_file, project_name)
        bw.projects.set_current(project_name)
        print(f"✅ Restored databases: {list(bw.databases)}")
    else:
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

def get_custom_process(process_name):
    """Get a custom process from EUFSI database."""
    bw.projects.set_current("EUFSI_LCA_Tool")
    db = bw.Database('eufsi_textile_custom')

    results = [act for act in db if process_name.lower() in act['name'].lower()]
    if results:
        return results[0]
    else:
        raise ValueError(f"Process '{process_name}' not found in custom database")

def get_ecoinvent_activity(search_term, location=None):
    """Search ecoinvent for an activity."""
    bw.projects.set_current("EUFSI_LCA_Tool")
    db = bw.Database('ecoinvent_391_cutoff')

    filters = {}
    if location:
        filters['location'] = location

    results = db.search(search_term, filter=filters)
    if results:
        return results[0]
    else:
        raise ValueError(f"Activity '{search_term}' not found in ecoinvent")
```

---

### Step 5.3: Update Calculation Functions

**File: `backend/server.py` - add import and initialization**

```python
# At the top of server.py
from brightway_setup import initialize_brightway, get_custom_process, get_ecoinvent_activity
import brightway2 as bw
from bw2calc import LCA

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    print("Initializing Brightway2 databases...")
    initialize_brightway()
    print("✅ Brightway2 ready")
```

---

### Step 5.4: Create Calculation Function with Custom Processes

**File: `backend/server.py` - enhanced calculation function**

```python
def calculate_textile_lca_with_custom(data):
    """
    Calculate LCA using custom processes when available,
    fallback to ecoinvent when not.
    """
    import brightway2 as bw
    from bw2calc import LCA

    bw.projects.set_current("EUFSI_LCA_Tool")

    # Example: Check if user wants custom organic cotton process
    fiber_type = data.get('fiber_composition', [{}])[0].get('fiber_type')
    origin = data.get('fiber_composition', [{}])[0].get('origin_country')

    if fiber_type == "Cotton (Organic)" and origin == "India":
        # Use custom process
        try:
            cotton_activity = get_custom_process("Organic cotton fiber production")
            print(f"Using custom process: {cotton_activity['name']}")
        except ValueError:
            # Fallback to ecoinvent
            cotton_activity = get_ecoinvent_activity("cotton fiber, organic", location="IN")
            print(f"Fallback to ecoinvent: {cotton_activity['name']}")
    else:
        # Use ecoinvent directly
        cotton_activity = get_ecoinvent_activity("cotton fiber production", location=origin[:2])

    # Build inventory
    fiber_weight = data.get('fiber_composition', [{}])[0].get('weight_grams', 0) / 1000  # kg

    functional_unit = {
        cotton_activity: fiber_weight
    }

    # Add more processes (spinning, dyeing, etc.)
    # ...

    # Calculate LCA
    lca = LCA(functional_unit)
    lca.lci()
    lca.lcia()

    return {
        "score": lca.score,
        "unit": "kg CO2 eq",
        "processes_used": [cotton_activity['name']],
        "database_sources": ["eufsi_textile_custom", "ecoinvent_391_cutoff"]
    }
```

---

### Step 5.5: Add Custom Process Management Endpoints

**File: `backend/server.py`**

```python
@api_router.get("/custom-processes")
async def list_custom_processes():
    """List all available custom processes."""
    import brightway2 as bw
    bw.projects.set_current("EUFSI_LCA_Tool")

    db = bw.Database('eufsi_textile_custom')
    processes = []

    for activity in db:
        processes.append({
            "id": activity.key[1],
            "name": activity['name'],
            "location": activity.get('location', 'Unknown'),
            "unit": activity.get('unit', 'Unknown'),
            "categories": activity.get('categories', [])
        })

    return {
        "total": len(processes),
        "processes": processes
    }

@api_router.get("/custom-processes/{process_id}")
async def get_custom_process_details(process_id: str):
    """Get detailed information about a custom process."""
    import brightway2 as bw
    bw.projects.set_current("EUFSI_LCA_Tool")

    activity = bw.get_activity(('eufsi_textile_custom', process_id))

    # Get all exchanges
    technosphere = []
    biosphere = []

    for exc in activity.technosphere():
        technosphere.append({
            "name": exc.input['name'],
            "amount": exc['amount'],
            "unit": exc['unit'],
            "database": exc.input.key[0]
        })

    for exc in activity.biosphere():
        biosphere.append({
            "name": exc.input['name'],
            "amount": exc['amount'],
            "unit": exc['unit'],
            "categories": exc.input.get('categories', [])
        })

    return {
        "name": activity['name'],
        "location": activity.get('location'),
        "unit": activity.get('unit'),
        "technosphere_inputs": technosphere,
        "biosphere_exchanges": biosphere
    }
```

---

## Phase 6: Testing & Optimization

**Duration**: 2-3 hours
**Objective**: Validate integration and optimize performance

### Step 6.1: Local Testing

**Test script: `backend/test_custom_processes.py`**

```python
import brightway2 as bw
from bw2calc import LCA
from brightway_setup import initialize_brightway, get_custom_process

# Initialize
initialize_brightway()

# Test 1: List databases
print("Test 1: List databases")
print(list(bw.databases))
assert 'eufsi_textile_custom' in bw.databases
assert 'ecoinvent_391_cutoff' in bw.databases
print("✅ Pass\n")

# Test 2: Get custom process
print("Test 2: Get custom process")
process = get_custom_process("Organic cotton")
print(f"Found: {process['name']}")
print(f"Location: {process.get('location')}")
print("✅ Pass\n")

# Test 3: Run LCA
print("Test 3: Run LCA with custom process")
lca = LCA({process: 1})
lca.lci()
lca.lcia()
print(f"Score: {lca.score} kg CO2 eq")
assert lca.score > 0
print("✅ Pass\n")

# Test 4: Check linking
print("Test 4: Check exchanges are linked")
unlinked = 0
for exc in process.technosphere():
    if exc.input[0] == 'eufsi_textile_custom':
        print(f"⚠️ Unlinked: {exc['name']}")
        unlinked += 1

if unlinked == 0:
    print("✅ All exchanges linked")
else:
    print(f"❌ {unlinked} unlinked exchanges found")

print("\n🎉 All tests passed!")
```

**Run tests:**
```bash
cd backend
python test_custom_processes.py
```

---

### Step 6.2: Performance Benchmarking

```python
import time
import brightway2 as bw
from bw2calc import LCA
from brightway_setup import get_custom_process, get_ecoinvent_activity

# Benchmark custom process
start = time.time()
custom_proc = get_custom_process("Organic cotton")
lca = LCA({custom_proc: 1})
lca.lci()
lca.lcia()
custom_time = time.time() - start

# Benchmark ecoinvent process
start = time.time()
eco_proc = get_ecoinvent_activity("cotton fiber production")
lca = LCA({eco_proc: 1})
lca.lci()
lca.lcia()
eco_time = time.time() - start

print(f"Custom process LCA: {custom_time:.3f}s")
print(f"Ecoinvent process LCA: {eco_time:.3f}s")
print(f"Difference: {abs(custom_time - eco_time):.3f}s")
```

**Expected results:**
- First LCA: 1-3 seconds (database loading)
- Subsequent LCAs: 0.1-0.5 seconds
- Difference should be minimal (<0.1s)

---

### Step 6.3: Deployment Testing

**On Render.com:**

1. **Add Brightway2 to requirements.txt**
```
# backend/requirements.txt
brightway2==2.4.6
bw2io==0.8.10
bw2data==3.6.6
bw2calc==1.8.2
```

2. **Update Dockerfile to include database backup**
```dockerfile
# backend/Dockerfile
COPY data/EUFSI_LCA_Tool.backup.tar.gz /app/data/
```

3. **Add initialization to startup**
Already done in Step 5.3

4. **Test deployment**
- Deploy to Render
- Check logs for "✅ Brightway2 ready"
- Test API endpoint: `GET /custom-processes`
- Test calculation: `POST /api/calculate-lca` with textile data

---

## Technical Architecture

### Database Structure

```
Brightway2 Project: EUFSI_LCA_Tool
├── ecoinvent_391_cutoff (21,238 activities)
│   ├── Cotton fiber production
│   ├── Electricity markets
│   ├── Transport processes
│   └── ... (all ecoinvent processes)
│
├── eufsi_textile_custom (15-50 activities)
│   ├── Organic cotton fiber - India
│   ├── Yarn spinning - Renewable - China
│   ├── Fabric dyeing - ZLD - Bangladesh
│   └── ... (your custom processes)
│
└── biosphere3 (elementary flows)
    ├── Carbon dioxide
    ├── Methane
    └── ... (emissions & resources)
```

### Linking Architecture

```
Custom Process: "Organic cotton fiber - India"
├── Inputs (Technosphere):
│   ├── Electricity, renewable → ecoinvent: "market for electricity, from wind, IN"
│   ├── Water → ecoinvent: "market for water, IN"
│   ├── Pesticides, organic → ecoinvent: "market for pesticide, organic"
│   └── Land use → ecoinvent: "land transformation"
│
└── Outputs (Biosphere):
    ├── CO2 → biosphere3: "Carbon dioxide"
    ├── N2O → biosphere3: "Dinitrogen monoxide"
    └── Water, ground → biosphere3: "Water, groundwater"
```

---

## Risk Mitigation

### Risk 1: Broken Links After Import
**Probability**: High
**Impact**: High
**Mitigation**:
- Export UUIDs correctly from OpenLCA
- Use automated relinking script (Phase 4.4)
- Manual validation for critical processes
- Keep OpenLCA export for reference

### Risk 2: Database Size Too Large for Render
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Use ecoinvent cutoff (smaller than consequential)
- Compress backup with tar.gz (reduces 10 GB → 2 GB)
- Consider external storage (S3) for databases
- Only import essential custom processes

### Risk 3: Calculation Performance
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Cache LCA results for identical inputs
- Pre-calculate common scenarios
- Use background workers for batch calculations
- Optimize inventory building

### Risk 4: Version Mismatch (OpenLCA vs Brightway2)
**Probability**: Low
**Impact**: Low
**Mitigation**:
- Document ecoinvent version (3.9.1)
- Test with sample processes before full import
- Keep OpenLCA as source of truth
- Rebuild if needed

---

## Timeline Estimate

### Development (Local Machine)
- **Day 1**: Export from OpenLCA, Set up Brightway2 (4-6 hours)
- **Day 2**: Import databases, Initial linking (4-6 hours)
- **Day 3**: Manual linking, Validation (4-6 hours)
- **Day 4**: Backend integration (4-6 hours)
- **Day 5**: Testing & optimization (4-6 hours)

**Total Development**: 20-30 hours (5 days part-time or 3 days full-time)

### Deployment
- **Preparation**: Package databases (1 hour)
- **Deploy to Render**: Update configs, deploy (2 hours)
- **Testing**: Validate production (2 hours)

**Total Deployment**: 5 hours

### **Grand Total**: 25-35 hours

---

## Success Criteria

✅ **Phase 1 Complete When**:
- Custom processes exported as JSON-LD
- Export file validated (can open and inspect JSON)

✅ **Phase 2 Complete When**:
- Brightway2 installed and working
- ecoinvent imported successfully (21k+ activities)

✅ **Phase 3 Complete When**:
- Custom processes imported into Brightway2
- Database shows correct number of processes

✅ **Phase 4 Complete When**:
- >95% of exchanges linked to ecoinvent
- Sample LCA runs without errors
- Results match OpenLCA (within 5%)

✅ **Phase 5 Complete When**:
- Backend API can access custom processes
- Calculation function uses custom processes
- New endpoints respond correctly

✅ **Phase 6 Complete When**:
- All automated tests pass
- Performance benchmarks met (<2s per LCA)
- Deployed to production successfully

---

## Next Steps After Implementation

1. **Documentation**:
   - Document which custom processes exist
   - Create user guide for adding new processes
   - Document maintenance procedures

2. **Monitoring**:
   - Track calculation performance
   - Monitor database size
   - Log errors and edge cases

3. **Maintenance**:
   - Update ecoinvent when new version released
   - Add new custom processes as needed
   - Periodic validation against OpenLCA

4. **Future Enhancements**:
   - Add UI for browsing custom processes
   - Allow users to upload their own processes
   - Create process comparison tool
   - Generate process documentation automatically

---

## Resources & References

### Documentation
- Brightway2 Docs: https://docs.brightway.dev/
- OpenLCA JSON-LD: https://github.com/GreenDelta/olca-schema
- ecoinvent: https://ecoinvent.org/

### Python Packages
- `brightway2`: Core framework
- `bw2io`: Import/export
- `bw2data`: Database management
- `bw2calc`: LCA calculations

### Support
- Brightway2 Community: https://brightway.groups.io/
- Stack Overflow: [brightway2] tag

---

## Appendix A: Troubleshooting Guide

### Problem: Import fails with "UUID not found"
**Solution**: Re-export from OpenLCA with UUID preservation enabled

### Problem: Exchanges not linking automatically
**Solution**: Use manual relinking script (Phase 4.3-4.4)

### Problem: LCA calculation gives NaN or 0
**Solution**: Check for circular references or missing characterization factors

### Problem: Database too large for Render
**Solution**: Use external storage (S3/Azure) or switch to VPS

### Problem: Different results than OpenLCA
**Solution**: Compare inventories, check allocation methods, verify impact method

---

## Appendix B: Sample Commands Reference

```python
# Quick reference for common operations

# Switch project
bw.projects.set_current("EUFSI_LCA_Tool")

# List databases
list(bw.databases)

# Search activity
bw.Database('ecoinvent_391_cutoff').search('cotton')

# Get activity by key
bw.get_activity(('database_name', 'activity_code'))

# Run LCA
lca = LCA({activity: 1})
lca.lci()
lca.lcia()
print(lca.score)

# List exchanges
for exc in activity.technosphere():
    print(exc.input['name'], exc['amount'])

# Relink database
bw.Database('eufsi_textile_custom').process()
```

---

**End of Integration Plan**

This plan provides a complete roadmap from OpenLCA export to production deployment. Follow each phase sequentially, validate at each step, and document deviations for future reference.
