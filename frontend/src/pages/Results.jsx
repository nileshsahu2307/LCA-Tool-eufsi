import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  Download, 
  Loader2,
  BarChart3,
  PieChart,
  FileText,
  Leaf,
  Droplets,
  Factory,
  Truck,
  Recycle,
  Zap,
  Search
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from "recharts";
import axios from "axios";
import ImpactTrace from "@/components/ImpactTrace";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLORS = ["#004494", "#FFD617", "#10B981", "#EF4444", "#64748B", "#8B5CF6", "#F59E0B", "#06B6D4"];

const stageIcons = {
  raw_materials: Leaf,
  yarn_production: Factory,
  fabric_production: Factory,
  dyeing_finishing: Droplets,
  manufacturing: Factory,
  transport: Truck,
  use_phase: Zap,
  end_of_life: Recycle,
  component_production: Factory,
  assembly: Factory,
  processing: Factory,
  installation: Factory,
  cell_production: Factory,
  pack_assembly: Factory
};

export default function Results() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    loadResults();
  }, [projectId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      
      const [projectRes, resultsRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`),
        axios.get(`${API}/lca/results/${projectId}`)
      ]);
      
      setProject(projectRes.data);
      setResults(resultsRes.data);
      
    } catch (error) {
      console.error("Error loading results:", error);
      toast.error("Failed to load results");
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${API}/reports/${projectId}/pdf`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `LCA_Report_${projectId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("PDF downloaded successfully");
    } catch (error) {
      console.error("Error downloading PDF:", error);
      toast.error("Failed to download PDF");
    } finally {
      setDownloading(false);
    }
  };

  const formatValue = (value, decimals = 4) => {
    if (typeof value !== 'number') return 'N/A';
    if (Math.abs(value) < 0.0001) return value.toExponential(2);
    return value.toFixed(decimals);
  };

  const prepareImpactChartData = () => {
    if (!results?.impact_categories) return [];
    
    return Object.entries(results.impact_categories)
      .slice(0, 10)
      .map(([key, data]) => ({
        name: key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ').substring(0, 20),
        value: data.value,
        unit: data.unit,
        fullName: data.name
      }));
  };

  const prepareContributionData = () => {
    if (!results?.contribution_by_stage?.climate_change) return [];
    
    const contributions = results.contribution_by_stage.climate_change;
    const total = Object.values(contributions).reduce((a, b) => a + b, 0);
    
    return Object.entries(contributions).map(([stage, value]) => ({
      name: stage.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
      value: value,
      percentage: ((value / total) * 100).toFixed(1)
    }));
  };

  const prepareRadarData = () => {
    if (!results?.impact_categories) return [];
    
    const categories = ['climate_change', 'water_depletion', 'acidification', 'eutrophication_freshwater', 'human_toxicity', 'land_use'];
    const maxValues = {};
    
    categories.forEach(cat => {
      const altCat = cat.replace('water_depletion', 'water_use')
        .replace('acidification', 'terrestrial_acidification')
        .replace('eutrophication_freshwater', 'freshwater_eutrophication');
      maxValues[cat] = results.impact_categories[cat]?.value || results.impact_categories[altCat]?.value || 0;
    });
    
    const maxVal = Math.max(...Object.values(maxValues), 1);
    
    return categories.map(cat => {
      const altCat = cat.replace('water_depletion', 'water_use')
        .replace('acidification', 'terrestrial_acidification')
        .replace('eutrophication_freshwater', 'freshwater_eutrophication');
      const value = results.impact_categories[cat]?.value || results.impact_categories[altCat]?.value || 0;
      return {
        category: cat.split('_').map(w => w.charAt(0).toUpperCase()).join(''),
        fullName: cat.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
        value: (value / maxVal) * 100,
        actual: value
      };
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-eu-blue animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!project || !results) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600 mb-4">Results not found</p>
          <Button onClick={() => navigate("/")} data-testid="back-home-btn">
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  const impactChartData = prepareImpactChartData();
  const contributionData = prepareContributionData();
  const radarData = prepareRadarData();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="app-header sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate("/")}
              className="flex items-center gap-2 text-slate-600 hover:text-eu-blue transition-colors"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="border-l border-slate-200 pl-4">
              <h1 className="font-heading font-bold text-lg text-slate-900">{project.name}</h1>
              <p className="text-xs text-slate-500 capitalize">{project.industry} • {project.method}</p>
            </div>
          </div>
          
          <Button 
            onClick={downloadPDF}
            disabled={downloading}
            className="gap-2 bg-eu-blue hover:bg-eu-blue/90"
            data-testid="download-pdf-btn"
          >
            {downloading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Download PDF
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-eu-blue/10 flex items-center justify-center">
                  <Leaf className="w-5 h-5 text-eu-blue" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Climate Change</p>
                  <p className="font-mono font-semibold text-lg" data-testid="climate-change-value">
                    {formatValue(results.impact_categories?.climate_change?.value, 2)}
                  </p>
                  <p className="text-xs text-slate-400">kg CO₂ eq</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                  <Droplets className="w-5 h-5 text-cyan-500" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Water Use</p>
                  <p className="font-mono font-semibold text-lg" data-testid="water-use-value">
                    {formatValue(results.impact_categories?.water_depletion?.value || results.impact_categories?.water_use?.value, 2)}
                  </p>
                  <p className="text-xs text-slate-400">m³</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Fossil Depletion</p>
                  <p className="font-mono font-semibold text-lg" data-testid="fossil-value">
                    {formatValue(results.impact_categories?.fossil_depletion?.value || results.impact_categories?.resource_use_fossils?.value, 2)}
                  </p>
                  <p className="text-xs text-slate-400">kg oil eq / MJ</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Scope</p>
                  <p className="font-semibold text-lg capitalize" data-testid="scope-value">
                    {project.scope?.replace('-', ' → ')}
                  </p>
                  <p className="text-xs text-slate-400">{project.database}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-white border border-slate-200">
            <TabsTrigger value="overview" className="gap-2" data-testid="tab-overview">
              <BarChart3 className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="categories" className="gap-2" data-testid="tab-categories">
              <PieChart className="w-4 h-4" />
              Impact Categories
            </TabsTrigger>
            <TabsTrigger value="contributions" className="gap-2" data-testid="tab-contributions">
              <Factory className="w-4 h-4" />
              Contribution Analysis
            </TabsTrigger>
            <TabsTrigger value="trace" className="gap-2" data-testid="tab-trace">
              <Search className="w-4 h-4" />
              Impact Trace
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-eu-blue">Impact Categories (Top 10)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={impactChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis type="number" tick={{ fontSize: 10 }} />
                        <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 10 }} />
                        <Tooltip 
                          formatter={(value, name, props) => [
                            `${formatValue(value)} ${props.payload.unit}`,
                            props.payload.fullName
                          ]}
                        />
                        <Bar dataKey="value" fill="#004494" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Radar Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-eu-blue">Environmental Profile</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#E2E8F0" />
                        <PolarAngleAxis dataKey="category" tick={{ fontSize: 11 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                        <Tooltip 
                          formatter={(value, name, props) => [
                            `${formatValue(props.payload.actual)}`,
                            props.payload.fullName
                          ]}
                        />
                        <Radar
                          name="Impact"
                          dataKey="value"
                          stroke="#004494"
                          fill="#004494"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Contribution Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-eu-blue">Climate Change Contribution by Life Cycle Stage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPie>
                        <Pie
                          data={contributionData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percentage }) => `${percentage}%`}
                          outerRadius={120}
                          dataKey="value"
                        >
                          {contributionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatValue(value) + " kg CO₂ eq"} />
                      </RechartsPie>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="flex flex-col justify-center space-y-3">
                    {contributionData.map((item, index) => {
                      const Icon = stageIcons[item.name.toLowerCase().replace(/ /g, '_')] || Factory;
                      return (
                        <div key={item.name} className="flex items-center gap-3">
                          <div 
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                          />
                          <Icon className="w-4 h-4 text-slate-400" />
                          <span className="text-sm text-slate-600 flex-1">{item.name}</span>
                          <span className="font-mono text-sm font-medium">{item.percentage}%</span>
                          <span className="font-mono text-xs text-slate-400">{formatValue(item.value, 3)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="categories">
            <Card>
              <CardHeader>
                <CardTitle className="text-eu-blue">All Impact Categories ({project.method})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full data-table">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4">Category</th>
                        <th className="text-left py-3 px-4">Abbreviation</th>
                        <th className="text-right py-3 px-4">Value</th>
                        <th className="text-left py-3 px-4">Unit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(results.impact_categories || {}).map(([key, data]) => (
                        <tr key={key} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-3 px-4 capitalize">
                            {key.replace(/_/g, ' ')}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-500">
                            {data.abbreviation}
                          </td>
                          <td className="py-3 px-4 text-right font-mono">
                            {formatValue(data.value, 6)}
                          </td>
                          <td className="py-3 px-4 text-slate-500 text-sm">
                            {data.unit}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contributions">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {Object.entries(results.contribution_by_stage || {}).slice(0, 6).map(([category, stages]) => {
                const total = Object.values(stages).reduce((a, b) => a + b, 0);
                const categoryInfo = results.impact_categories?.[category];
                
                return (
                  <Card key={category}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-eu-blue capitalize text-base">
                        {category.replace(/_/g, ' ')}
                      </CardTitle>
                      <p className="text-sm text-slate-500">
                        Total: {formatValue(total, 4)} {categoryInfo?.unit || ''}
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(stages).map(([stage, value]) => {
                          const percentage = total > 0 ? (value / total) * 100 : 0;
                          const Icon = stageIcons[stage] || Factory;
                          
                          return (
                            <div key={stage}>
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                  <Icon className="w-4 h-4 text-slate-400" />
                                  <span className="text-sm capitalize">{stage.replace(/_/g, ' ')}</span>
                                </div>
                                <span className="font-mono text-sm">{percentage.toFixed(1)}%</span>
                              </div>
                              <div className="progress-bar">
                                <div 
                                  className="progress-bar-fill"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="trace">
            <ImpactTrace 
              projectId={projectId} 
              industry={project.industry} 
              method={project.method}
            />
          </TabsContent>
        </Tabs>

        {/* Methodology Note */}
        <Card className="mt-8">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-eu-blue/10 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-eu-blue" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-slate-900 mb-1">Methodology</h3>
                <p className="text-sm text-slate-600">
                  This assessment was performed using the EUFSI LCA framework with the 
                  <strong> {project.database}</strong> database and <strong>{project.method}</strong> impact assessment method.
                  The scope of this analysis is <strong>{project.scope?.replace('-', ' to ')}</strong>.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="py-6 px-6 bg-white border-t border-slate-200 mt-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-slate-500">
          <span>EUFSI • Life Cycle Assessment</span>
          <span>© {new Date().getFullYear()} EUFSI</span>
        </div>
      </footer>
    </div>
  );
}
