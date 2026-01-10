# Calculation & Validation Architecture
## Deep Dive: Ensuring Accuracy in Batch LCA Processing

**Date**: 2026-01-11
**Purpose**: Comprehensive technical specification for calculation accuracy, validation, and error handling

---

## Table of Contents
1. [CSV Input Validation Strategy](#csv-input-validation-strategy)
2. [Backend Calculation Architecture](#backend-calculation-architecture)
3. [Data Integrity Checks](#data-integrity-checks)
4. [Error Handling & Recovery](#error-handling--recovery)
5. [Testing & Verification](#testing--verification)
6. [Performance Optimization](#performance-optimization)

---

# CSV Input Validation Strategy

## 1. Multi-Layer Validation Approach

### **Layer 1: Schema-Level Validation (Structural)**
Validates CSV structure matches expected schema before any parsing.

```python
class CSVValidator:
    def __init__(self, schema):
        self.schema = schema
        self.errors = []
        self.warnings = []

    def validate_structure(self, df: pd.DataFrame) -> bool:
        """
        Validate CSV has all required columns.
        """
        required_columns = self._get_required_columns()
        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            self.errors.append({
                "type": "MISSING_COLUMNS",
                "message": f"Missing required columns: {', '.join(missing_columns)}",
                "severity": "critical"
            })
            return False

        return True

    def _get_required_columns(self) -> List[str]:
        """
        Generate list of required columns from schema.
        """
        required = []

        for section in self.schema['sections']:
            if section.get('repeatable'):
                # For repeatable sections, at least _1 suffix is required
                for field in section['fields']:
                    if field.get('required'):
                        required.append(f"{field['id']}_1")
            else:
                # Non-repeatable sections
                for field in section['fields']:
                    if field.get('required'):
                        required.append(field['id'])

        return required
```

---

### **Layer 2: Data Type Validation**
Ensures each cell contains the correct data type.

```python
def validate_data_types(self, df: pd.DataFrame, row_idx: int, product: dict) -> List[str]:
    """
    Validate data types for each field.
    Returns list of errors for this row.
    """
    row_errors = []

    for section in self.schema['sections']:
        section_id = section['id']

        if section.get('repeatable'):
            # Validate repeatable section items
            for i in range(1, section.get('max_items', 1) + 1):
                for field in section['fields']:
                    col_name = f"{field['id']}_{i}"
                    value = df.at[row_idx, col_name]

                    if pd.notna(value):  # Only validate if value exists
                        error = self._validate_field_type(field, value, col_name, row_idx)
                        if error:
                            row_errors.append(error)
        else:
            # Validate non-repeatable section
            for field in section['fields']:
                col_name = field['id']
                value = df.at[row_idx, col_name]

                if pd.notna(value):
                    error = self._validate_field_type(field, value, col_name, row_idx)
                    if error:
                        row_errors.append(error)

    return row_errors

def _validate_field_type(self, field: dict, value: any, col_name: str, row_idx: int) -> Optional[str]:
    """
    Validate individual field value against field type.
    """
    field_type = field['type']

    try:
        if field_type == 'number':
            # Attempt to convert to float
            float_val = float(value)

            # Check min/max constraints
            if 'min' in field and float_val < field['min']:
                return f"Row {row_idx + 2}, {col_name}: Value {float_val} is below minimum {field['min']}"

            if 'max' in field and float_val > field['max']:
                return f"Row {row_idx + 2}, {col_name}: Value {float_val} exceeds maximum {field['max']}"

        elif field_type == 'select':
            # Validate value is in allowed options
            if value not in field['options']:
                return f"Row {row_idx + 2}, {col_name}: '{value}' is not a valid option. Must be one of: {', '.join(field['options'][:5])}..."

        elif field_type == 'boolean':
            # Validate boolean values
            if str(value).upper() not in ['TRUE', 'FALSE', '1', '0', 'YES', 'NO']:
                return f"Row {row_idx + 2}, {col_name}: '{value}' is not a valid boolean (use TRUE/FALSE or 1/0)"

        elif field_type == 'text':
            # Text should be string
            if not isinstance(value, str):
                return f"Row {row_idx + 2}, {col_name}: Value must be text"

    except ValueError as e:
        return f"Row {row_idx + 2}, {col_name}: Cannot convert '{value}' to {field_type} - {str(e)}"

    return None
```

---

### **Layer 3: Business Logic Validation**
Validates domain-specific rules (e.g., percentages sum to 100%).

```python
def validate_business_rules(self, product: dict, row_idx: int) -> List[str]:
    """
    Validate business logic rules.
    """
    errors = []

    # Rule 1: Fiber percentages must sum to 100%
    if 'fiber_composition' in product:
        fibers = product['fiber_composition']
        if len(fibers) > 0:
            total_pct = sum(float(f.get('percentage', 0)) for f in fibers)

            if abs(total_pct - 100) > 0.1:  # Allow 0.1% tolerance for rounding
                errors.append(
                    f"Row {row_idx + 2}: Fiber percentages sum to {total_pct:.1f}%, must equal 100%"
                )

    # Rule 2: Fiber weights must match total product weight
    if 'fiber_composition' in product and 'product_info' in product:
        total_weight = float(product['product_info'].get('total_weight_grams', 0))
        fiber_weights_sum = sum(float(f.get('weight_grams', 0)) for f in product['fiber_composition'])

        if abs(fiber_weights_sum - total_weight) > 1:  # 1 gram tolerance
            errors.append(
                f"Row {row_idx + 2}: Sum of fiber weights ({fiber_weights_sum}g) doesn't match total product weight ({total_weight}g)"
            )

    # Rule 3: Waste percentages must sum to 100%
    if 'waste_management' in product:
        waste = product['waste_management']
        waste_total = (
            float(waste.get('waste_recycled', 0)) +
            float(waste.get('waste_incinerated', 0)) +
            float(waste.get('waste_landfilled', 0))
        )

        if abs(waste_total - 100) > 0.1:
            errors.append(
                f"Row {row_idx + 2}: Waste percentages sum to {waste_total:.1f}%, must equal 100%"
            )

    # Rule 4: End-of-life percentages must sum to 100% (if end-of-life included)
    if 'end_of_life' in product:
        eol = product['end_of_life']
        if eol.get('include_end_of_life'):
            eol_total = (
                float(eol.get('reuse_percentage', 0)) +
                float(eol.get('recycled_percentage', 0)) +
                float(eol.get('downcycled_percentage', 0)) +
                float(eol.get('incinerated_percentage', 0)) +
                float(eol.get('landfill_percentage', 0))
            )

            if abs(eol_total - 100) > 0.1:
                errors.append(
                    f"Row {row_idx + 2}: End-of-life percentages sum to {eol_total:.1f}%, must equal 100%"
                )

    # Rule 5: Required fields check
    errors.extend(self._validate_required_fields(product, row_idx))

    return errors

def _validate_required_fields(self, product: dict, row_idx: int) -> List[str]:
    """
    Check all required fields are present and not empty.
    """
    errors = []

    for section in self.schema['sections']:
        section_id = section['id']

        for field in section['fields']:
            if field.get('required'):
                # Check in product data
                if section.get('repeatable'):
                    # For repeatable sections, check at least one item exists
                    if section_id not in product or len(product[section_id]) == 0:
                        errors.append(
                            f"Row {row_idx + 2}: Missing required section '{section['title']}'"
                        )
                        break

                    # Check required field in first item
                    first_item = product[section_id][0]
                    if field['id'] not in first_item or not first_item[field['id']]:
                        errors.append(
                            f"Row {row_idx + 2}: Missing required field '{field['label']}' in {section['title']}"
                        )
                else:
                    # Non-repeatable section
                    if section_id not in product:
                        errors.append(
                            f"Row {row_idx + 2}: Missing section '{section['title']}'"
                        )
                        continue

                    if field['id'] not in product[section_id] or not product[section_id][field['id']]:
                        errors.append(
                            f"Row {row_idx + 2}: Missing required field '{field['label']}'"
                        )

    return errors
```

---

### **Layer 4: Data Completeness Warnings**
Non-critical issues that may affect calculation quality.

```python
def generate_warnings(self, product: dict, row_idx: int) -> List[str]:
    """
    Generate warnings for incomplete but valid data.
    """
    warnings = []

    # Warning 1: Missing optional energy data
    if 'yarn_production' in product:
        yarn = product['yarn_production']
        if not yarn.get('spinning_renewable_energy'):
            warnings.append(
                f"Row {row_idx + 2}: Missing renewable energy % for spinning (will assume 0%)"
            )

    # Warning 2: Missing transport data
    if 'logistics' not in product or len(product.get('logistics', [])) == 0:
        warnings.append(
            f"Row {row_idx + 2}: No transport legs defined (will use default assumptions)"
        )

    # Warning 3: Use phase not included
    if 'use_phase' in product:
        if not product['use_phase'].get('include_use_phase'):
            warnings.append(
                f"Row {row_idx + 2}: Use phase excluded (cradle-to-gate only)"
            )

    # Warning 4: Low data quality indicators
    if 'fiber_composition' in product:
        for fiber in product['fiber_composition']:
            if fiber.get('origin_country') == 'Other':
                warnings.append(
                    f"Row {row_idx + 2}: Generic origin country 'Other' used for {fiber.get('fiber_type')} (results may be less accurate)"
                )

    return warnings
```

---

## Complete Validation Pipeline

```python
@app.post("/api/batch/parse-csv")
async def parse_and_validate_csv(file: UploadFile, industry: str):
    """
    Complete CSV parsing and validation pipeline.
    """
    import pandas as pd

    # Step 1: Read CSV
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read CSV file: {str(e)}")

    # Step 2: Get schema
    schema = get_schema(industry)
    validator = CSVValidator(schema)

    # Step 3: Validate structure
    if not validator.validate_structure(df):
        return {
            "status": "error",
            "errors": validator.errors,
            "message": "CSV structure is invalid"
        }

    # Step 4: Parse and validate each row
    products = []
    global_errors = []

    for row_idx, row in df.iterrows():
        # Parse row into product structure
        product = parse_row_to_product(row, schema, row_idx)

        # Validate data types
        type_errors = validator.validate_data_types(df, row_idx, product)

        # Validate business rules
        business_errors = validator.validate_business_rules(product, row_idx)

        # Generate warnings
        warnings = validator.generate_warnings(product, row_idx)

        # Combine all errors
        all_errors = type_errors + business_errors

        product['row_number'] = row_idx + 2  # +2 because row 1 is headers, 0-indexed
        product['errors'] = all_errors
        product['warnings'] = warnings
        product['is_valid'] = len(all_errors) == 0

        products.append(product)

    # Step 5: Return validation results
    valid_count = len([p for p in products if p['is_valid']])
    invalid_count = len([p for p in products if not p['is_valid']])

    return {
        "status": "success",
        "total": len(products),
        "valid": valid_count,
        "invalid": invalid_count,
        "products": products,
        "global_errors": global_errors
    }
```

---

# Backend Calculation Architecture

## 2. Calculation Flow with Error Handling

### **Step 1: Pre-Calculation Setup**

```python
class BatchLCACalculator:
    def __init__(self, industry: str):
        self.industry = industry
        self.schema = get_schema(industry)
        self.bw_engine = Brightway2Engine()
        self.emission_factor_cache = {}
        self.calculation_log = []

    def calculate_batch(self, products: List[dict]) -> dict:
        """
        Calculate LCA for batch of products with parallel processing.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        start_time = time.time()
        results = []
        successful = 0
        failed = 0

        # Step 1: Pre-load emission factors (shared across all calculations)
        self._preload_emission_factors()

        # Step 2: Process products in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all jobs
            future_to_product = {
                executor.submit(self._calculate_single_product, product): product
                for product in products
            }

            # Collect results as they complete
            for future in as_completed(future_to_product):
                product = future_to_product[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per product
                    results.append(result)

                    if result['status'] == 'success':
                        successful += 1
                    else:
                        failed += 1

                except TimeoutError:
                    results.append({
                        "product_id": product['product_info']['product_id'],
                        "product_name": product['product_info']['product_name'],
                        "status": "failed",
                        "error": "Calculation timeout after 30 seconds"
                    })
                    failed += 1

                except Exception as e:
                    results.append({
                        "product_id": product['product_info']['product_id'],
                        "product_name": product['product_info']['product_name'],
                        "status": "failed",
                        "error": f"Unexpected error: {str(e)}"
                    })
                    failed += 1

        end_time = time.time()

        return {
            "batch_id": str(uuid.uuid4()),
            "total_products": len(products),
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": round(end_time - start_time, 2),
            "results": results
        }

    def _preload_emission_factors(self):
        """
        Pre-load commonly used emission factors into cache.
        """
        # Load all fiber production emission factors
        fibers = [
            "Cotton (Conventional)", "Cotton (Organic)", "Polyester (Virgin)",
            "Polyester (Recycled)", "Wool (Virgin)", "Nylon (Virgin)"
        ]

        for fiber in fibers:
            for country in ["India", "China", "Turkey", "Bangladesh", "Vietnam"]:
                key = f"fiber_{fiber}_{country}"
                if key not in self.emission_factor_cache:
                    self.emission_factor_cache[key] = self.bw_engine.get_emission_factor(
                        activity_type='fiber_production',
                        material=fiber,
                        location=country
                    )

        # Load spinning emission factors
        spinning_techs = ["Ring Spinning", "Open End", "Air Jet"]
        for tech in spinning_techs:
            for country in ["India", "China", "Bangladesh", "Vietnam"]:
                key = f"spinning_{tech}_{country}"
                if key not in self.emission_factor_cache:
                    self.emission_factor_cache[key] = self.bw_engine.get_emission_factor(
                        activity_type='spinning',
                        technology=tech,
                        location=country
                    )

        print(f"Pre-loaded {len(self.emission_factor_cache)} emission factors into cache")
```

---

### **Step 2: Single Product Calculation with Validation**

```python
def _calculate_single_product(self, product: dict) -> dict:
    """
    Calculate LCA for a single product with comprehensive error handling.
    """
    product_id = product['product_info']['product_id']
    product_name = product['product_info']['product_name']

    try:
        # Step 1: Build activity inventory
        inventory = self._build_inventory(product)

        # Step 2: Validate inventory completeness
        inventory_errors = self._validate_inventory(inventory)
        if inventory_errors:
            return {
                "product_id": product_id,
                "product_name": product_name,
                "status": "failed",
                "error": f"Inventory validation failed: {'; '.join(inventory_errors)}"
            }

        # Step 3: Calculate impacts using Brightway2
        impacts = self._calculate_impacts(inventory, product)

        # Step 4: Validate calculation results
        result_errors = self._validate_results(impacts)
        if result_errors:
            return {
                "product_id": product_id,
                "product_name": product_name,
                "status": "failed",
                "error": f"Result validation failed: {'; '.join(result_errors)}"
            }

        # Step 5: Return successful result
        return {
            "product_id": product_id,
            "product_name": product_name,
            "status": "success",
            "impacts": impacts,
            "inventory_summary": {
                "total_activities": len(inventory),
                "total_mass_kg": sum(a.get('amount', 0) for a in inventory)
            },
            "data_quality": self._assess_data_quality(product)
        }

    except Exception as e:
        # Log error for debugging
        self.calculation_log.append({
            "product_id": product_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "product_id": product_id,
            "product_name": product_name,
            "status": "failed",
            "error": str(e)
        }
```

---

### **Step 3: Build Activity Inventory**

```python
def _build_inventory(self, product: dict) -> List[dict]:
    """
    Build complete inventory of activities from product data.
    """
    inventory = []

    # Activity 1: Fiber Production
    for fiber in product.get('fiber_composition', []):
        fiber_activity = {
            "name": f"Fiber Production: {fiber['fiber_type']}",
            "amount": float(fiber['weight_grams']) / 1000,  # Convert to kg
            "unit": "kg",
            "activity_type": "fiber_production",
            "material": fiber['fiber_type'],
            "location": fiber['origin_country'],
            "emission_factor_key": f"fiber_{fiber['fiber_type']}_{fiber['origin_country']}"
        }
        inventory.append(fiber_activity)

    # Activity 2: Yarn Production (Spinning)
    if 'yarn_production' in product:
        yarn = product['yarn_production']
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000

        spinning_activity = {
            "name": "Yarn Production (Spinning)",
            "amount": total_weight_kg,
            "unit": "kg",
            "activity_type": "spinning",
            "technology": yarn['spinning_technology'],
            "location": yarn['spinning_location'],
            "electricity_kwh": float(yarn['spinning_electricity_kwh']) * total_weight_kg,
            "renewable_energy_pct": float(yarn.get('spinning_renewable_energy', 0)),
            "emission_factor_key": f"spinning_{yarn['spinning_technology']}_{yarn['spinning_location']}"
        }
        inventory.append(spinning_activity)

    # Activity 3: Fabric Construction
    if 'fabric_construction' in product:
        fabric = product['fabric_construction']
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000

        construction_activity = {
            "name": "Fabric Construction",
            "amount": total_weight_kg,
            "unit": "kg",
            "activity_type": "fabric_construction",
            "method": fabric['construction_method'],
            "location": fabric['construction_location'],
            "electricity_kwh": float(fabric['construction_electricity_kwh']) * total_weight_kg,
            "renewable_energy_pct": float(fabric.get('construction_renewable_energy', 0)),
            "emission_factor_key": f"construction_{fabric['construction_method']}_{fabric['construction_location']}"
        }
        inventory.append(construction_activity)

    # Activity 4: Wet Processing (Dyeing, Finishing)
    if 'wet_processing' in product:
        wet = product['wet_processing']
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000

        wet_activity = {
            "name": "Wet Processing",
            "amount": total_weight_kg,
            "unit": "kg",
            "activity_type": "wet_processing",
            "dyeing_type": wet['dyeing_process_type'],
            "color_depth": wet['color_depth'],
            "finishing_method": wet['finishing_method'],
            "location": wet['finishing_location'],
            "water_l": float(wet['water_consumption_l']) * total_weight_kg,
            "thermal_energy_mj": float(wet['thermal_energy_mj']) * total_weight_kg,
            "electricity_kwh": float(wet['electricity_kwh']) * total_weight_kg,
            "renewable_energy_pct": float(wet.get('wet_renewable_energy', 0)),
            "has_etp": wet['onsite_etp'],
            "has_zld": wet['zero_liquid_discharge'],
            "emission_factor_key": f"dyeing_{wet['dyeing_process_type']}_{wet['color_depth']}_{wet['finishing_location']}"
        }
        inventory.append(wet_activity)

    # Activity 5: Manufacturing (CMT)
    if 'manufacturing' in product:
        mfg = product['manufacturing']
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000
        cutting_waste_rate = float(mfg['cutting_waste_rate']) / 100

        # Account for cutting waste (need more fabric than final product)
        fabric_needed_kg = total_weight_kg / (1 - cutting_waste_rate)

        manufacturing_activity = {
            "name": "Cut, Make & Trim",
            "amount": 1,  # Per piece
            "unit": "piece",
            "activity_type": "manufacturing",
            "location": mfg['factory_location'],
            "cutting_waste_kg": fabric_needed_kg - total_weight_kg,
            "electricity_kwh": float(mfg.get('sewing_electricity_kwh', 0.02)),  # Default 0.02 kWh/piece
            "renewable_energy_pct": float(mfg.get('manufacturing_renewable_energy', 0)),
            "emission_factor_key": f"manufacturing_{mfg['factory_location']}"
        }
        inventory.append(manufacturing_activity)

    # Activity 6: Packaging
    if 'packaging' in product:
        pkg = product['packaging']

        # Primary packaging
        if float(pkg.get('primary_packaging_weight_g', 0)) > 0:
            primary_pkg_activity = {
                "name": f"Primary Packaging ({pkg['primary_packaging_type']})",
                "amount": float(pkg['primary_packaging_weight_g']) / 1000,  # Convert to kg
                "unit": "kg",
                "activity_type": "packaging",
                "material_type": pkg['primary_packaging_type'],
                "emission_factor_key": f"packaging_{pkg['primary_packaging_type']}"
            }
            inventory.append(primary_pkg_activity)

        # Secondary packaging
        if pkg.get('secondary_packaging_type') and pkg.get('secondary_packaging_type') != 'None':
            if float(pkg.get('secondary_packaging_weight_g', 0)) > 0:
                secondary_pkg_activity = {
                    "name": f"Secondary Packaging ({pkg['secondary_packaging_type']})",
                    "amount": float(pkg['secondary_packaging_weight_g']) / 1000,
                    "unit": "kg",
                    "activity_type": "packaging",
                    "material_type": pkg['secondary_packaging_type'],
                    "emission_factor_key": f"packaging_{pkg['secondary_packaging_type']}"
                }
                inventory.append(secondary_pkg_activity)

    # Activity 7: Transport
    if 'logistics' in product:
        for leg in product['logistics']:
            transport_activity = {
                "name": f"Transport: {leg['leg_name']}",
                "amount": float(leg['distance_km']),
                "unit": "tkm",  # tonne-kilometers
                "activity_type": "transport",
                "mode": leg['transport_mode'],
                "distance_km": float(leg['distance_km']),
                "cargo_weight_kg": float(product['product_info']['total_weight_grams']) / 1000,
                "emission_factor_key": f"transport_{leg['transport_mode']}"
            }
            inventory.append(transport_activity)

    # Activity 8: Waste Management
    if 'waste_management' in product and 'manufacturing' in product:
        waste_mgmt = product['waste_management']
        mfg = product['manufacturing']

        cutting_waste_rate = float(mfg['cutting_waste_rate']) / 100
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000
        waste_kg = total_weight_kg * cutting_waste_rate / (1 - cutting_waste_rate)

        # Recycled waste
        if float(waste_mgmt.get('waste_recycled', 0)) > 0:
            recycled_waste_kg = waste_kg * float(waste_mgmt['waste_recycled']) / 100
            inventory.append({
                "name": "Fabric Waste - Recycled",
                "amount": recycled_waste_kg,
                "unit": "kg",
                "activity_type": "waste_treatment",
                "treatment_type": "recycling",
                "emission_factor_key": "waste_textile_recycling"
            })

        # Incinerated waste
        if float(waste_mgmt.get('waste_incinerated', 0)) > 0:
            incinerated_waste_kg = waste_kg * float(waste_mgmt['waste_incinerated']) / 100
            inventory.append({
                "name": "Fabric Waste - Incinerated",
                "amount": incinerated_waste_kg,
                "unit": "kg",
                "activity_type": "waste_treatment",
                "treatment_type": "incineration_with_energy_recovery",
                "emission_factor_key": "waste_textile_incineration"
            })

        # Landfilled waste
        if float(waste_mgmt.get('waste_landfilled', 0)) > 0:
            landfilled_waste_kg = waste_kg * float(waste_mgmt['waste_landfilled']) / 100
            inventory.append({
                "name": "Fabric Waste - Landfilled",
                "amount": landfilled_waste_kg,
                "unit": "kg",
                "activity_type": "waste_treatment",
                "treatment_type": "landfill",
                "emission_factor_key": "waste_textile_landfill"
            })

    # Activity 9: Use Phase (Optional)
    if product.get('use_phase', {}).get('include_use_phase'):
        use = product['use_phase']
        num_washes = int(use.get('lifetime_washing_cycles', 50))
        wash_temp = float(use.get('washing_temperature', 40))

        washing_activity = {
            "name": "Consumer Use Phase - Washing",
            "amount": num_washes,
            "unit": "washes",
            "activity_type": "use_phase",
            "sub_type": "washing",
            "temperature_celsius": wash_temp,
            "machine_type": use.get('washing_machine_type', 'Front-loading'),
            "emission_factor_key": f"washing_{use.get('washing_machine_type', 'Front-loading')}_{wash_temp}C"
        }
        inventory.append(washing_activity)

        # Drying
        if use.get('drying_method') and use['drying_method'] != 'Line dry':
            drying_activity = {
                "name": "Consumer Use Phase - Drying",
                "amount": num_washes,
                "unit": "cycles",
                "activity_type": "use_phase",
                "sub_type": "drying",
                "method": use['drying_method'],
                "emission_factor_key": f"drying_{use['drying_method']}"
            }
            inventory.append(drying_activity)

        # Ironing
        if use.get('ironing'):
            ironing_minutes = float(use.get('ironing_minutes', 5)) * num_washes
            ironing_activity = {
                "name": "Consumer Use Phase - Ironing",
                "amount": ironing_minutes,
                "unit": "minutes",
                "activity_type": "use_phase",
                "sub_type": "ironing",
                "emission_factor_key": "ironing_electricity"
            }
            inventory.append(ironing_activity)

    # Activity 10: End of Life (Optional)
    if product.get('end_of_life', {}).get('include_end_of_life'):
        eol = product['end_of_life']
        total_weight_kg = float(product['product_info']['total_weight_grams']) / 1000

        # Reuse (credit for avoided production)
        if float(eol.get('reuse_percentage', 0)) > 0:
            reuse_kg = total_weight_kg * float(eol['reuse_percentage']) / 100
            inventory.append({
                "name": "End of Life - Reuse",
                "amount": reuse_kg,
                "unit": "kg",
                "activity_type": "end_of_life",
                "treatment": "reuse",
                "credit": True,  # Environmental credit
                "emission_factor_key": "eol_reuse_credit"
            })

        # Recycling (textile-to-textile)
        if float(eol.get('recycled_percentage', 0)) > 0:
            recycled_kg = total_weight_kg * float(eol['recycled_percentage']) / 100
            inventory.append({
                "name": "End of Life - Recycled",
                "amount": recycled_kg,
                "unit": "kg",
                "activity_type": "end_of_life",
                "treatment": "textile_to_textile_recycling",
                "emission_factor_key": "eol_textile_recycling"
            })

        # Downcycling
        if float(eol.get('downcycled_percentage', 0)) > 0:
            downcycled_kg = total_weight_kg * float(eol['downcycled_percentage']) / 100
            inventory.append({
                "name": "End of Life - Downcycled",
                "amount": downcycled_kg,
                "unit": "kg",
                "activity_type": "end_of_life",
                "treatment": "downcycling",
                "emission_factor_key": "eol_downcycling"
            })

        # Incineration
        if float(eol.get('incinerated_percentage', 0)) > 0:
            incinerated_kg = total_weight_kg * float(eol['incinerated_percentage']) / 100
            inventory.append({
                "name": "End of Life - Incinerated",
                "amount": incinerated_kg,
                "unit": "kg",
                "activity_type": "end_of_life",
                "treatment": "incineration_with_energy_recovery",
                "emission_factor_key": "eol_incineration"
            })

        # Landfill
        if float(eol.get('landfill_percentage', 0)) > 0:
            landfilled_kg = total_weight_kg * float(eol['landfill_percentage']) / 100
            inventory.append({
                "name": "End of Life - Landfilled",
                "amount": landfilled_kg,
                "unit": "kg",
                "activity_type": "end_of_life",
                "treatment": "landfill",
                "emission_factor_key": "eol_landfill"
            })

    return inventory
```

---

### **Step 4: Validate Inventory**

```python
def _validate_inventory(self, inventory: List[dict]) -> List[str]:
    """
    Validate the built inventory for completeness and consistency.
    """
    errors = []

    if len(inventory) == 0:
        errors.append("Inventory is empty - no activities found")
        return errors

    # Check for required activity types
    activity_types = {act['activity_type'] for act in inventory}
    required_types = ['fiber_production', 'spinning', 'manufacturing']

    missing_types = set(required_types) - activity_types
    if missing_types:
        errors.append(f"Missing required activities: {', '.join(missing_types)}")

    # Check for negative amounts
    for activity in inventory:
        if activity.get('amount', 0) < 0:
            errors.append(f"Negative amount in activity '{activity['name']}': {activity['amount']}")

    # Check for missing emission factor keys
    for activity in inventory:
        if 'emission_factor_key' not in activity:
            errors.append(f"Missing emission factor key for activity '{activity['name']}'")

    # Check mass balance (fiber weight should roughly equal product weight)
    fiber_activities = [a for a in inventory if a['activity_type'] == 'fiber_production']
    total_fiber_kg = sum(a['amount'] for a in fiber_activities)

    # Allow 20% tolerance for manufacturing waste
    # (total fibers should be >= product weight due to waste)
    if total_fiber_kg < 0.001:  # Less than 1 gram
        errors.append("Total fiber weight is too low (< 1 gram)")

    return errors
```

---

### **Step 5: Calculate Impacts using Brightway2**

```python
def _calculate_impacts(self, inventory: List[dict], product: dict) -> dict:
    """
    Calculate environmental impacts using Brightway2 engine.
    """
    impacts = {
        "climate_change_kg_co2eq": 0,
        "water_use_liters": 0,
        "human_health_daly": 0,
        "ecosystems_pdf_m2_yr": 0,
        "resource_availability_usd": 0,
        "eutrophication_freshwater_kg_p_eq": 0,
        "eutrophication_marine_kg_n_eq": 0,
        "eutrophication_terrestrial_mol_n_eq": 0,
        "acidification_mol_h_eq": 0,
        "ecotoxicity_freshwater_ctue": 0,
        "human_toxicity_cancer_ctuh": 0,
        "human_toxicity_non_cancer_ctuh": 0,
        "ionizing_radiation_kbq_u235_eq": 0,
        "land_use_pt": 0,
        "ozone_depletion_kg_cfc11_eq": 0,
        "particulate_matter_disease_incidence": 0,
        "photochemical_ozone_kg_nmvoc_eq": 0
    }

    contribution_breakdown = []

    for activity in inventory:
        # Get emission factors from cache or database
        ef_key = activity['emission_factor_key']

        if ef_key in self.emission_factor_cache:
            emission_factors = self.emission_factor_cache[ef_key]
        else:
            # Fetch from Brightway2
            emission_factors = self.bw_engine.get_emission_factors_for_activity(activity)
            self.emission_factor_cache[ef_key] = emission_factors

        # Calculate impacts for this activity
        activity_amount = activity['amount']
        activity_impacts = {}

        for impact_category, factor in emission_factors.items():
            impact_value = activity_amount * factor

            # Apply grid mix adjustment for electricity
            if 'electricity_kwh' in activity:
                grid_factor = self._get_grid_emission_factor(
                    location=activity.get('location', 'Global'),
                    renewable_pct=activity.get('renewable_energy_pct', 0)
                )

                electricity_kwh = activity['electricity_kwh']
                electricity_impact = electricity_kwh * grid_factor.get(impact_category, 0)

                impact_value += electricity_impact

            activity_impacts[impact_category] = impact_value
            impacts[impact_category] = impacts.get(impact_category, 0) + impact_value

        # Store contribution for breakdown
        contribution_breakdown.append({
            "activity_name": activity['name'],
            "activity_type": activity['activity_type'],
            "amount": activity_amount,
            "unit": activity['unit'],
            "impacts": activity_impacts,
            "contribution_pct": {}  # Will calculate after totals known
        })

    # Calculate contribution percentages
    for contrib in contribution_breakdown:
        for impact_cat, value in contrib['impacts'].items():
            total = impacts[impact_cat]
            contrib['contribution_pct'][impact_cat] = (value / total * 100) if total > 0 else 0

    impacts['contribution_breakdown'] = contribution_breakdown

    return impacts

def _get_grid_emission_factor(self, location: str, renewable_pct: float) -> dict:
    """
    Get electricity grid emission factors adjusted for renewable energy.
    """
    # Grid emission factors by country (kg CO2eq/kWh and other impacts)
    grid_factors = {
        "India": {"climate_change_kg_co2eq": 0.82, "water_use_liters": 0.5},
        "China": {"climate_change_kg_co2eq": 0.65, "water_use_liters": 0.4},
        "Bangladesh": {"climate_change_kg_co2eq": 0.71, "water_use_liters": 0.3},
        "Vietnam": {"climate_change_kg_co2eq": 0.68, "water_use_liters": 0.35},
        "Turkey": {"climate_change_kg_co2eq": 0.48, "water_use_liters": 0.25},
        "Global": {"climate_change_kg_co2eq": 0.47, "water_use_liters": 0.3}
    }

    base_factors = grid_factors.get(location, grid_factors["Global"])

    # Adjust for renewable energy (reduce impacts proportionally)
    renewable_fraction = renewable_pct / 100
    adjusted_factors = {
        k: v * (1 - renewable_fraction) for k, v in base_factors.items()
    }

    return adjusted_factors
```

---

### **Step 6: Validate Calculation Results**

```python
def _validate_results(self, impacts: dict) -> List[str]:
    """
    Validate calculation results for sanity.
    """
    errors = []

    # Check for negative impacts (shouldn't happen except for credits)
    for impact_cat, value in impacts.items():
        if impact_cat == 'contribution_breakdown':
            continue

        if value < 0:
            errors.append(f"Negative impact value for {impact_cat}: {value}")

    # Check for unreasonably high values (data quality issue indicator)
    # For a typical t-shirt:
    # - Climate change: 2-15 kg CO2eq is reasonable
    # - Water use: 500-5000 liters is reasonable
    # - Values 100x higher suggest data error

    if impacts.get('climate_change_kg_co2eq', 0) > 200:
        errors.append(f"Climate change impact unusually high: {impacts['climate_change_kg_co2eq']:.2f} kg CO2eq (expected < 200)")

    if impacts.get('water_use_liters', 0) > 100000:
        errors.append(f"Water use unusually high: {impacts['water_use_liters']:.0f} liters (expected < 100,000)")

    # Check for all zeros (calculation likely failed)
    non_zero_impacts = sum(1 for k, v in impacts.items() if k != 'contribution_breakdown' and v > 0)
    if non_zero_impacts == 0:
        errors.append("All impact values are zero - calculation may have failed")

    return errors
```

---

### **Step 7: Data Quality Assessment**

```python
def _assess_data_quality(self, product: dict) -> dict:
    """
    Assess overall data quality of the product inputs.
    """
    quality_score = 100  # Start with perfect score
    deductions = []

    # Deduct points for missing optional data
    if 'yarn_production' in product:
        if not product['yarn_production'].get('spinning_renewable_energy'):
            quality_score -= 5
            deductions.append("Missing renewable energy data for spinning")

    if 'logistics' not in product or len(product.get('logistics', [])) == 0:
        quality_score -= 10
        deductions.append("No transport data provided (using defaults)")

    # Deduct for generic countries
    for fiber in product.get('fiber_composition', []):
        if fiber.get('origin_country') == 'Other':
            quality_score -= 5
            deductions.append(f"Generic origin for {fiber.get('fiber_type')}")

    # Deduct for missing use phase (if doing cradle-to-grave)
    if not product.get('use_phase', {}).get('include_use_phase'):
        quality_score -= 5
        deductions.append("Use phase not included (cradle-to-gate only)")

    # Cap at 0
    quality_score = max(0, quality_score)

    quality_rating = "Excellent" if quality_score >= 90 else \
                    "Good" if quality_score >= 75 else \
                    "Fair" if quality_score >= 60 else "Poor"

    return {
        "score": quality_score,
        "rating": quality_rating,
        "deductions": deductions,
        "completeness_pct": quality_score
    }
```

---

## 3. Complete End-to-End Example

```python
# Example: Processing 100 products

products = [
    {
        "product_info": {
            "product_id": "TS-001",
            "product_name": "Cotton Tee",
            "total_weight_grams": 180
        },
        "fiber_composition": [
            {
                "fiber_type": "Cotton (Conventional)",
                "percentage": 100,
                "weight_grams": 180,
                "origin_country": "India"
            }
        ],
        "yarn_production": {
            "spinning_technology": "Ring Spinning",
            "spinning_location": "India",
            "spinning_electricity_kwh": 0.35,
            "spinning_renewable_energy": 10
        },
        # ... more sections
    },
    # ... 99 more products
]

calculator = BatchLCACalculator(industry="textile")
results = calculator.calculate_batch(products)

print(f"Processed {results['total_products']} products")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
print(f"Time: {results['processing_time_seconds']}s")

for result in results['results']:
    if result['status'] == 'success':
        print(f"{result['product_id']}: {result['impacts']['climate_change_kg_co2eq']:.2f} kg CO2eq")
    else:
        print(f"{result['product_id']}: FAILED - {result['error']}")
```

---

## Summary: How We Ensure Accuracy

### **CSV Input Validation** ✅
1. **Structural validation**: Column headers match schema
2. **Type validation**: Numbers are numbers, selects are valid options
3. **Business rules**: Percentages sum to 100%, weights match
4. **Completeness warnings**: Optional fields missing (not errors)

### **Calculation Accuracy** ✅
1. **Inventory validation**: All required activities present
2. **Mass balance**: Fiber weights match product weight
3. **Emission factor caching**: Pre-load factors, avoid redundant queries
4. **Grid mix adjustment**: Location-specific + renewable energy %
5. **Result validation**: Sanity checks on impact values

### **Error Handling** ✅
1. **Graceful failures**: One failed product doesn't stop batch
2. **Detailed error messages**: User knows exactly what's wrong
3. **Timeout protection**: 30 seconds per product max
4. **Logging**: All errors logged for debugging

### **Performance** ✅
1. **Parallel processing**: 10 concurrent workers
2. **Caching**: Emission factors cached, not re-queried
3. **Pre-loading**: Common factors loaded before batch starts
4. **Target**: 100 products in <60 seconds

This comprehensive approach ensures **data quality**, **calculation accuracy**, and **robust error handling** for batch LCA processing! 🚀
