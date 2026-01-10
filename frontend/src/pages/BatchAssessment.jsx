import React, { useState } from 'react';
import { Upload, Download, AlertCircle, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function BatchAssessment() {
  const [step, setStep] = useState('upload'); // upload, validate, calculate, results
  const [industry] = useState('textile'); // Fixed to textile only
  const [uploadedFile, setUploadedFile] = useState(null);
  const [parsedData, setParsedData] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [calculationProgress, setCalculationProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDownloadTemplate = async () => {
    try {
      const response = await fetch(`${API_URL}/api/schemas/${industry}/csv-template`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${industry}_batch_template.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading template:', error);
      alert('Failed to download template. Please try again.');
    }
  };

  const handleFileUpload = async (file) => {
    setLoading(true);
    setUploadedFile(file);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('industry', industry);

      const response = await fetch(`${API_URL}/api/batch/parse-csv?industry=${industry}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'error') {
        setValidationErrors(data.errors || []);
        alert(data.message || 'Validation failed');
        setLoading(false);
        return;
      }

      setParsedData(data);
      setStep('validate');
    } catch (error) {
      console.error('Error parsing CSV:', error);
      alert('Failed to parse CSV file. Please check the format and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    setStep('calculate');
    setLoading(true);

    // Filter only valid products
    const validProducts = parsedData.products.filter(p => p.is_valid);

    try {
      const response = await fetch(`${API_URL}/api/batch/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          industry,
          products: validProducts,
        }),
      });

      const data = await response.json();
      setResults(data);
      setStep('results');
    } catch (error) {
      console.error('Error calculating batch:', error);
      alert('Failed to calculate LCA. Please try again.');
      setStep('validate');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format) => {
    // TODO: Implement export to Excel/CSV
    console.log('Exporting results as', format);
    alert(`Export as ${format} - Coming soon!`);
  };

  const resetWizard = () => {
    setStep('select');
    setIndustry(null);
    setUploadedFile(null);
    setParsedData(null);
    setValidationErrors([]);
    setResults(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
            Batch Textile LCA Assessment
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Process multiple textile products at once using CSV import
          </p>
          <Alert className="mt-4">
            <AlertDescription>
              Batch processing is currently available for <strong>Textile products only</strong>. For other industries (bAwear, Water, Food), please use the standard assessment form.
            </AlertDescription>
          </Alert>
        </div>

        {/* Step Indicator */}
        <div className="mb-8 flex items-center justify-center space-x-4">
          {['Upload CSV', 'Validate Data', 'Calculate', 'Results'].map((stepName, idx) => {
            const stepKeys = ['upload', 'validate', 'calculate', 'results'];
            const currentStepIdx = stepKeys.indexOf(step);
            const isActive = idx === currentStepIdx;
            const isCompleted = idx < currentStepIdx;

            return (
              <React.Fragment key={stepName}>
                <div className={`flex items-center space-x-2 ${isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-slate-400'}`}>
                  <div className={`step-indicator ${isActive ? 'active' : isCompleted ? 'completed' : 'inactive'}`}>
                    {isCompleted ? '✓' : idx + 1}
                  </div>
                  <span className="text-sm font-medium hidden md:inline">{stepName}</span>
                </div>
                {idx < 3 && (
                  <ArrowRight className={`w-4 h-4 ${isCompleted ? 'text-green-600' : 'text-slate-300'}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="space-y-6">
          {/* Step 1: Upload CSV */}
          {step === 'upload' && (
            <Card>
              <CardHeader>
                <CardTitle>Upload CSV File</CardTitle>
                <CardDescription>
                  Download the textile template, fill it with your product data, then upload it below.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Download Template Button */}
                <div>
                  <Button onClick={handleDownloadTemplate} variant="outline" className="w-full" size="lg">
                    <Download className="w-4 h-4 mr-2" />
                    Download Textile CSV Template
                  </Button>
                  <p className="text-sm text-muted-foreground mt-2 text-center">
                    The template includes all required fields for comprehensive textile LCA assessment
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
                    if (file && file.name.endsWith('.csv')) {
                      handleFileUpload(file);
                    } else {
                      alert('Please upload a CSV file');
                    }
                  }}
                >
                  <Upload className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
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
                  <Button asChild variant="secondary" disabled={loading}>
                    <label htmlFor="csv-upload" className="cursor-pointer">
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        'Browse Files'
                      )}
                    </label>
                  </Button>
                </div>

                <div className="flex justify-between">
                  <Button variant="ghost" onClick={resetWizard}>
                    ← Back to Industry Selection
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 3: Validate Data */}
          {step === 'validate' && parsedData && (
            <Card>
              <CardHeader>
                <CardTitle>Validation Results</CardTitle>
                <CardDescription>
                  Review the validation results before proceeding with calculations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <Card className="bg-primary/10 border-primary/20">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-primary">{parsedData.total}</div>
                      <div className="text-sm text-muted-foreground">Total Products</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-green-500/10 border-green-500/20">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-green-600">{parsedData.valid}</div>
                      <div className="text-sm text-muted-foreground">Valid</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-red-500/10 border-red-500/20">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-red-600">{parsedData.invalid}</div>
                      <div className="text-sm text-muted-foreground">Invalid</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Error Alert */}
                {parsedData.invalid > 0 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {parsedData.invalid} products have validation errors. Fix them and re-upload, or proceed with only valid products.
                    </AlertDescription>
                  </Alert>
                )}

                {/* Products Table */}
                <div className="border rounded-lg overflow-hidden">
                  <div className="max-h-96 overflow-y-auto">
                    <table className="w-full">
                      <thead className="bg-muted sticky top-0">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Row</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Product ID</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Product Name</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Issues</th>
                        </tr>
                      </thead>
                      <tbody>
                        {parsedData.products.map((product, idx) => (
                          <tr key={idx} className={`border-t ${product.errors?.length > 0 ? 'bg-red-50 dark:bg-red-900/10' : ''}`}>
                            <td className="px-4 py-3 text-sm">{product.row_number}</td>
                            <td className="px-4 py-3 text-sm font-mono">{product.product_info?.product_id || 'N/A'}</td>
                            <td className="px-4 py-3 text-sm">{product.product_info?.product_name || 'N/A'}</td>
                            <td className="px-4 py-3 text-sm">
                              {product.is_valid ? (
                                <span className="inline-flex items-center text-green-600">
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Valid
                                </span>
                              ) : (
                                <span className="inline-flex items-center text-red-600">
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Invalid
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {product.errors?.length > 0 && (
                                <div className="space-y-1">
                                  {product.errors.map((error, i) => (
                                    <div key={i} className="text-xs text-red-600">• {error}</div>
                                  ))}
                                </div>
                              )}
                              {product.warnings?.length > 0 && (
                                <div className="space-y-1">
                                  {product.warnings.map((warning, i) => (
                                    <div key={i} className="text-xs text-amber-600">⚠ {warning}</div>
                                  ))}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-between">
                  <Button variant="outline" onClick={() => setStep('upload')}>
                    ← Upload Different File
                  </Button>
                  {parsedData.valid > 0 && (
                    <Button onClick={handleCalculate} size="lg">
                      Calculate {parsedData.valid} Valid Products →
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 4: Calculate */}
          {step === 'calculate' && (
            <Card>
              <CardContent className="p-12">
                <div className="max-w-2xl mx-auto text-center space-y-6">
                  <Loader2 className="w-16 h-16 mx-auto animate-spin text-primary" />
                  <h2 className="text-2xl font-semibold">Calculating LCA Results</h2>
                  <p className="text-muted-foreground">
                    Processing {parsedData?.valid} products in parallel...
                  </p>
                  <div className="text-sm text-muted-foreground">
                    This may take a few minutes for large batches
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 5: Results */}
          {step === 'results' && results && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Batch Assessment Results</CardTitle>
                    <CardDescription>
                      Processed {results.total_products} products in {results.processing_time_seconds}s
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => handleExport('csv')}>
                      Export CSV
                    </Button>
                    <Button onClick={() => handleExport('excel')}>
                      Export Excel Report
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Total Products</div>
                      <div className="text-2xl font-bold">{results.total_products}</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-green-500/10">
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Successful</div>
                      <div className="text-2xl font-bold text-green-600">{results.successful}</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-red-500/10">
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Failed</div>
                      <div className="text-2xl font-bold text-red-600">{results.failed}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-sm text-muted-foreground">Processing Time</div>
                      <div className="text-2xl font-bold">{results.processing_time_seconds}s</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Results Table */}
                <div className="border rounded-lg overflow-hidden">
                  <div className="max-h-[600px] overflow-y-auto">
                    <table className="w-full">
                      <thead className="bg-muted sticky top-0">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Product ID</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Product Name</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">Climate (kg CO2eq)</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">Water (L)</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">Quality</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.results.map((result, idx) => (
                          <tr key={idx} className="border-t hover:bg-muted/50">
                            <td className="px-4 py-3 text-sm font-mono">{result.product_id}</td>
                            <td className="px-4 py-3 text-sm">{result.product_name}</td>
                            <td className="px-4 py-3 text-sm">
                              {result.status === 'success' ? (
                                <span className="inline-flex items-center text-green-600">
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Success
                                </span>
                              ) : (
                                <span className="inline-flex items-center text-red-600">
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Failed
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-right font-mono">
                              {result.impacts?.climate_change_kg_co2eq?.toFixed(2) || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-right font-mono">
                              {result.impacts?.water_use_liters?.toFixed(0) || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {result.data_quality ? (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  result.data_quality.score >= 90 ? 'bg-green-100 text-green-800' :
                                  result.data_quality.score >= 75 ? 'bg-blue-100 text-blue-800' :
                                  result.data_quality.score >= 60 ? 'bg-amber-100 text-amber-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {result.data_quality.rating} ({result.data_quality.score})
                                </span>
                              ) : result.error ? (
                                <span className="text-xs text-red-600">{result.error}</span>
                              ) : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-between">
                  <Button variant="outline" onClick={resetWizard}>
                    ← Start New Batch
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
