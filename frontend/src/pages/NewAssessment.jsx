import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  ArrowRight, 
  Save, 
  Play, 
  Plus, 
  Trash2,
  CheckCircle2,
  Circle,
  Loader2
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function NewAssessment() {
  const { industry } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [schema, setSchema] = useState(null);
  const [databases, setDatabases] = useState({});
  const [methods, setMethods] = useState({});
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [projectId, setProjectId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [calculating, setCalculating] = useState(false);

  // Configuration step data
  const [config, setConfig] = useState({
    name: "",
    description: "",
    scope: "cradle-to-gate",
    database: "USLCI",
    method: "ReCiPe",
    product_weight_grams: 0,
    product_scenario: ""
  });

  useEffect(() => {
    loadInitialData();
  }, [industry]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load schema, databases, and methods in parallel
      const [schemaRes, dbRes, methodRes] = await Promise.all([
        axios.get(`${API}/industries/${industry}/schema`),
        axios.get(`${API}/lca/databases`),
        axios.get(`${API}/lca/methods`)
      ]);
      
      setSchema(schemaRes.data);
      setDatabases(dbRes.data.databases);
      setMethods(methodRes.data.methods);
      
      // Initialize form data with schema sections
      const initialFormData = {};
      schemaRes.data.sections.forEach(section => {
        if (section.repeatable) {
          initialFormData[section.id] = [{}];
        } else {
          initialFormData[section.id] = {};
        }
      });
      setFormData(initialFormData);
      
      // Check if loading existing project
      const existingProjectId = searchParams.get("project");
      if (existingProjectId) {
        await loadExistingProject(existingProjectId);
      }
      
    } catch (error) {
      console.error("Error loading data:", error);
      toast.error("Failed to load assessment data");
    } finally {
      setLoading(false);
    }
  };

  const loadExistingProject = async (id) => {
    try {
      const response = await axios.get(`${API}/projects/${id}`);
      const project = response.data;
      
      setProjectId(id);
      setConfig({
        name: project.name,
        description: project.description || "",
        scope: project.scope,
        database: project.database,
        method: project.method,
        product_weight_grams: project.product_weight_grams,
        product_scenario: project.product_scenario
      });
      
      if (project.input_data) {
        setFormData(project.input_data);
      }
    } catch (error) {
      console.error("Error loading project:", error);
    }
  };

  const steps = schema ? [
    { id: "config", title: "Configuration", description: "Project setup" },
    ...schema.sections.map(s => ({ id: s.id, title: s.title, description: s.description || "" }))
  ] : [];

  const handleConfigChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handleFieldChange = (sectionId, fieldId, value, index = null) => {
    setFormData(prev => {
      const newData = { ...prev };
      if (index !== null) {
        // Repeatable section
        if (!Array.isArray(newData[sectionId])) {
          newData[sectionId] = [{}];
        }
        newData[sectionId] = [...newData[sectionId]];
        newData[sectionId][index] = {
          ...newData[sectionId][index],
          [fieldId]: value
        };
      } else {
        // Single section
        newData[sectionId] = {
          ...newData[sectionId],
          [fieldId]: value
        };
      }
      return newData;
    });
  };

  const addRepeatableItem = (sectionId) => {
    setFormData(prev => ({
      ...prev,
      [sectionId]: [...(prev[sectionId] || []), {}]
    }));
  };

  const removeRepeatableItem = (sectionId, index) => {
    setFormData(prev => ({
      ...prev,
      [sectionId]: prev[sectionId].filter((_, i) => i !== index)
    }));
  };

  const saveProject = async () => {
    setSaving(true);
    try {
      if (!projectId) {
        // Create new project
        const response = await axios.post(`${API}/projects`, {
          name: config.name || `${industry} Assessment`,
          description: config.description,
          industry: industry,
          scope: config.scope,
          database: config.database,
          method: config.method,
          product_weight_grams: config.product_weight_grams || 100,
          product_scenario: config.product_scenario || "Custom"
        });
        setProjectId(response.data.id);
        
        // Save input data
        await axios.put(`${API}/projects/${response.data.id}/input-data`, formData);
        toast.success("Project created successfully");
      } else {
        // Update existing project input data
        await axios.put(`${API}/projects/${projectId}/input-data`, formData);
        toast.success("Project saved successfully");
      }
    } catch (error) {
      console.error("Error saving project:", error);
      toast.error("Failed to save project");
    } finally {
      setSaving(false);
    }
  };

  const runCalculation = async () => {
    if (!projectId) {
      await saveProject();
    }
    
    setCalculating(true);
    try {
      // Ensure we have a project ID
      let currentProjectId = projectId;
      if (!currentProjectId) {
        const response = await axios.post(`${API}/projects`, {
          name: config.name || `${industry} Assessment`,
          description: config.description,
          industry: industry,
          scope: config.scope,
          database: config.database,
          method: config.method,
          product_weight_grams: config.product_weight_grams || 100,
          product_scenario: config.product_scenario || "Custom"
        });
        currentProjectId = response.data.id;
        setProjectId(currentProjectId);
        await axios.put(`${API}/projects/${currentProjectId}/input-data`, formData);
      }
      
      // Start calculation
      await axios.post(`${API}/lca/calculate/${currentProjectId}`);
      toast.success("Calculation started!");
      
      // Poll for results
      const pollForResults = async () => {
        try {
          const projectRes = await axios.get(`${API}/projects/${currentProjectId}`);
          if (projectRes.data.status === "completed") {
            navigate(`/results/${currentProjectId}`);
          } else if (projectRes.data.status === "error") {
            toast.error("Calculation failed. Please try again.");
            setCalculating(false);
          } else {
            setTimeout(pollForResults, 2000);
          }
        } catch (err) {
          console.error("Error polling:", err);
          setCalculating(false);
        }
      };
      
      setTimeout(pollForResults, 2000);
      
    } catch (error) {
      console.error("Error starting calculation:", error);
      toast.error("Failed to start calculation");
      setCalculating(false);
    }
  };

  const renderField = (field, sectionId, index = null) => {
    const value = index !== null 
      ? formData[sectionId]?.[index]?.[field.id] ?? ""
      : formData[sectionId]?.[field.id] ?? "";
    
    const fieldKey = `${sectionId}-${field.id}-${index ?? 0}`;
    
    switch (field.type) {
      case "text":
        return (
          <Input
            key={fieldKey}
            id={fieldKey}
            value={value}
            onChange={(e) => handleFieldChange(sectionId, field.id, e.target.value, index)}
            placeholder={field.placeholder}
            data-testid={`input-${sectionId}-${field.id}`}
          />
        );
      
      case "textarea":
        return (
          <Textarea
            key={fieldKey}
            id={fieldKey}
            value={value}
            onChange={(e) => handleFieldChange(sectionId, field.id, e.target.value, index)}
            placeholder={field.placeholder}
            rows={3}
            data-testid={`textarea-${sectionId}-${field.id}`}
          />
        );
      
      case "number":
        return (
          <div className="input-with-unit">
            <Input
              key={fieldKey}
              id={fieldKey}
              type="number"
              value={value}
              onChange={(e) => handleFieldChange(sectionId, field.id, parseFloat(e.target.value) || 0, index)}
              min={field.min}
              max={field.max}
              step={field.step || "any"}
              className="font-mono"
              data-testid={`input-${sectionId}-${field.id}`}
            />
            {field.unit && <span className="input-unit">{field.unit}</span>}
          </div>
        );
      
      case "select":
        return (
          <Select
            key={fieldKey}
            value={value || ""}
            onValueChange={(val) => handleFieldChange(sectionId, field.id, val, index)}
          >
            <SelectTrigger data-testid={`select-${sectionId}-${field.id}`}>
              <SelectValue placeholder={`Select ${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case "boolean":
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              key={fieldKey}
              id={fieldKey}
              checked={value === true}
              onCheckedChange={(checked) => handleFieldChange(sectionId, field.id, checked, index)}
              data-testid={`checkbox-${sectionId}-${field.id}`}
            />
            <Label htmlFor={fieldKey} className="text-sm text-muted-foreground">
              {field.label}
            </Label>
          </div>
        );
      
      default:
        return (
          <Input
            key={fieldKey}
            id={fieldKey}
            value={value}
            onChange={(e) => handleFieldChange(sectionId, field.id, e.target.value, index)}
            data-testid={`input-${sectionId}-${field.id}`}
          />
        );
    }
  };

  const renderConfigStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">Project Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Project Name *</Label>
              <Input
                id="name"
                value={config.name}
                onChange={(e) => handleConfigChange("name", e.target.value)}
                placeholder="Enter project name"
                data-testid="input-project-name"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="weight">Product Weight *</Label>
              <div className="input-with-unit">
                <Input
                  id="weight"
                  type="number"
                  value={config.product_weight_grams}
                  onChange={(e) => handleConfigChange("product_weight_grams", parseFloat(e.target.value) || 0)}
                  placeholder="e.g., 250"
                  className="font-mono"
                  data-testid="input-product-weight"
                />
                <span className="input-unit">grams</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={config.description}
              onChange={(e) => handleConfigChange("description", e.target.value)}
              placeholder="Optional description"
              rows={2}
              data-testid="input-description"
            />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">LCA Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Assessment Scope *</Label>
              <Select
                value={config.scope}
                onValueChange={(val) => handleConfigChange("scope", val)}
              >
                <SelectTrigger data-testid="select-scope">
                  <SelectValue placeholder="Select scope" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cradle-to-gate">Cradle-to-Gate</SelectItem>
                  <SelectItem value="cradle-to-grave">Cradle-to-Grave</SelectItem>
                  <SelectItem value="both">Both (Comparison)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>LCA Database *</Label>
              <Select
                value={config.database}
                onValueChange={(val) => handleConfigChange("database", val)}
              >
                <SelectTrigger data-testid="select-database">
                  <SelectValue placeholder="Select database" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(databases).map(([key, db]) => (
                    <SelectItem key={key} value={key}>
                      {db.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>LCIA Method *</Label>
              <Select
                value={config.method}
                onValueChange={(val) => handleConfigChange("method", val)}
              >
                <SelectTrigger data-testid="select-method">
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(methods).map(([key, method]) => (
                    <SelectItem key={key} value={key}>
                      {method.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Product Scenario</Label>
              <Input
                value={config.product_scenario}
                onChange={(e) => handleConfigChange("product_scenario", e.target.value)}
                placeholder="e.g., Casual T-shirt cotton"
                data-testid="input-scenario"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSectionStep = (section) => {
    if (section.repeatable) {
      const items = formData[section.id] || [{}];
      return (
        <div className="space-y-4">
          {items.map((item, index) => (
            <Card key={index} className="relative">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg text-primary">
                    {section.title} {index + 1}
                  </CardTitle>
                  {items.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeRepeatableItem(section.id, index)}
                      className="text-red-500 hover:text-red-700"
                      data-testid={`remove-${section.id}-${index}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {section.fields.map((field) => (
                    <div key={field.id} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                      {field.type !== "boolean" && (
                        <Label className="text-sm text-muted-foreground mb-1 block">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                      )}
                      {renderField(field, section.id, index)}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
          
          {(!section.max_items || items.length < section.max_items) && (
            <Button
              variant="outline"
              onClick={() => addRepeatableItem(section.id)}
              className="w-full gap-2 border-dashed"
              data-testid={`add-${section.id}`}
            >
              <Plus className="w-4 h-4" />
              Add {section.title}
            </Button>
          )}
        </div>
      );
    }
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-primary">{section.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {section.fields.map((field) => (
              <div key={field.id} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                {field.type !== "boolean" && (
                  <Label className="text-sm text-slate-600 mb-1 block">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                )}
                {renderField(field, section.id)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading assessment form...</p>
        </div>
      </div>
    );
  }

  if (calculating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-24 h-24 border-4 border-border border-t-primary rounded-full animate-spin mx-auto mb-6" />
          <h2 className="font-heading font-bold text-2xl text-foreground mb-2">Running LCA Calculation</h2>
          <p className="text-muted-foreground mb-2">Powered by Brightway2</p>
          <p className="text-sm text-muted-foreground">This may take a few moments...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="wizard-sidebar w-64 min-h-screen p-6 hidden lg:block sticky top-0">
        <div className="mb-8">
          <button 
            onClick={() => navigate("/")}
            className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
        </div>
        
        <div className="mb-6">
          <h2 className="font-heading font-bold text-lg text-foreground capitalize">{industry} Assessment</h2>
          <p className="text-sm text-muted-foreground">Complete all sections</p>
        </div>
        
        <nav className="space-y-2">
          {steps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => setCurrentStep(index)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                currentStep === index
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent"
              }`}
              data-testid={`step-${step.id}`}
            >
              <div className={`flex-shrink-0 step-indicator ${
                currentStep === index ? "active" :
                currentStep > index ? "completed" : "inactive"
              }`}>
                {currentStep > index ? <CheckCircle2 className="w-4 h-4" /> : index + 1}
              </div>
              <span className="text-sm font-medium flex-1 leading-tight">{step.title}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 lg:p-10">
        <div className="max-w-3xl mx-auto">
          {/* Mobile back button */}
          <div className="lg:hidden mb-6">
            <button 
              onClick={() => navigate("/")}
              className="flex items-center gap-2 text-muted-foreground"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
          </div>
          
          {/* Step Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <span>Step {currentStep + 1} of {steps.length}</span>
            </div>
            <h1 className="font-heading font-bold text-2xl text-foreground">
              {steps[currentStep]?.title}
            </h1>
          </div>
          
          {/* Step Content */}
          <div className="mb-8">
            {currentStep === 0 ? renderConfigStep() : 
              schema && renderSectionStep(schema.sections[currentStep - 1])}
          </div>
          
          {/* Navigation */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-200">
            <Button
              variant="outline"
              onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
              disabled={currentStep === 0}
              className="gap-2"
              data-testid="prev-step"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </Button>
            
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={saveProject}
                disabled={saving}
                className="gap-2"
                data-testid="save-project"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save
              </Button>
              
              {currentStep === steps.length - 1 ? (
                <Button
                  onClick={runCalculation}
                  disabled={!config.name}
                  className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
                  data-testid="run-calculation"
                >
                  <Play className="w-4 h-4" />
                  Run Calculation
                </Button>
              ) : (
                <Button
                  onClick={() => setCurrentStep(prev => Math.min(steps.length - 1, prev + 1))}
                  className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
                  data-testid="next-step"
                >
                  Next
                  <ArrowRight className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
