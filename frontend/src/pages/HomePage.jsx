import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Factory,
  Footprints,
  Building2,
  Battery,
  Apple,
  Droplet,
  History,
  ArrowRight,
  FileText,
  Database,
  BarChart3,
  CheckCircle2,
  LogOut,
  User
} from "lucide-react";
import axios from "axios";
import baWearLogo from "@/assets/bawear-logo.png";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const industries = [
  {
    id: "textile",
    name: "Textile",
    description: "Apparel, fabrics, and textile products",
    icon: Factory,
    image: "https://images.unsplash.com/photo-1684259499086-93cb3e555803?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  },
  {
    id: "bawear",
    name: "Textile - bAwear",
    description: "bAwear textile products and materials",
    icon: Factory,
    image: baWearLogo
  },
  {
    id: "footwear",
    name: "Footwear",
    description: "Shoes, boots, and footwear products",
    icon: Footprints,
    image: "https://images.unsplash.com/photo-1610211967522-17bcf0091ea6?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  },
  {
    id: "construction",
    name: "Construction",
    description: "Building materials and components",
    icon: Building2,
    image: "https://images.unsplash.com/photo-1617357283233-227e9df5966e?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  },
  {
    id: "battery",
    name: "Battery",
    description: "Battery systems and energy storage",
    icon: Battery,
    image: "https://images.unsplash.com/photo-1642721085288-3aa4dad43050?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  },
  {
    id: "food",
    name: "Food",
    description: "Food production and processing",
    icon: Apple,
    image: "https://images.unsplash.com/photo-1542838132-92c53300491e?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  },
  {
    id: "water",
    name: "Water",
    description: "Water treatment and distribution",
    icon: Droplet,
    image: "https://images.unsplash.com/photo-1559827260-dc66d52bef19?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
  }
];

const features = [
  {
    icon: Database,
    title: "Real LCA Databases",
    description: "Powered by USLCI, Agribalyse, and FORWAST databases"
  },
  {
    icon: BarChart3,
    title: "16+ Impact Categories",
    description: "Full ReCiPe and EF 3.1 methodology support"
  },
  {
    icon: FileText,
    title: "PDF Reports",
    description: "Generate detailed assessment reports"
  },
  {
    icon: CheckCircle2,
    title: "Verified Calculations",
    description: "Scientifically validated LCA methodology"
  }
];

export default function HomePage() {
  const navigate = useNavigate();
  const [recentProjects, setRecentProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
    fetchRecentProjects();
  }, []);

  const fetchRecentProjects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/projects`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setRecentProjects(response.data.slice(0, 3));
    } catch (error) {
      console.error("Error fetching projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="app-header sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src="/eufsi-logo.png" 
              alt="EUFSI Logo" 
              className="h-10 object-contain"
            />
          </div>
          <nav className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <User className="w-4 h-4" />
                <span>{user.name}</span>
              </div>
            )}
            <Link to="/history">
              <Button variant="ghost" className="gap-2" data-testid="history-btn">
                <History className="w-4 h-4" />
                History
              </Button>
            </Link>
            <Button 
              variant="ghost" 
              className="gap-2 text-slate-500 hover:text-red-500" 
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-6 blueprint-grid">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="font-heading font-bold text-4xl sm:text-5xl text-slate-900 mb-4">
            Multi-Industry <span className="text-eu-blue">Life Cycle Assessment</span>
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            Comprehensive environmental impact analysis with verified LCA calculations.
            Select an industry to begin your assessment.
          </p>
          
          {/* Features */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12 max-w-4xl mx-auto">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-white/80 backdrop-blur rounded-lg p-4 border border-slate-200 animate-fadeIn"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <feature.icon className="w-6 h-6 text-eu-blue mx-auto mb-2" />
                <h3 className="font-heading font-semibold text-sm text-slate-900">{feature.title}</h3>
                <p className="text-xs text-slate-500 mt-1">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Industry Selection */}
      <section className="py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <h3 className="font-heading font-bold text-2xl text-slate-900 mb-2">Select Industry</h3>
          <p className="text-slate-600 mb-8">Choose the industry for your LCA assessment</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {industries.map((industry) => (
              <Card 
                key={industry.id}
                className="industry-card cursor-pointer h-64 border-0 rounded-xl overflow-hidden"
                onClick={() => navigate(`/new-assessment/${industry.id}`)}
                data-testid={`industry-card-${industry.id}`}
              >
                <img 
                  src={industry.image} 
                  alt={industry.name}
                  className="absolute inset-0 w-full h-full object-cover"
                />
                <CardContent className="relative z-10 h-full flex flex-col justify-end p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <industry.icon className="w-5 h-5 text-white" />
                    <h4 className="font-heading font-bold text-xl text-white">{industry.name}</h4>
                  </div>
                  <p className="text-sm text-white/80">{industry.description}</p>
                  <div className="mt-4 flex items-center gap-2 text-eu-yellow text-sm font-medium">
                    Start Assessment
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Projects */}
      {recentProjects.length > 0 && (
        <section className="py-12 px-6 bg-white border-t border-slate-200">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-heading font-bold text-2xl text-slate-900">Recent Assessments</h3>
                <p className="text-slate-600">Continue where you left off</p>
              </div>
              <Link to="/history">
                <Button variant="outline" className="gap-2">
                  View All
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {recentProjects.map((project) => (
                <Card 
                  key={project.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => project.status === 'completed' 
                    ? navigate(`/results/${project.id}`)
                    : navigate(`/new-assessment/${project.industry}?project=${project.id}`)
                  }
                  data-testid={`recent-project-${project.id}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-heading font-semibold text-slate-900">{project.name}</h4>
                        <p className="text-sm text-slate-500 capitalize">{project.industry}</p>
                      </div>
                      <span className={`badge ${
                        project.status === 'completed' ? 'badge-success' :
                        project.status === 'calculating' ? 'badge-warning' :
                        project.status === 'error' ? 'badge-error' : 'badge-info'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                      <span>{project.scope?.replace('-', ' → ')}</span>
                      <span>•</span>
                      <span>{project.method}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="py-8 px-6 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img 
              src="/eufsi-logo.png" 
              alt="EUFSI Logo" 
              className="h-8 object-contain brightness-0 invert"
            />
          </div>
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} EUFSI • Life Cycle Assessment Tool
          </p>
        </div>
      </footer>
    </div>
  );
}
