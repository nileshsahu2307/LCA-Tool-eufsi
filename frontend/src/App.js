import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import HomePage from "./pages/HomePage";
import NewAssessment from "./pages/NewAssessment";
import Results from "./pages/Results";
import History from "./pages/History";
import AuthPage from "./pages/AuthPage";
import "@/App.css";

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <div className="App min-h-screen bg-slate-50">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          } />
          <Route path="/new-assessment" element={
            <ProtectedRoute>
              <NewAssessment />
            </ProtectedRoute>
          } />
          <Route path="/new-assessment/:industry" element={
            <ProtectedRoute>
              <NewAssessment />
            </ProtectedRoute>
          } />
          <Route path="/results/:projectId" element={
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          } />
          <Route path="/history" element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
