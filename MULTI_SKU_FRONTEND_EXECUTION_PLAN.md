# Multi-SKU Frontend Execution Plan

## Overview
This document outlines how we will execute batch/multi-SKU LCA assessments in the frontend, allowing users to process 100+ product SKUs efficiently.

---

## Architecture: Two Approaches

### **Approach 1: CSV Bulk Upload (Recommended for Phase 1)**
Best for: 100+ SKUs, offline data preparation, Excel power users

### **Approach 2: In-App Batch Entry (Phase 2)**
Best for: 10-50 SKUs, collaborative teams, quick iterations

---

## **APPROACH 1: CSV Bulk Upload**

### User Flow

```
1. User clicks "Batch Assessment" in navigation
2. User selects industry (Textile, Water, Food, etc.)
3. User downloads CSV template for selected industry
4. User fills template in Excel with 100 SKU rows
5. User uploads filled CSV
6. System validates all rows, shows errors
7. User fixes errors, re-uploads if needed
8. User clicks "Calculate All"
9. Progress bar shows "Processing 45/100..."
10. Results table displays all SKUs with sortable columns
11. User downloads comprehensive Excel report
```

---

## Frontend Components

### **1. BatchAssessment.jsx** (New Page)
**Route**: `/batch-assessment`

#### Component Structure:
```jsx
import React, { useState } from 'react';
import { Upload, Download, Play, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { Table } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Alert } from '@/components/ui/alert';

export default function BatchAssessment() {
  const [step, setStep] = useState('select'); // select, upload, validate, calculate, results
  const [industry, setIndustry] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [parsedData, setParsedData] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [calculationProgress, setCalculationProgress] = useState(0);
  const [results, setResults] = useState([]);

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Batch LCA Assessment</h1>

      {/* Step Indicator */}
      <StepIndicator currentStep={step} />

      {/* Step 1: Select Industry */}
      {step === 'select' && <IndustrySelector onSelect={handleIndustrySelect} />}

      {/* Step 2: Upload CSV */}
      {step === 'upload' && <CSVUploader industry={industry} onUpload={handleUpload} />}

      {/* Step 3: Validate Data */}
      {step === 'validate' && <DataValidator data={parsedData} errors={validationErrors} onProceed={handleCalculate} />}

      {/* Step 4: Calculate */}
      {step === 'calculate' && <CalculationProgress progress={calculationProgress} />}

      {/* Step 5: Results */}
      {step === 'results' && <ResultsTable results={results} onExport={handleExport} />}
    </div>
  );
}
```

---

### **2. IndustrySelector Component**

```jsx
function IndustrySelector({ onSelect }) {
  const industries = [
    { id: 'textile', name: 'Textile Products', icon: '👕' },
    { id: 'bawear', name: 'Textile (bAwear Detailed)', icon: '🧥' },
    { id: 'water', name: 'Packaged Water', icon: '💧' },
    { id: 'food', name: 'Food Products', icon: '🍎' },
    { id: 'footwear', name: 'Footwear', icon: '👟' },
  ];

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Select Industry</h2>
      <p className="text-muted-foreground mb-6">
        Choose the industry for your batch assessment. The CSV template will be customized for this industry.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {industries.map((industry) => (
          <Card
            key={industry.id}
            className="p-6 cursor-pointer hover:border-primary transition-all"
            onClick={() => onSelect(industry.id)}
          >
            <div className="text-4xl mb-2">{industry.icon}</div>
            <h3 className="font-semibold">{industry.name}</h3>
          </Card>
        ))}
      </div>
    </Card>
  );
}
```

---

### **3. CSVUploader Component**

```jsx
function CSVUploader({ industry, onUpload }) {
  const [dragActive, setDragActive] = useState(false);

  const handleDownloadTemplate = async () => {
    // Call API to generate dynamic template
    const response = await fetch(`/api/schemas/${industry}/csv-template`);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${industry}_batch_template.csv`;
    a.click();
  };

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('industry', industry);

    const response = await fetch('/api/batch/parse-csv', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    onUpload(data);
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Upload CSV File</h2>

      {/* Download Template Button */}
      <div className="mb-6">
        <Button onClick={handleDownloadTemplate} variant="outline" className="w-full">
          <Download className="w-4 h-4 mr-2" />
          Download CSV Template for {industry}
        </Button>
        <p className="text-sm text-muted-foreground mt-2">
          Download the template, fill it with your product data, then upload it below.
        </p>
      </div>

      {/* Drag & Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragActive ? 'border-primary bg-primary/5' : 'border-border'
        }`}
        onDragEnter={() => setDragActive(true)}
        onDragLeave={() => setDragActive(false)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFileUpload(file);
        }}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="text-lg font-semibold mb-2">Drop CSV file here</h3>
        <p className="text-muted-foreground mb-4">or click to browse</p>
        <input
          type="file"
          accept=".csv"
          className="hidden"
          id="csv-upload"
          onChange={(e) => {
            const file = e.target.files[0];
            if (file) handleFileUpload(file);
          }}
        />
        <Button asChild variant="secondary">
          <label htmlFor="csv-upload" className="cursor-pointer">
            Browse Files
          </label>
        </Button>
      </div>

      {/* Example Data Format */}
      <div className="mt-6 p-4 bg-muted rounded-lg">
        <h4 className="font-semibold mb-2">Expected CSV Format:</h4>
        <pre className="text-xs overflow-x-auto">
{`product_id,product_name,product_category,total_weight_grams,fiber_type_1,percentage_1,...
TS-001,Cotton Tee,T-Shirt,180,Cotton (Conventional),100,...
TS-002,Poly Blend,T-Shirt,160,Cotton (Conventional),60,...`}
        </pre>
      </div>
    </Card>
  );
}
```

---

### **4. DataValidator Component**

```jsx
function DataValidator({ data, errors, onProceed }) {
  const [showErrors, setShowErrors] = useState(true);

  const validRows = data.filter(row => !row.errors || row.errors.length === 0);
  const invalidRows = data.filter(row => row.errors && row.errors.length > 0);

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Validation Results</h2>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="p-4 bg-primary/10">
          <div className="text-2xl font-bold text-primary">{data.length}</div>
          <div className="text-sm text-muted-foreground">Total Products</div>
        </Card>
        <Card className="p-4 bg-green-500/10">
          <div className="text-2xl font-bold text-green-600">{validRows.length}</div>
          <div className="text-sm text-muted-foreground">Valid</div>
        </Card>
        <Card className="p-4 bg-red-500/10">
          <div className="text-2xl font-bold text-red-600">{invalidRows.length}</div>
          <div className="text-sm text-muted-foreground">Invalid</div>
        </Card>
      </div>

      {/* Error Messages */}
      {invalidRows.length > 0 && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <div>
            <h4 className="font-semibold">Validation Errors Found</h4>
            <p className="text-sm">
              {invalidRows.length} products have errors. Fix them and re-upload, or proceed with only valid products.
            </p>
          </div>
        </Alert>
      )}

      {/* Data Preview Table */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Data Preview</h3>
          <Button variant="ghost" size="sm" onClick={() => setShowErrors(!showErrors)}>
            {showErrors ? 'Show All' : 'Show Only Errors'}
          </Button>
        </div>

        <Table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Product ID</th>
              <th>Product Name</th>
              <th>Weight (g)</th>
              <th>Fibers</th>
              <th>Status</th>
              <th>Errors</th>
            </tr>
          </thead>
          <tbody>
            {(showErrors ? invalidRows : data).map((row, index) => (
              <tr key={index} className={row.errors?.length > 0 ? 'bg-red-50' : ''}>
                <td>{index + 1}</td>
                <td>{row.product_info?.product_id}</td>
                <td>{row.product_info?.product_name}</td>
                <td>{row.product_info?.total_weight_grams}</td>
                <td>
                  {row.fiber_composition?.map(f => f.fiber_type).join(', ')}
                </td>
                <td>
                  {row.errors?.length > 0 ? (
                    <span className="text-red-600 font-semibold">❌ Invalid</span>
                  ) : (
                    <span className="text-green-600 font-semibold">✓ Valid</span>
                  )}
                </td>
                <td>
                  {row.errors?.map((error, i) => (
                    <div key={i} className="text-xs text-red-600">{error}</div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button onClick={() => window.location.reload()} variant="outline">
          Upload Different File
        </Button>
        {validRows.length > 0 && (
          <Button onClick={() => onProceed(validRows)} className="flex-1">
            Calculate {validRows.length} Valid Products
          </Button>
        )}
      </div>
    </Card>
  );
}
```

---

### **5. CalculationProgress Component**

```jsx
function CalculationProgress({ progress, total, currentProduct }) {
  const percentage = Math.round((progress / total) * 100);

  return (
    <Card className="p-8 max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold mb-6 text-center">Calculating LCA Results</h2>

      <div className="mb-8">
        <div className="flex justify-between text-sm text-muted-foreground mb-2">
          <span>Progress</span>
          <span>{progress} / {total} products</span>
        </div>
        <Progress value={percentage} className="h-3" />
        <div className="text-center mt-2 text-lg font-semibold text-primary">
          {percentage}%
        </div>
      </div>

      {currentProduct && (
        <div className="text-center p-4 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground mb-1">Currently processing:</p>
          <p className="font-semibold">{currentProduct.product_name}</p>
          <p className="text-sm text-muted-foreground">{currentProduct.product_id}</p>
        </div>
      )}

      <div className="mt-6 flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <div className="animate-spin">⏳</div>
        <span>This may take a few minutes for large batches...</span>
      </div>
    </Card>
  );
}
```

---

### **6. ResultsTable Component**

```jsx
function ResultsTable({ results, onExport }) {
  const [sortBy, setSortBy] = useState('climate_change');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedProducts, setSelectedProducts] = useState([]);

  const sortedResults = [...results].sort((a, b) => {
    const aVal = a.impacts?.[sortBy] || 0;
    const bVal = b.impacts?.[sortBy] || 0;
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Batch Assessment Results</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => onExport('csv')}>
            Export CSV
          </Button>
          <Button onClick={() => onExport('excel')}>
            Export Excel Report
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Total Products</div>
          <div className="text-2xl font-bold">{results.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Avg Climate Impact</div>
          <div className="text-2xl font-bold">
            {(results.reduce((sum, r) => sum + (r.impacts?.climate_change || 0), 0) / results.length).toFixed(2)} kg
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Avg Water Use</div>
          <div className="text-2xl font-bold">
            {(results.reduce((sum, r) => sum + (r.impacts?.water_use || 0), 0) / results.length).toFixed(0)} L
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Best Performer</div>
          <div className="text-lg font-bold truncate">
            {sortedResults[sortedResults.length - 1]?.product_id}
          </div>
        </Card>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center gap-4 mb-4">
        <span className="text-sm font-medium">Sort by:</span>
        <Select value={sortBy} onValueChange={setSortBy}>
          <option value="climate_change">Climate Change</option>
          <option value="water_use">Water Use</option>
          <option value="human_health">Human Health</option>
          <option value="ecosystems">Ecosystems</option>
        </Select>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
        >
          {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
        </Button>
      </div>

      {/* Results Table */}
      <Table>
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedProducts(results.map(r => r.product_id));
                  } else {
                    setSelectedProducts([]);
                  }
                }}
              />
            </th>
            <th>Product ID</th>
            <th>Product Name</th>
            <th>Status</th>
            <th>Climate Change (kg CO2eq)</th>
            <th>Water Use (L)</th>
            <th>Human Health (DALY)</th>
            <th>Ecosystems (PDF·m²·yr)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedResults.map((result) => (
            <tr key={result.product_id} className="hover:bg-muted/50">
              <td>
                <input
                  type="checkbox"
                  checked={selectedProducts.includes(result.product_id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedProducts([...selectedProducts, result.product_id]);
                    } else {
                      setSelectedProducts(selectedProducts.filter(id => id !== result.product_id));
                    }
                  }}
                />
              </td>
              <td className="font-mono text-sm">{result.product_id}</td>
              <td className="font-medium">{result.product_name}</td>
              <td>
                {result.status === 'success' ? (
                  <span className="text-green-600 font-semibold">✓ Success</span>
                ) : (
                  <span className="text-red-600 font-semibold">✗ Failed</span>
                )}
              </td>
              <td className="text-right font-mono">
                {result.impacts?.climate_change?.toFixed(2) || 'N/A'}
              </td>
              <td className="text-right font-mono">
                {result.impacts?.water_use?.toFixed(0) || 'N/A'}
              </td>
              <td className="text-right font-mono">
                {result.impacts?.human_health?.toExponential(2) || 'N/A'}
              </td>
              <td className="text-right font-mono">
                {result.impacts?.ecosystems?.toExponential(2) || 'N/A'}
              </td>
              <td>
                <Button variant="ghost" size="sm" onClick={() => viewDetails(result.product_id)}>
                  View Details
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Bulk Actions */}
      {selectedProducts.length > 0 && (
        <div className="mt-4 p-4 bg-primary/10 rounded-lg flex items-center justify-between">
          <span className="font-medium">{selectedProducts.length} products selected</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">Compare Selected</Button>
            <Button variant="outline" size="sm">Export Selected</Button>
            <Button variant="outline" size="sm">Delete Selected</Button>
          </div>
        </div>
      )}
    </Card>
  );
}
```

---

## Backend API Endpoints

### **1. Generate CSV Template**

```python
@app.get("/api/schemas/{industry}/csv-template")
async def generate_csv_template(industry: str):
    """
    Generate dynamic CSV template based on industry schema.
    """
    schema = get_schema(industry)  # TEXTILE_SCHEMA, BAWEAR_SCHEMA, etc.

    headers = []
    example_row = []

    # Product info section
    for field in schema['sections'][0]['fields']:  # product_info
        headers.append(field['id'])
        example_row.append(f"Example {field['label']}")

    # Repeatable sections (e.g., fiber_composition)
    for section in schema['sections']:
        if section.get('repeatable'):
            max_items = section.get('max_items', 1)
            for i in range(1, max_items + 1):
                for field in section['fields']:
                    headers.append(f"{field['id']}_{i}")
                    example_row.append("")
        else:
            # Non-repeatable sections
            for field in section['fields']:
                headers.append(field['id'])
                example_row.append("")

    # Generate CSV
    csv_content = ",".join(headers) + "\n"
    csv_content += ",".join(example_row) + "\n"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={industry}_template.csv"}
    )
```

---

### **2. Parse and Validate CSV**

```python
@app.post("/api/batch/parse-csv")
async def parse_csv(file: UploadFile, industry: str):
    """
    Parse uploaded CSV and validate against schema.
    """
    import pandas as pd

    # Read CSV
    df = pd.read_csv(file.file)
    schema = get_schema(industry)

    products = []

    for index, row in df.iterrows():
        product = {
            "row_number": index + 1,
            "errors": []
        }

        # Parse product_info
        product["product_info"] = {}
        for field in schema['sections'][0]['fields']:
            field_id = field['id']
            value = row.get(field_id)

            if field.get('required') and pd.isna(value):
                product["errors"].append(f"Missing required field: {field['label']}")
            else:
                product["product_info"][field_id] = value

        # Parse repeatable sections (fiber_composition)
        for section in schema['sections']:
            if section.get('repeatable'):
                section_id = section['id']
                product[section_id] = []

                for i in range(1, section.get('max_items', 1) + 1):
                    item = {}
                    has_data = False

                    for field in section['fields']:
                        col_name = f"{field['id']}_{i}"
                        value = row.get(col_name)

                        if pd.notna(value):
                            has_data = True
                            item[field['id']] = value

                    if has_data:
                        product[section_id].append(item)

            elif section['id'] != 'product_info':
                # Non-repeatable sections
                product[section['id']] = {}
                for field in section['fields']:
                    value = row.get(field['id'])
                    if pd.notna(value):
                        product[section['id']][field['id']] = value

        # Validate fiber percentages sum to 100%
        if "fiber_composition" in product:
            total_pct = sum(float(f.get('percentage', 0)) for f in product['fiber_composition'])
            if abs(total_pct - 100) > 0.1:
                product["errors"].append(f"Fiber percentages sum to {total_pct}%, must equal 100%")

        products.append(product)

    return {
        "total": len(products),
        "valid": len([p for p in products if len(p['errors']) == 0]),
        "invalid": len([p for p in products if len(p['errors']) > 0]),
        "products": products
    }
```

---

### **3. Batch Calculate**

```python
@app.post("/api/batch/calculate")
async def calculate_batch(request: BatchCalculateRequest, background_tasks: BackgroundTasks):
    """
    Calculate LCA for multiple products in parallel.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    products = request.products
    industry = request.industry

    results = []
    progress = 0

    def calculate_single(product_data):
        try:
            result = calculate_lca(product_data, industry)
            return {
                "product_id": product_data['product_info']['product_id'],
                "product_name": product_data['product_info']['product_name'],
                "status": "success",
                "impacts": result
            }
        except Exception as e:
            return {
                "product_id": product_data['product_info']['product_id'],
                "product_name": product_data['product_info']['product_name'],
                "status": "failed",
                "error": str(e)
            }

    # Process in parallel with 10 workers
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_product = {
            executor.submit(calculate_single, product): product
            for product in products
        }

        for future in as_completed(future_to_product):
            result = future.result()
            results.append(result)
            progress += 1

            # Send progress update via WebSocket (optional)
            # await websocket.send_json({"progress": progress, "total": len(products)})

    return {
        "batch_id": str(uuid.uuid4()),
        "total_products": len(products),
        "successful": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] == 'failed']),
        "results": results
    }
```

---

## CSV Template Example (Textile Industry)

```csv
product_id,product_name,product_category,total_weight_grams,description,fiber_type_1,percentage_1,weight_grams_1,origin_country_1,fiber_type_2,percentage_2,weight_grams_2,origin_country_2,spinning_technology,yarn_count_nm,spinning_location,spinning_electricity_kwh,spinning_renewable_energy,construction_method,construction_location,construction_electricity_kwh,construction_renewable_energy,fabric_waste_rate,dyeing_process_type,color_depth,printing_method,finishing_method,finishing_location,water_consumption_l,thermal_energy_mj,electricity_kwh,wet_renewable_energy,chemicals_kg,onsite_etp,zero_liquid_discharge,factory_location,cutting_waste_rate,sewing_electricity_kwh,manufacturing_renewable_energy,accessories_weight_g,thread_weight_g,finish_treatment_1,finish_treatment_2,primary_packaging_type,primary_packaging_weight_g,secondary_packaging_type,secondary_packaging_weight_g,hangtag_weight_g,waste_recycled,waste_incinerated,waste_landfilled,leg_name_1,distance_km_1,transport_mode_1,leg_name_2,distance_km_2,transport_mode_2,include_use_phase,lifetime_washing_cycles,washing_temperature,washing_machine_type,drying_method,ironing,ironing_minutes,include_end_of_life,reuse_percentage,recycled_percentage,downcycled_percentage,incinerated_percentage,landfill_percentage

TS-001,Basic Cotton Tee,T-Shirt,180,Classic crew neck,Cotton (Conventional),100,180,India,,,,,Ring Spinning,30,India,0.35,10,Knitting - Circular,India,0.12,15,5,Jet Dyeing,Medium,None,Continuous - natural fibers,India,50,80,0.5,20,0.1,TRUE,FALSE,Bangladesh,12,0.02,10,2,1,None,None,Polybag (LDPE),5,None,0,1,10,70,20,Fiber to Spinning,500,Truck (Diesel),Fabric to Factory,800,Sea Freight (Container),TRUE,50,40,Front-loading,Tumble dry - low,TRUE,5,TRUE,5,10,15,40,30

TS-002,Poly Blend Sport Tee,T-Shirt,160,Performance wear,Cotton (Conventional),60,96,India,Polyester (Virgin),40,64,China,Ring Spinning,35,China,0.32,25,Knitting - Circular,China,0.15,30,4,Jet Dyeing,Dark,Screen Printing,Continuous - synthetic fibers,China,45,75,0.6,35,0.08,TRUE,TRUE,Vietnam,10,0.018,20,3,1.5,None,None,Polybag (Recycled PE),4,Cardboard box,15,2,15,65,20,Fiber to Spinning,600,Truck (Diesel),Fabric to Factory,1200,Sea Freight (Container),TRUE,75,30,Front-loading,Line dry,FALSE,0,TRUE,3,8,12,35,42
```

---

## Key Features

### **Real-time Progress Updates (Optional)**
Use WebSockets for live progress:

```jsx
// In BatchAssessment.jsx
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/batch-progress');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setCalculationProgress(data.progress);
    setCurrentProduct(data.current_product);
  };

  return () => ws.close();
}, []);
```

---

## Performance Optimization

1. **Chunked Processing**: Process 100 products in batches of 10
2. **Caching**: Cache emission factors to avoid redundant database queries
3. **Parallel Execution**: Use ThreadPoolExecutor with 10 workers
4. **Progress Tracking**: Store progress in Redis for resume capability

---

## Error Handling

1. **Validation Errors**: Show inline errors in data preview
2. **Calculation Errors**: Continue batch, mark individual products as failed
3. **Partial Results**: Allow export of successful calculations even if some fail
4. **Retry Logic**: Allow re-running failed products only

---

## Summary

**User Experience**:
- Download template → Fill in Excel → Upload → Validate → Calculate → Export
- Processing time: ~60 seconds for 100 products
- Clear progress indication
- Error recovery without starting over

**Technical Approach**:
- CSV parsing with pandas
- Schema-driven validation
- Parallel calculation with ThreadPoolExecutor
- Comprehensive Excel export with multiple sheets

This approach balances ease of use, performance, and data quality for processing large batches of LCA assessments.
