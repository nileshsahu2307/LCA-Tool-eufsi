import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { 
  ArrowLeft,
  Search,
  Trash2,
  BarChart3,
  FileText,
  Loader2,
  Factory,
  Footprints,
  Building2,
  Battery,
  Filter
} from "lucide-react";
import { Input } from "@/components/ui/input";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const industryIcons = {
  textile: Factory,
  footwear: Footprints,
  construction: Building2,
  battery: Battery
};

const statusColors = {
  draft: "badge-info",
  calculating: "badge-warning",
  completed: "badge-success",
  error: "badge-error"
};

export default function History() {
  const navigate = useNavigate();
  
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterIndustry, setFilterIndustry] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error("Error loading projects:", error);
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = async (projectId, e) => {
    e.stopPropagation();
    
    if (!window.confirm("Are you sure you want to delete this project?")) {
      return;
    }
    
    setDeleting(projectId);
    try {
      await axios.delete(`${API}/projects/${projectId}`);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      toast.success("Project deleted successfully");
    } catch (error) {
      console.error("Error deleting project:", error);
      toast.error("Failed to delete project");
    } finally {
      setDeleting(null);
    }
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesIndustry = filterIndustry === "all" || project.industry === filterIndustry;
    const matchesStatus = filterStatus === "all" || project.status === filterStatus;
    
    return matchesSearch && matchesIndustry && matchesStatus;
  });

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-eu-blue animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading projects...</p>
        </div>
      </div>
    );
  }

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
              <h1 className="font-heading font-bold text-lg text-slate-900">Assessment History</h1>
              <p className="text-xs text-slate-500">{projects.length} total projects</p>
            </div>
          </div>
          
          <Button 
            onClick={() => navigate("/")}
            className="gap-2 bg-eu-blue hover:bg-eu-blue/90"
            data-testid="new-assessment-btn"
          >
            <FileText className="w-4 h-4" />
            New Assessment
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="search-input"
            />
          </div>
          
          <Select value={filterIndustry} onValueChange={setFilterIndustry}>
            <SelectTrigger className="w-full md:w-48" data-testid="filter-industry">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Industry" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Industries</SelectItem>
              <SelectItem value="textile">Textile</SelectItem>
              <SelectItem value="footwear">Footwear</SelectItem>
              <SelectItem value="construction">Construction</SelectItem>
              <SelectItem value="battery">Battery</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-full md:w-48" data-testid="filter-status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="calculating">Calculating</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="error">Error</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Projects Grid */}
        {filteredProjects.length === 0 ? (
          <div className="text-center py-16">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="font-heading font-semibold text-slate-900 mb-2">No Projects Found</h3>
            <p className="text-slate-500 mb-4">
              {projects.length === 0 
                ? "You haven't created any assessments yet."
                : "No projects match your search criteria."}
            </p>
            <Button onClick={() => navigate("/")} className="bg-eu-blue hover:bg-eu-blue/90">
              Start New Assessment
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => {
              const Icon = industryIcons[project.industry] || Factory;
              
              return (
                <Card 
                  key={project.id}
                  className="cursor-pointer hover:shadow-lg transition-all group"
                  onClick={() => project.status === 'completed' 
                    ? navigate(`/results/${project.id}`)
                    : navigate(`/new-assessment/${project.industry}?project=${project.id}`)
                  }
                  data-testid={`project-card-${project.id}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-eu-blue/10 flex items-center justify-center">
                          <Icon className="w-5 h-5 text-eu-blue" />
                        </div>
                        <div>
                          <h3 className="font-heading font-semibold text-slate-900 group-hover:text-eu-blue transition-colors">
                            {project.name}
                          </h3>
                          <p className="text-sm text-slate-500 capitalize">{project.industry}</p>
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => deleteProject(project.id, e)}
                        disabled={deleting === project.id}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500"
                        data-testid={`delete-project-${project.id}`}
                      >
                        {deleting === project.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                    
                    {project.description && (
                      <p className="text-sm text-slate-500 mb-4 line-clamp-2">
                        {project.description}
                      </p>
                    )}
                    
                    <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>{project.scope?.replace('-', ' → ')}</span>
                        <span>•</span>
                        <span>{project.method}</span>
                      </div>
                      
                      <span className={`badge ${statusColors[project.status] || 'badge-info'}`}>
                        {project.status}
                      </span>
                    </div>
                    
                    <p className="text-xs text-slate-400 mt-3">
                      {formatDate(project.updated_at || project.created_at)}
                    </p>
                    
                    {project.status === 'completed' && (
                      <div className="mt-4 flex items-center gap-2 text-eu-blue text-sm">
                        <BarChart3 className="w-4 h-4" />
                        View Results
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
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
