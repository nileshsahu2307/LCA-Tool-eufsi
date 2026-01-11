# Custom Processes Integration Architecture
## How OpenLCA Custom Processes Integrate with EUFSI LCA Tool

**Date**: January 11, 2026
**Purpose**: Detailed architecture for integrating custom textile processes into the EUFSI tool workflow

---

## 🎯 Integration Strategy Overview

Your EUFSI tool will use a **hybrid approach**:

1. **Custom processes** when available (your specialized textile data from OpenLCA)
2. **ecoinvent fallback** when custom processes don't exist
3. **Intelligent selection** based on user input parameters
4. **Transparent reporting** showing which data sources were used

---

## 📊 Current EUFSI Tool Architecture

### Current Workflow (Before Integration)

```
User fills form → Backend receives data → Brightway2 calculation → Results
                                           ↓
                              Search ecoinvent only
                              Build inventory
                              Calculate impacts
```

### New Workflow (After Integration)

```
User fills form → Backend receives data → Process Selector → Brightway2 calculation → Results
                                           ↓                  ↓
                              1. Check custom processes    Use selected processes
                              2. Check criteria match      Build inventory
                              3. Fallback to ecoinvent     Calculate impacts
                              4. Build hybrid inventory    Return + metadata
```

---

## 🔧 Integration Architecture

### 1. Database Layer

**Three Databases Available:**

```python
# In Brightway2 project: "EUFSI_LCA_Tool"

1. ecoinvent_391_cutoff
   - 21,238 activities
   - Global coverage
   - Standard processes
   - ALWAYS available

2. eufsi_textile_custom
   - 15-50 activities (your custom processes)
   - Specialized textile data
   - Country-specific
   - Updated by you

3. biosphere3
   - Elementary flows
   - Standard emissions
   - Used by both above
```

---

### 2. Process Selection Logic

**File**: `backend/process_selector.py` (new file)

```python
"""
Intelligent process selector for hybrid ecoinvent + custom database usage.
"""

import brightway2 as bw
from typing import Dict, Any, Optional, List

class ProcessSelector:
    """
    Selects the best process from custom or ecoinvent databases
    based on user input criteria.
    """

    def __init__(self):
        bw.projects.set_current("EUFSI_LCA_Tool")
        self.custom_db = bw.Database('eufsi_textile_custom')
        self.ecoinvent_db = bw.Database('ecoinvent_391_cutoff')

        # Build process mapping
        self.custom_process_map = self._build_custom_map()

    def _build_custom_map(self) -> Dict[str, List]:
        """
        Build a searchable map of custom processes.

        Returns mapping like:
        {
            'cotton_organic_IN': [activity1, activity2],
            'yarn_spinning_renewable_CN': [activity3],
            ...
        }
        """
        process_map = {}

        for activity in self.custom_db:
            # Create search keys from activity metadata
            fiber_type = activity.get('fiber_type', '').lower()
            location = activity.get('location', '').lower()
            tech = activity.get('technology', '').lower()

            key = f"{fiber_type}_{location}_{tech}".replace(' ', '_')

            if key not in process_map:
                process_map[key] = []
            process_map[key].append(activity)

        return process_map

    def select_fiber_process(
        self,
        fiber_type: str,
        origin_country: str,
        is_organic: bool = False,
        is_recycled: bool = False
    ):
        """
        Select fiber production process.

        Priority:
        1. Custom process matching fiber + country + organic/recycled
        2. Custom process matching fiber + country
        3. ecoinvent process matching fiber + country
        4. ecoinvent global average
        """
        # Try custom database first
        search_keys = [
            f"cotton_organic_{origin_country.lower()}" if is_organic else None,
            f"cotton_recycled_{origin_country.lower()}" if is_recycled else None,
            f"{fiber_type.lower()}_{origin_country.lower()}",
        ]

        for key in search_keys:
            if key and key in self.custom_process_map:
                process = self.custom_process_map[key][0]
                return {
                    'activity': process,
                    'source': 'custom',
                    'name': process['name'],
                    'location': process.get('location'),
                    'confidence': 'high'
                }

        # Fallback to ecoinvent
        search_term = self._build_ecoinvent_search(
            fiber_type, is_organic, is_recycled
        )

        results = self.ecoinvent_db.search(
            search_term,
            filter={'location': origin_country}
        )

        if results:
            return {
                'activity': results[0],
                'source': 'ecoinvent',
                'name': results[0]['name'],
                'location': results[0].get('location'),
                'confidence': 'medium'
            }

        # Global fallback
        results = self.ecoinvent_db.search(search_term)
        if results:
            return {
                'activity': results[0],
                'source': 'ecoinvent_global',
                'name': results[0]['name'],
                'location': results[0].get('location', 'GLO'),
                'confidence': 'low'
            }

        raise ValueError(f"No process found for {fiber_type} in {origin_country}")

    def select_spinning_process(
        self,
        spinning_technology: str,
        location: str,
        renewable_energy_percent: float = 0
    ):
        """
        Select yarn spinning process.

        Uses custom process if renewable energy is specified,
        otherwise uses ecoinvent.
        """
        # If high renewable energy, try custom
        if renewable_energy_percent > 50:
            search_key = f"yarn_spinning_renewable_{location.lower()}"
            if search_key in self.custom_process_map:
                process = self.custom_process_map[search_key][0]
                return {
                    'activity': process,
                    'source': 'custom',
                    'name': process['name'],
                    'location': process.get('location'),
                    'confidence': 'high',
                    'renewable_adjusted': True
                }

        # Fallback to ecoinvent + grid mix adjustment
        tech_map = {
            'Ring Spinning': 'ring spinning',
            'Open End': 'open end spinning',
            'Air Jet': 'air jet spinning',
        }

        search_term = tech_map.get(spinning_technology, 'yarn spinning')
        results = self.ecoinvent_db.search(search_term, filter={'location': location})

        if results:
            return {
                'activity': results[0],
                'source': 'ecoinvent',
                'name': results[0]['name'],
                'location': results[0].get('location'),
                'confidence': 'medium',
                'requires_grid_adjustment': renewable_energy_percent > 0
            }

        raise ValueError(f"No spinning process found for {spinning_technology}")

    def select_dyeing_process(
        self,
        dyeing_type: str,
        color_depth: str,
        location: str,
        has_zld: bool = False
    ):
        """
        Select fabric dyeing process.

        Zero Liquid Discharge (ZLD) processes use custom database.
        """
        # ZLD processes are custom
        if has_zld:
            search_key = f"dyeing_zld_{location.lower()}"
            if search_key in self.custom_process_map:
                process = self.custom_process_map[search_key][0]
                return {
                    'activity': process,
                    'source': 'custom',
                    'name': process['name'],
                    'location': process.get('location'),
                    'confidence': 'high',
                    'zero_liquid_discharge': True
                }

        # Standard dyeing from ecoinvent
        dyeing_map = {
            'Jet Dyeing': 'dyeing',
            'Pad Batch': 'dyeing',
            'Continuous': 'dyeing, continuous'
        }

        search_term = dyeing_map.get(dyeing_type, 'textile dyeing')
        results = self.ecoinvent_db.search(search_term)

        if results:
            return {
                'activity': results[0],
                'source': 'ecoinvent',
                'name': results[0]['name'],
                'location': results[0].get('location'),
                'confidence': 'medium'
            }

        raise ValueError(f"No dyeing process found for {dyeing_type}")

    def _build_ecoinvent_search(
        self,
        fiber_type: str,
        is_organic: bool,
        is_recycled: bool
    ) -> str:
        """Build search term for ecoinvent."""
        base_fiber = fiber_type.lower().replace('(', '').replace(')', '')

        if 'cotton' in base_fiber:
            if is_organic:
                return 'cotton fiber, organic'
            elif is_recycled:
                return 'cotton fiber, recycled'
            else:
                return 'cotton fiber production'
        elif 'polyester' in base_fiber:
            if is_recycled:
                return 'polyester fiber, recycled'
            else:
                return 'polyester fiber production'
        # ... more mappings

        return f"{base_fiber} production"

# Singleton instance
process_selector = ProcessSelector()
```

---

### 3. Enhanced Calculation Function

**File**: `backend/lca_calculator.py` (enhanced)

```python
"""
Enhanced LCA calculator using hybrid custom + ecoinvent processes.
"""

import brightway2 as bw
from bw2calc import LCA
from typing import Dict, Any, List
from process_selector import process_selector

def calculate_textile_lca_hybrid(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate textile LCA using hybrid approach:
    - Custom processes when available
    - ecoinvent fallback
    - Grid mix adjustments for renewable energy
    """
    bw.projects.set_current("EUFSI_LCA_Tool")

    # Track which processes were used
    process_log = []
    inventory = {}

    # ===== 1. FIBER PRODUCTION =====
    for fiber in assessment_data.get('fiber_composition', []):
        fiber_type = fiber.get('fiber_type')
        origin = fiber.get('origin_country')
        percentage = fiber.get('percentage', 0)
        weight_g = fiber.get('weight_grams', 0)

        # Determine if organic/recycled
        is_organic = 'organic' in fiber_type.lower()
        is_recycled = 'recycled' in fiber_type.lower()

        # Select best process
        fiber_process = process_selector.select_fiber_process(
            fiber_type=fiber_type,
            origin_country=origin,
            is_organic=is_organic,
            is_recycled=is_recycled
        )

        # Add to inventory
        weight_kg = weight_g / 1000
        inventory[fiber_process['activity']] = weight_kg

        # Log
        process_log.append({
            'stage': 'Fiber Production',
            'input': f"{fiber_type} - {origin}",
            'process_used': fiber_process['name'],
            'source': fiber_process['source'],
            'confidence': fiber_process['confidence'],
            'amount': weight_kg,
            'unit': 'kg'
        })

    # ===== 2. YARN PRODUCTION (SPINNING) =====
    yarn_data = assessment_data.get('yarn_production', {})
    if yarn_data:
        spinning_process = process_selector.select_spinning_process(
            spinning_technology=yarn_data.get('spinning_technology'),
            location=yarn_data.get('spinning_location'),
            renewable_energy_percent=yarn_data.get('spinning_renewable_energy', 0)
        )

        # Get total fiber weight for yarn input
        total_fiber_weight = sum(
            f.get('weight_grams', 0) for f in assessment_data.get('fiber_composition', [])
        ) / 1000

        inventory[spinning_process['activity']] = total_fiber_weight

        # If renewable energy adjustment needed
        if spinning_process.get('requires_grid_adjustment'):
            electricity_kwh = yarn_data.get('spinning_electricity_kwh', 0) * total_fiber_weight
            renewable_pct = yarn_data.get('spinning_renewable_energy', 0)

            # Add renewable electricity
            renewable_elec = get_renewable_electricity(
                location=yarn_data.get('spinning_location'),
                amount_kwh=electricity_kwh * (renewable_pct / 100)
            )
            inventory[renewable_elec] = electricity_kwh * (renewable_pct / 100)

            # Add grid electricity
            grid_elec = get_grid_electricity(
                location=yarn_data.get('spinning_location'),
                amount_kwh=electricity_kwh * (1 - renewable_pct / 100)
            )
            inventory[grid_elec] = electricity_kwh * (1 - renewable_pct / 100)

        process_log.append({
            'stage': 'Yarn Production',
            'input': yarn_data.get('spinning_technology'),
            'process_used': spinning_process['name'],
            'source': spinning_process['source'],
            'confidence': spinning_process['confidence'],
            'amount': total_fiber_weight,
            'unit': 'kg'
        })

    # ===== 3. FABRIC CONSTRUCTION =====
    fabric_data = assessment_data.get('fabric_construction', {})
    if fabric_data:
        # Use ecoinvent for fabric construction (usually no custom)
        construction_method = fabric_data.get('construction_method')
        construction_activity = get_ecoinvent_construction(construction_method)

        inventory[construction_activity] = total_fiber_weight

        process_log.append({
            'stage': 'Fabric Construction',
            'input': construction_method,
            'process_used': construction_activity['name'],
            'source': 'ecoinvent',
            'confidence': 'medium',
            'amount': total_fiber_weight,
            'unit': 'kg'
        })

    # ===== 4. WET PROCESSING (DYEING) =====
    wet_data = assessment_data.get('wet_processing', {})
    if wet_data:
        dyeing_process = process_selector.select_dyeing_process(
            dyeing_type=wet_data.get('dyeing_process_type'),
            color_depth=wet_data.get('color_depth'),
            location=wet_data.get('finishing_location'),
            has_zld=wet_data.get('zero_liquid_discharge', False)
        )

        inventory[dyeing_process['activity']] = total_fiber_weight

        process_log.append({
            'stage': 'Wet Processing',
            'input': wet_data.get('dyeing_process_type'),
            'process_used': dyeing_process['name'],
            'source': dyeing_process['source'],
            'confidence': dyeing_process['confidence'],
            'amount': total_fiber_weight,
            'unit': 'kg',
            'special': 'ZLD' if dyeing_process.get('zero_liquid_discharge') else None
        })

    # ===== 5. MANUFACTURING (CMT) =====
    # Usually ecoinvent for cut-make-trim
    # (unless you have custom CMT processes)

    # ===== 6. PACKAGING =====
    # ecoinvent for packaging materials

    # ===== 7. TRANSPORTATION =====
    # ecoinvent for transport

    # ===== RUN LCA CALCULATION =====
    lca = LCA(inventory)
    lca.lci()
    lca.lcia()

    # Calculate detailed impacts
    impact_results = {}
    for method in get_impact_methods():
        lca.switch_method(method)
        lca.lcia()
        impact_results[method[2]] = {
            'value': lca.score,
            'unit': get_method_unit(method)
        }

    # ===== PREPARE RESPONSE =====
    return {
        'total_score': lca.score,
        'unit': 'kg CO2 eq',
        'impacts': impact_results,
        'process_log': process_log,
        'database_summary': {
            'custom_processes_used': len([p for p in process_log if p['source'] == 'custom']),
            'ecoinvent_processes_used': len([p for p in process_log if p['source'] == 'ecoinvent']),
            'total_processes': len(process_log)
        },
        'data_quality': calculate_data_quality(process_log),
        'transparency': {
            'custom_data_coverage': calculate_custom_coverage(process_log),
            'confidence_score': calculate_confidence_score(process_log)
        }
    }

def calculate_data_quality(process_log: List[Dict]) -> str:
    """Calculate overall data quality based on sources used."""
    custom_count = len([p for p in process_log if p['source'] == 'custom'])
    total = len(process_log)

    custom_pct = (custom_count / total * 100) if total > 0 else 0

    if custom_pct >= 70:
        return "Excellent (70%+ custom data)"
    elif custom_pct >= 40:
        return "Good (40-70% custom data)"
    elif custom_pct >= 20:
        return "Fair (20-40% custom data)"
    else:
        return "Standard (ecoinvent baseline)"

def calculate_custom_coverage(process_log: List[Dict]) -> float:
    """Calculate percentage of custom data used."""
    custom_count = len([p for p in process_log if p['source'] == 'custom'])
    total = len(process_log)
    return (custom_count / total * 100) if total > 0 else 0

def calculate_confidence_score(process_log: List[Dict]) -> float:
    """
    Calculate confidence score based on:
    - High confidence (custom, exact match): 1.0
    - Medium confidence (ecoinvent, country match): 0.6
    - Low confidence (ecoinvent, global): 0.3
    """
    confidence_map = {'high': 1.0, 'medium': 0.6, 'low': 0.3}

    total_confidence = sum(
        confidence_map.get(p.get('confidence', 'medium'), 0.6)
        for p in process_log
    )

    return (total_confidence / len(process_log) * 100) if process_log else 0
```

---

### 4. API Integration

**File**: `backend/server.py` (enhanced endpoints)

```python
from lca_calculator import calculate_textile_lca_hybrid
from process_selector import process_selector

# ===== EXISTING ENDPOINT (ENHANCED) =====
@api_router.post("/api/calculate-lca")
async def calculate_lca(request: LCARequest):
    """
    Enhanced LCA calculation with custom process support.
    """
    try:
        # Use hybrid calculator
        result = calculate_textile_lca_hybrid(request.data)

        # Save to database
        assessment_id = await save_assessment(request.data, result)

        return {
            "status": "success",
            "assessment_id": assessment_id,
            "results": result,
            "metadata": {
                "custom_processes_used": result['database_summary']['custom_processes_used'],
                "data_quality": result['data_quality'],
                "confidence_score": result['transparency']['confidence_score']
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== NEW ENDPOINT: List Custom Processes =====
@api_router.get("/api/custom-processes")
async def list_custom_processes():
    """
    List all available custom processes.
    Users can see what custom data is available.
    """
    import brightway2 as bw
    bw.projects.set_current("EUFSI_LCA_Tool")

    db = bw.Database('eufsi_textile_custom')
    processes = []

    for activity in db:
        processes.append({
            "id": activity.key[1],
            "name": activity['name'],
            "location": activity.get('location', 'Unknown'),
            "category": activity.get('categories', [''])[0] if activity.get('categories') else 'Uncategorized',
            "unit": activity.get('unit', 'kg'),
            "description": activity.get('comment', '')
        })

    return {
        "total": len(processes),
        "processes": sorted(processes, key=lambda x: x['name'])
    }

# ===== NEW ENDPOINT: Process Details =====
@api_router.get("/api/custom-processes/{process_id}")
async def get_process_details(process_id: str):
    """
    Get detailed information about a specific custom process.
    Shows inputs, outputs, and data sources.
    """
    import brightway2 as bw
    bw.projects.set_current("EUFSI_LCA_Tool")

    try:
        activity = bw.get_activity(('eufsi_textile_custom', process_id))
    except:
        raise HTTPException(status_code=404, detail="Process not found")

    # Get technosphere inputs (from ecoinvent)
    technosphere = []
    for exc in activity.technosphere():
        technosphere.append({
            "name": exc.input['name'],
            "amount": exc['amount'],
            "unit": exc['unit'],
            "database": exc.input.key[0],
            "location": exc.input.get('location', 'Unknown')
        })

    # Get biosphere flows (emissions)
    biosphere = []
    for exc in activity.biosphere():
        biosphere.append({
            "name": exc.input['name'],
            "amount": exc['amount'],
            "unit": exc['unit'],
            "categories": exc.input.get('categories', [])
        })

    return {
        "id": process_id,
        "name": activity['name'],
        "location": activity.get('location'),
        "unit": activity.get('unit'),
        "description": activity.get('comment', ''),
        "technosphere_inputs": technosphere,
        "biosphere_flows": biosphere,
        "linked_to_ecoinvent": len([e for e in technosphere if e['database'] == 'ecoinvent_391_cutoff'])
    }

# ===== NEW ENDPOINT: Process Comparison =====
@api_router.post("/api/compare-processes")
async def compare_processes(request: CompareRequest):
    """
    Compare custom process vs ecoinvent equivalent.
    Shows impact difference.
    """
    import brightway2 as bw
    from bw2calc import LCA

    bw.projects.set_current("EUFSI_LCA_Tool")

    # Get both processes
    custom_process = bw.get_activity(('eufsi_textile_custom', request.custom_id))
    eco_process = bw.get_activity(('ecoinvent_391_cutoff', request.ecoinvent_id))

    # Calculate LCA for both
    lca_custom = LCA({custom_process: 1})
    lca_custom.lci()
    lca_custom.lcia()

    lca_eco = LCA({eco_process: 1})
    lca_eco.lci()
    lca_eco.lcia()

    # Calculate difference
    difference = lca_custom.score - lca_eco.score
    pct_difference = (difference / lca_eco.score * 100) if lca_eco.score != 0 else 0

    return {
        "custom_process": {
            "name": custom_process['name'],
            "score": lca_custom.score,
            "unit": "kg CO2 eq"
        },
        "ecoinvent_process": {
            "name": eco_process['name'],
            "score": lca_eco.score,
            "unit": "kg CO2 eq"
        },
        "comparison": {
            "absolute_difference": difference,
            "percentage_difference": pct_difference,
            "interpretation": "Custom process has lower impact" if difference < 0 else "Custom process has higher impact"
        }
    }
```

---

### 5. Frontend Integration

**Enhanced Results Display**

**File**: `frontend/src/pages/Results.jsx` (enhanced)

```jsx
// Show which processes were used
const ProcessLog = ({ processLog }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Processes Used</CardTitle>
        <CardDescription>
          Detailed breakdown of data sources
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Stage</TableHead>
              <TableHead>Process</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {processLog.map((process, idx) => (
              <TableRow key={idx}>
                <TableCell>{process.stage}</TableCell>
                <TableCell>{process.process_used}</TableCell>
                <TableCell>
                  <Badge variant={process.source === 'custom' ? 'success' : 'default'}>
                    {process.source}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={
                    process.confidence === 'high' ? 'success' :
                    process.confidence === 'medium' ? 'warning' : 'secondary'
                  }>
                    {process.confidence}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

// Show data quality metrics
const DataQuality = ({ databaseSummary, transparency }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Quality & Transparency</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Custom Data Coverage</Label>
          <Progress value={transparency.custom_data_coverage} className="mt-2" />
          <p className="text-sm text-muted-foreground mt-1">
            {transparency.custom_data_coverage.toFixed(1)}% of processes use custom data
          </p>
        </div>

        <div>
          <Label>Confidence Score</Label>
          <Progress value={transparency.confidence_score} className="mt-2" />
          <p className="text-sm text-muted-foreground mt-1">
            {transparency.confidence_score.toFixed(1)}% overall confidence
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="border rounded-lg p-3">
            <p className="text-sm font-medium">Custom Processes</p>
            <p className="text-2xl font-bold">{databaseSummary.custom_processes_used}</p>
          </div>
          <div className="border rounded-lg p-3">
            <p className="text-sm font-medium">ecoinvent Processes</p>
            <p className="text-2xl font-bold">{databaseSummary.ecoinvent_processes_used}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## 🎯 User Experience Flow

### Scenario 1: User Has All Custom Process Matches

**Input:**
```
Fiber: Organic Cotton
Origin: India
Spinning: Renewable Energy 80%
Dyeing: Zero Liquid Discharge
```

**What Happens:**
1. System finds custom "Organic cotton fiber - India"
2. System finds custom "Yarn spinning renewable - India"
3. System finds custom "Dyeing ZLD - India"
4. All 3 use custom processes ✅
5. Results show "Excellent data quality (100% custom)"
6. High confidence score (100%)

---

### Scenario 2: User Has Partial Match

**Input:**
```
Fiber: Conventional Cotton
Origin: Bangladesh
Spinning: Ring Spinning
Dyeing: Jet Dyeing
```

**What Happens:**
1. System doesn't find custom cotton for Bangladesh → uses ecoinvent
2. System doesn't find custom spinning → uses ecoinvent + grid adjustment
3. System doesn't find custom dyeing → uses ecoinvent
4. All 3 use ecoinvent fallback
5. Results show "Standard data quality (ecoinvent baseline)"
6. Medium confidence score (60%)

---

### Scenario 3: Hybrid Approach

**Input:**
```
Fiber: Organic Cotton
Origin: India
Spinning: Ring Spinning
Dyeing: Zero Liquid Discharge
```

**What Happens:**
1. System finds custom "Organic cotton - India" ✅
2. System doesn't find custom spinning → uses ecoinvent
3. System finds custom "Dyeing ZLD" ✅
4. Mixed: 2 custom, 1 ecoinvent
5. Results show "Good data quality (67% custom)"
6. High-medium confidence score (80%)

---

## 📊 Batch Processing Integration

**For CSV batch uploads**, the same logic applies:

```python
# In batch calculation
for product in products:
    # Each product uses hybrid selector
    result = calculate_textile_lca_hybrid(product)

    # Results include custom/ecoinvent breakdown
    results.append({
        'product_id': product['product_id'],
        'score': result['total_score'],
        'custom_coverage': result['transparency']['custom_data_coverage'],
        'data_quality': result['data_quality']
    })

# Aggregate statistics
batch_summary = {
    'avg_custom_coverage': mean([r['custom_coverage'] for r in results]),
    'products_with_custom_data': len([r for r in results if r['custom_coverage'] > 0]),
    'data_quality_distribution': {
        'excellent': len([r for r in results if 'Excellent' in r['data_quality']]),
        'good': len([r for r in results if 'Good' in r['data_quality']]),
        'fair': len([r for r in results if 'Fair' in r['data_quality']]),
        'standard': len([r for r in results if 'Standard' in r['data_quality']])
    }
}
```

---

## 🔄 Update Workflow

### Adding New Custom Processes

**Step 1**: Create in OpenLCA
```
1. Build new process in OpenLCA
2. Link to ecoinvent background data
3. Validate calculations
```

**Step 2**: Export & Import
```bash
# Export from OpenLCA (JSON-LD)
# Import to Brightway2
python update_custom_processes.py new_process.zip
```

**Step 3**: Update Process Map
```python
# Automatically rebuilds on import
# Or manually:
from process_selector import process_selector
process_selector._build_custom_map()
```

**Step 4**: Deploy
```bash
# Backup updated database
# Deploy to Render
# Test with sample calculation
```

**No code changes needed!**

---

## 🎨 Benefits of This Architecture

### For Users
✅ **Transparent**: See exactly which data sources are used
✅ **Automatic**: System picks best process automatically
✅ **Flexible**: Works with any combination of custom/standard data
✅ **Quality metrics**: Clear data quality indicators

### For You (Developer/Owner)
✅ **Maintainable**: Add processes without code changes
✅ **Scalable**: Easy to expand custom database
✅ **Testable**: Clear separation of concerns
✅ **Auditable**: Full process logging

### For Data Quality
✅ **Best available data**: Always uses most specific process
✅ **Confidence tracking**: Know reliability of results
✅ **Fallback safety**: Never fails due to missing custom data
✅ **Comparative analysis**: Compare custom vs standard

---

## 📈 Future Enhancements

### Phase 2 Features (After Initial Integration)

1. **Process Recommendation Engine**
   - Suggest which custom processes to create
   - Based on user input patterns
   - Identify high-impact gaps

2. **Custom Process Upload UI**
   - Allow users to upload their own processes
   - Validation and approval workflow
   - Community database

3. **Real-time Process Comparison**
   - Side-by-side comparison in results
   - Show impact difference
   - Explain why custom is different

4. **Data Quality Dashboard**
   - Track custom coverage over time
   - Identify most-used processes
   - Highlight gaps in custom database

5. **Automated Updates**
   - Sync with OpenLCA database
   - Incremental updates (not full re-import)
   - Version control for processes

---

## 🔐 Security & Validation

### Data Integrity Checks

```python
def validate_custom_process(activity):
    """
    Validate custom process before using in calculations.
    """
    checks = {
        'has_name': bool(activity.get('name')),
        'has_location': bool(activity.get('location')),
        'has_unit': bool(activity.get('unit')),
        'has_exchanges': len(list(activity.exchanges())) > 0,
        'linked_to_ecoinvent': any(
            exc.input.key[0] == 'ecoinvent_391_cutoff'
            for exc in activity.technosphere()
        ),
        'no_circular_references': check_no_circular(activity)
    }

    if not all(checks.values()):
        raise ValidationError(f"Process {activity['name']} failed validation: {checks}")

    return True
```

---

## 📋 Summary

This integration architecture provides:

1. **Intelligent Process Selection**: Automatically chooses best data source
2. **Hybrid Database**: Combines your custom OpenLCA processes with ecoinvent
3. **Transparent Results**: Users see exactly which data was used
4. **Quality Metrics**: Confidence scores and data quality indicators
5. **Zero User Friction**: Works seamlessly with existing UI
6. **Maintainable**: Add processes without code changes
7. **Scalable**: Easy to expand custom database over time

The user fills the same form, but gets better results when custom data is available, with full transparency about data sources.

---

**End of Integration Architecture Document**
