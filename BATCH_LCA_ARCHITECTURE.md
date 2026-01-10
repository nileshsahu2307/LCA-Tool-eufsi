# Batch/Multi-SKU LCA Architecture Plan

## Overview
This document outlines the architecture for implementing batch LCA processing capability, allowing users to assess 100+ product SKUs in a single operation.

## Current State
- **Single Product Assessment**: Users can currently assess one product at a time through the web form
- **Manual Data Entry**: Each assessment requires filling out the multi-step form manually
- **No Bulk Import**: No capability to import multiple products simultaneously

## Target State
- **Batch Processing**: Process 100+ SKU assessments in one operation
- **CSV/Excel Import**: Import product data from spreadsheets
- **Parallel Calculation**: Calculate multiple assessments concurrently
- **Bulk Export**: Export all results in a single comprehensive report

---

## Architecture Components

### 1. Frontend: Batch Upload Interface

#### New Page: `/batch-assessment`
Located at: `frontend/src/pages/BatchAssessment.jsx`

**Features**:
- File upload component (CSV/Excel)
- Template download button (pre-formatted CSV with all required columns)
- Data preview table showing imported rows
- Validation status per row (valid/invalid with error messages)
- Progress bar during calculation
- Results summary table

**UI Flow**:
```
1. User selects industry (Textile, Water, Food, etc.)
2. User downloads CSV template for that industry
3. User fills template with product data (100 rows = 100 SKUs)
4. User uploads filled CSV
5. System validates all rows, shows errors if any
6. User clicks "Calculate All"
7. Progress bar shows completion (e.g., "Processing 45/100")
8. Results displayed in sortable table
9. User downloads comprehensive Excel report
```

#### Template Generation
- Generate CSV template dynamically based on selected schema
- Column headers map to field IDs in schema
- Include example row with sample data
- Include data validation rules as comments

---

### 2. Backend: Batch Processing Endpoint

#### New API Endpoint: `POST /api/calculate-batch`

**Request Format**:
```python
{
    "industry": "textile",
    "products": [
        {
            "product_info": {"product_id": "TS-001", ...},
            "raw_materials": [{...}, {...}],
            "yarn_production": {...},
            ...
        },
        {
            "product_info": {"product_id": "TS-002", ...},
            ...
        }
        # ... up to 100+ products
    ]
}
```

**Response Format**:
```python
{
    "batch_id": "batch_20260111_123456",
    "total_products": 100,
    "successful": 98,
    "failed": 2,
    "results": [
        {
            "product_id": "TS-001",
            "status": "success",
            "climate_change_kg_co2eq": 5.234,
            "eutrophication_freshwater": 0.012,
            ...  # All 16 PEF impact categories
        },
        {
            "product_id": "TS-002",
            "status": "failed",
            "error": "Invalid fiber composition: percentages sum to 105%"
        },
        ...
    ],
    "processing_time_seconds": 45.2
}
```

---

### 3. Parallel Processing Strategy

#### Option A: Multi-threading (Recommended for Python)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def calculate_batch(products, industry):
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all calculation jobs
        future_to_product = {
            executor.submit(calculate_single_product, product, industry): product
            for product in products
        }

        # Collect results as they complete
        for future in as_completed(future_to_product):
            product = future_to_product[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "product_id": product.get("product_info", {}).get("product_id"),
                    "status": "failed",
                    "error": str(e)
                })

    return results
```

**Benefits**:
- Utilizes multiple CPU cores
- 10x faster for 100 products (45 seconds vs 450 seconds)
- Python's GIL is not an issue here since Brightway2 calculations are CPU-bound

#### Option B: Celery Task Queue (Future Enhancement)
- Use Celery for asynchronous job processing
- Better for very large batches (1000+ products)
- Requires Redis/RabbitMQ setup
- Allows progress tracking via WebSockets

---

### 4. CSV/Excel Parsing

#### CSV Structure for Textile Industry
```csv
product_id,product_name,product_category,total_weight_grams,fiber_type_1,percentage_1,weight_grams_1,origin_country_1,fiber_type_2,percentage_2,weight_grams_2,origin_country_2,spinning_technology,spinning_location,spinning_electricity_kwh,...
TS-001,Cotton T-Shirt,T-Shirt,180,Cotton (Conventional),100,180,India,,0,0,,Ring Spinning,India,0.35,...
TS-002,Poly Blend Tee,T-Shirt,160,Cotton (Conventional),60,96,India,Polyester (Virgin),40,64,China,Ring Spinning,China,0.32,...
```

**Handling Repeatable Sections**:
- Raw Materials (repeatable, max 8): Use columns `fiber_type_1` through `fiber_type_8`
- Logistics (repeatable, max 6): Use columns `leg_name_1` through `leg_name_6`
- Empty cells = not provided

**Parser Implementation**:
```python
def parse_csv_to_products(csv_file, industry_schema):
    """
    Convert CSV rows into product data structures matching schema format.
    """
    df = pd.read_csv(csv_file)
    products = []

    for _, row in df.iterrows():
        product = {}

        # Parse non-repeatable sections
        product["product_info"] = {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            ...
        }

        # Parse repeatable sections (raw_materials)
        raw_materials = []
        for i in range(1, 9):  # max_items = 8
            fiber_type = row.get(f"fiber_type_{i}")
            if pd.notna(fiber_type):  # Not empty
                raw_materials.append({
                    "fiber_type": fiber_type,
                    "percentage": row[f"percentage_{i}"],
                    "weight_grams": row[f"weight_grams_{i}"],
                    "origin_country": row[f"origin_country_{i}"],
                    ...
                })
        product["raw_materials"] = raw_materials

        products.append(product)

    return products
```

---

### 5. Validation Layer

#### Pre-Calculation Validation
Before running expensive Brightway2 calculations, validate all inputs:

```python
def validate_product(product_data, schema):
    """
    Validate a single product against schema rules.
    Returns: (is_valid, error_messages)
    """
    errors = []

    # Check required fields
    for section in schema["sections"]:
        for field in section["fields"]:
            if field.get("required") and not product_data.get(field["id"]):
                errors.append(f"Missing required field: {field['label']}")

    # Check percentage sums to 100% for raw materials
    if "raw_materials" in product_data:
        total_pct = sum(item["percentage"] for item in product_data["raw_materials"])
        if abs(total_pct - 100) > 0.1:
            errors.append(f"Fiber percentages sum to {total_pct}%, must equal 100%")

    # Check waste percentages sum to 100%
    if "waste_management" in product_data:
        waste_total = (
            product_data["waste_management"].get("waste_recycled", 0) +
            product_data["waste_management"].get("waste_incinerated", 0) +
            product_data["waste_management"].get("waste_landfilled", 0)
        )
        if abs(waste_total - 100) > 0.1:
            errors.append(f"Waste percentages sum to {waste_total}%, must equal 100%")

    return (len(errors) == 0, errors)
```

---

### 6. Results Export

#### Comprehensive Excel Export
Generate multi-sheet Excel workbook:

**Sheet 1: Summary**
- Product ID, Name, Category, Total Weight
- Climate Change (kg CO2eq)
- All 16 PEF impact categories in columns

**Sheet 2: Detailed Breakdown (per product)**
- Life cycle stage contributions
- Process-level contributions
- Similar to current results visualization

**Sheet 3: Input Data**
- All input parameters for reproducibility
- Can be re-imported for future analysis

**Implementation**:
```python
from openpyxl import Workbook

def export_batch_results_to_excel(batch_results, filename):
    wb = Workbook()

    # Sheet 1: Summary
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.append(["Product ID", "Product Name", "Status", "Climate Change (kg CO2eq)", ...])

    for result in batch_results:
        ws_summary.append([
            result["product_id"],
            result.get("product_name", ""),
            result["status"],
            result.get("climate_change_kg_co2eq", "N/A"),
            ...
        ])

    # Sheet 2: Detailed Results
    ws_detail = wb.create_sheet("Detailed Breakdown")
    # ... populate with stage breakdowns

    # Sheet 3: Input Data
    ws_inputs = wb.create_sheet("Input Parameters")
    # ... populate with all input parameters

    wb.save(filename)
    return filename
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Create batch processing endpoint in `server.py`
- [ ] Implement parallel calculation with ThreadPoolExecutor
- [ ] Add validation layer for batch inputs
- [ ] Test with 10-product batch

### Phase 2: CSV Import/Export (Week 2-3)
- [ ] Build CSV template generator (dynamic based on schema)
- [ ] Implement CSV parser with repeatable section handling
- [ ] Build Excel export with multi-sheet format
- [ ] Test with 100-product CSV

### Phase 3: Frontend UI (Week 3-4)
- [ ] Create `BatchAssessment.jsx` page
- [ ] Build file upload component with drag-drop
- [ ] Implement data preview table with validation indicators
- [ ] Add progress tracking during calculation
- [ ] Build results table with sorting/filtering

### Phase 4: Optimization & Polish (Week 4-5)
- [ ] Optimize Brightway2 calculations for batch processing
- [ ] Add caching for repeated calculations (same fiber, same process)
- [ ] Implement error recovery (continue batch even if one fails)
- [ ] Add batch history tracking (save past batches)

---

## Technical Considerations

### 1. Memory Management
- **Issue**: Loading 100 products × 11 sections × ~70 fields = large memory footprint
- **Solution**: Stream CSV parsing, process in chunks of 10 products
- **Solution**: Clear Brightway2 activity cache between products

### 2. Database Locking
- **Issue**: Brightway2 may have database locks with concurrent access
- **Solution**: Use `multiprocessing` with separate database instances per worker
- **Alternative**: Process serially but show progress (slower but simpler)

### 3. Error Handling
- **Issue**: One corrupted product shouldn't fail entire batch
- **Solution**: Wrap each calculation in try-except, continue on failure
- **Solution**: Return partial results with clear error messages

### 4. API Timeout
- **Issue**: 100 products may take 2-3 minutes, HTTP timeout
- **Solution**: Use async processing with batch_id polling
- **Alternative**: Use WebSockets for real-time progress updates

---

## CSV Template Example (Textile)

```csv
# EUFSI LCA Tool - Textile Batch Import Template
# Instructions: Fill one row per product. Empty columns are optional.
# Repeatable sections: Use _1, _2, _3 suffixes (e.g., fiber_type_1, fiber_type_2)

product_id,product_name,product_category,total_weight_grams,description,fiber_type_1,percentage_1,weight_grams_1,origin_country_1,fertilizer_n_kg_1,pesticides_kg_1,irrigation_m3_1,yield_kg_ha_1,fiber_type_2,percentage_2,weight_grams_2,origin_country_2,fertilizer_n_kg_2,pesticides_kg_2,irrigation_m3_2,yield_kg_ha_2,spinning_technology,yarn_count_nm,spinning_location,spinning_electricity_kwh,spinning_renewable_energy,construction_method,construction_location,construction_electricity_kwh,construction_renewable_energy,fabric_waste_rate,dyeing_process_type,color_depth,printing_method,finishing_method,finishing_location,water_consumption_l,thermal_energy_mj,electricity_kwh,wet_renewable_energy,chemicals_kg,onsite_etp,zero_liquid_discharge,factory_location,cutting_waste_rate,sewing_electricity_kwh,manufacturing_renewable_energy,accessories_weight_g,thread_weight_g,finish_treatment_1,finish_treatment_2,primary_packaging_type,primary_packaging_weight_g,secondary_packaging_type,secondary_packaging_weight_g,hangtag_weight_g,waste_recycled,waste_incinerated,waste_landfilled,leg_name_1,distance_km_1,transport_mode_1,leg_name_2,distance_km_2,transport_mode_2,include_use_phase,lifetime_washing_cycles,washing_temperature,washing_machine_type,drying_method,ironing,ironing_minutes,include_end_of_life,reuse_percentage,recycled_percentage,downcycled_percentage,incinerated_percentage,landfill_percentage

TS-001,Basic Cotton Tee,T-Shirt,180,Classic crew neck,Cotton (Conventional),100,180,India,0.05,0.02,1.5,850,,0,0,,,,,Ring Spinning,30,India,0.35,10,Knitting - Circular,India,0.12,15,5,Jet Dyeing,Medium,None,Continuous - natural fibers,India,50,80,0.5,20,0.1,TRUE,FALSE,Bangladesh,12,0.02,10,2,1,None,None,Polybag (LDPE),5,None,0,1,10,70,20,Fiber to Spinning,500,Truck (Diesel),Fabric to Factory,800,Sea Freight (Container),TRUE,50,40,Front-loading,Tumble dry - low,TRUE,5,TRUE,5,10,15,40,30

TS-002,Poly Blend Sport Tee,T-Shirt,160,Performance athletic wear,Cotton (Conventional),60,96,India,0.05,0.02,1.5,850,Polyester (Virgin),40,64,China,,,,,Ring Spinning,35,China,0.32,25,Knitting - Circular,China,0.15,30,4,Jet Dyeing,Dark,Screen Printing,Continuous - synthetic fibers,China,45,75,0.6,35,0.08,TRUE,TRUE,Vietnam,10,0.018,20,3,1.5,None,None,Polybag (Recycled PE),4,Cardboard box,15,2,15,65,20,Fiber to Spinning,600,Truck (Diesel),Fabric to Factory,1200,Sea Freight (Container),TRUE,75,30,Front-loading,Line dry,FALSE,0,TRUE,3,8,12,35,42
```

---

## Success Metrics

### Performance
- Process 100 products in < 60 seconds (with parallelization)
- Support batches up to 500 products
- < 2% failure rate on valid inputs

### Usability
- Template download available for all industries
- Clear validation error messages
- Progress visibility during calculation

### Accuracy
- Batch results match single-product calculations
- All 16 PEF impact categories calculated
- Stage-level breakdown preserved

---

## Future Enhancements

### 1. Comparative Analysis
- Automatically generate comparison charts (Product A vs Product B)
- Identify best/worst performers in batch
- Hotspot analysis across entire product line

### 2. Scenario Modeling
- Run multiple scenarios per product (e.g., renewable energy 0% vs 100%)
- Generate "what-if" reports

### 3. API Integration
- REST API for external systems (ERP, PLM) to submit batches
- Webhook callbacks when calculations complete

### 4. Machine Learning
- Auto-suggest missing data based on similar products
- Anomaly detection (flag unusual inputs)

---

## Conclusion

The batch LCA architecture enables users to:
1. **Scale assessments** from 1 product to 100+ products
2. **Save time** through CSV import vs manual form entry
3. **Ensure consistency** through template-driven data entry
4. **Analyze trends** across product portfolios

This positions the EUFSI LCA Tool as a professional-grade solution for brands and manufacturers conducting comprehensive product portfolio assessments.
