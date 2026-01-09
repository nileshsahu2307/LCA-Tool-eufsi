import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { toast } from "sonner";
import { 
  Search, 
  Loader2, 
  ChevronDown, 
  ChevronRight,
  Factory,
  Zap,
  ArrowRight,
  Info,
  FlaskConical
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ImpactTrace({ projectId, industry, method }) {
  const [stages, setStages] = useState([]);
  const [impactCategories, setImpactCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("climate_change");
  const [selectedStage, setSelectedStage] = useState("");
  const [traceResult, setTraceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedActivities, setExpandedActivities] = useState({});

  useEffect(() => {
    loadStagesAndCategories();
  }, [industry, method]);

  const loadStagesAndCategories = async () => {
    try {
      const [stagesRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/lca/stages/${industry}`),
        axios.get(`${API}/lca/impact-categories/${method}`)
      ]);
      
      setStages(stagesRes.data.stages);
      if (stagesRes.data.stages.length > 0) {
        setSelectedStage(stagesRes.data.stages[0].id);
      }
      
      // Convert categories object to array
      const cats = Object.entries(categoriesRes.data.categories).map(([key, value]) => ({
        id: key,
        ...value
      }));
      setImpactCategories(cats);
      
    } catch (error) {
      console.error("Error loading trace options:", error);
    }
  };

  const runTrace = async () => {
    if (!selectedCategory || !selectedStage) {
      toast.error("Please select both an impact category and life cycle stage");
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/lca/trace/${projectId}?impact_category=${selectedCategory}&life_cycle_stage=${selectedStage}`
      );
      setTraceResult(response.data);
      // Expand all activities by default
      const expanded = {};
      response.data.activities?.forEach((_, idx) => {
        expanded[idx] = true;
      });
      setExpandedActivities(expanded);
    } catch (error) {
      console.error("Error running trace:", error);
      toast.error("Failed to trace impact origin");
    } finally {
      setLoading(false);
    }
  };

  const toggleActivity = (index) => {
    setExpandedActivities(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatValue = (value, decimals = 6) => {
    if (typeof value !== 'number') return 'N/A';
    if (Math.abs(value) < 0.000001) return value.toExponential(2);
    if (Math.abs(value) < 0.001) return value.toExponential(3);
    return value.toFixed(decimals);
  };

  return (
    <div className="space-y-6">
      {/* Selection Controls */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-eu-blue flex items-center gap-2">
            <Search className="w-5 h-5" />
            Impact Traceability
          </CardTitle>
          <p className="text-sm text-slate-500">
            Trace the origin of impact results to see which activities, exchanges, and characterization factors contribute
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Impact Category</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger data-testid="select-trace-category">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {impactCategories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.name || cat.id.replace(/_/g, ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Life Cycle Stage</label>
              <Select value={selectedStage} onValueChange={setSelectedStage}>
                <SelectTrigger data-testid="select-trace-stage">
                  <SelectValue placeholder="Select stage" />
                </SelectTrigger>
                <SelectContent>
                  {stages.map((stage) => (
                    <SelectItem key={stage.id} value={stage.id}>
                      {stage.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button 
                onClick={runTrace}
                disabled={loading || !selectedCategory || !selectedStage}
                className="w-full bg-eu-blue hover:bg-eu-blue/90 gap-2"
                data-testid="run-trace-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Trace Impact
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trace Results */}
      {traceResult && (
        <>
          {/* Summary Card */}
          <Card className="border-eu-blue/20 bg-eu-blue/5">
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Impact Category</p>
                  <p className="font-semibold text-slate-900 capitalize">
                    {traceResult.impact_category?.replace(/_/g, ' ')}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Life Cycle Stage</p>
                  <p className="font-semibold text-slate-900 capitalize">
                    {traceResult.life_cycle_stage?.replace(/_/g, ' ')}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Total Stage Impact</p>
                  <p className="font-mono font-semibold text-eu-blue">
                    {formatValue(traceResult.total_stage_impact, 4)} {traceResult.summary?.unit}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Product Weight</p>
                  <p className="font-mono font-semibold text-slate-900">
                    {traceResult.product_weight_kg} kg
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Methodology */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Info className="w-4 h-4 text-slate-400" />
                Calculation Methodology
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 mb-3">{traceResult.methodology?.description}</p>
              <div className="bg-slate-50 rounded-lg p-3 font-mono text-sm">
                {traceResult.methodology?.formula}
              </div>
              
              {/* Characterization Factors Used */}
              <div className="mt-4">
                <p className="text-sm font-medium text-slate-700 mb-2">Characterization Factors Applied:</p>
                <div className="flex flex-wrap gap-2">
                  {traceResult.methodology?.characterization_factors_used?.map((cf, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-amber-50 text-amber-800 rounded text-xs font-mono"
                    >
                      <FlaskConical className="w-3 h-3" />
                      {cf.emission}: {cf.factor} {cf.unit}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Activities Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Factory className="w-5 h-5 text-eu-blue" />
                  Activities & Exchanges ({traceResult.summary?.num_activities} activities, {traceResult.summary?.num_exchanges} exchanges)
                </span>
                {traceResult.summary?.dominant_activity && (
                  <span className="text-sm font-normal text-slate-500">
                    Dominant: <span className="font-medium text-eu-blue">{traceResult.summary.dominant_activity}</span>
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {traceResult.activities?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Zap className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                  <p>No activities with relevant exchanges found for this combination</p>
                  <p className="text-sm mt-1">Try selecting a different impact category or life cycle stage</p>
                </div>
              ) : (
                traceResult.activities?.map((activity, actIdx) => (
                  <Collapsible 
                    key={actIdx}
                    open={expandedActivities[actIdx]}
                    onOpenChange={() => toggleActivity(actIdx)}
                  >
                    <CollapsibleTrigger asChild>
                      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors">
                        <div className="flex items-center gap-3">
                          {expandedActivities[actIdx] ? (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-400" />
                          )}
                          <Factory className="w-5 h-5 text-eu-blue" />
                          <div>
                            <p className="font-medium text-slate-900">{activity.activity_name}</p>
                            <p className="text-xs text-slate-500 font-mono">{activity.activity_code}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-mono font-semibold text-eu-blue">
                            {formatValue(activity.subtotal_impact, 4)}
                          </p>
                          <p className="text-xs text-slate-500">{traceResult.summary?.unit}</p>
                        </div>
                      </div>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent>
                      <div className="ml-8 mt-2 border-l-2 border-slate-200 pl-4 space-y-2">
                        {activity.exchanges?.map((exchange, exIdx) => (
                          <div 
                            key={exIdx}
                            className="p-3 bg-white rounded border border-slate-100"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <Zap className="w-4 h-4 text-amber-500" />
                                  <span className="font-medium text-sm">{exchange.flow_name}</span>
                                </div>
                                
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                  <div>
                                    <p className="text-slate-500">Flow Amount</p>
                                    <p className="font-mono">{formatValue(exchange.flow_amount)} {exchange.flow_unit}</p>
                                  </div>
                                  <div>
                                    <p className="text-slate-500">Emission</p>
                                    <p className="font-mono">{exchange.emission_name}: {formatValue(exchange.emission_amount)} {exchange.emission_unit}</p>
                                  </div>
                                  <div>
                                    <p className="text-slate-500">Char. Factor</p>
                                    <p className="font-mono">{exchange.characterization_factor} {exchange.cf_unit}</p>
                                  </div>
                                  <div>
                                    <p className="text-slate-500">Impact</p>
                                    <p className="font-mono font-semibold text-green-600">
                                      {formatValue(exchange.impact_contribution, 4)}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            {/* Calculation breakdown */}
                            <div className="mt-2 pt-2 border-t border-slate-100">
                              <p className="text-xs text-slate-400 font-mono flex items-center gap-1">
                                <ArrowRight className="w-3 h-3" />
                                {formatValue(exchange.emission_amount)} {exchange.emission_unit} × {exchange.characterization_factor} = {formatValue(exchange.impact_contribution)} {traceResult.summary?.unit}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                ))
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
