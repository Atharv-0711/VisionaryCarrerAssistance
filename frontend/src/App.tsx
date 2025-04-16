import React, { useState, useEffect } from 'react';
import { Brain, BarChart3, BookOpen, Users, LogIn } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import SurveyForm from './components/SurveyForm';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ResourcesPage from './Resources';
import AboutPage from './About';
import PsychiatricInsights from './components/psychatric_insights'; // Ensure this file exists or correct the path

// Define types for the API response data
interface BackgroundAnalysisData {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  average_score: number;
  highly_positive: number;
  positive: number;
  neutral: number;
  negative: number;
  highly_negative: number;
}

interface BehavioralAnalysisData {
  highly_positive_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  highly_negative_count: number;
  average_score: number;
  total_responses: number;
}

interface RoleModelAnalysisData {
  positiveImpact: number;
  neutralImpact: number;
  negativeImpact: number;
  influentialCount: number;
  totalTraits: number;
  topTraits: {
    [key: string]: number;
  };
}

interface IncomeAnalysisData {
  below_poverty_line: number;
  low_income: number;
  below_average: number;
  average: number;
  above_average: number;
  averageIncome: number;
  total_households: number;
  current_thresholds: {
    poverty_line: number;
    low_income: number;
    below_average: number;
    average: number;
  };
}

interface AnalysisData {
  background: BackgroundAnalysisData;
  behavioral: BehavioralAnalysisData;
  rolemodel: RoleModelAnalysisData;
  income: IncomeAnalysisData;
  totalSurveys: number;
}

interface SurveyData {
  id: string;
  timestamp: string;
  sentimentScore: number;
  emotionalTraits: string[];
  cognitiveBias: string[];
  recommendedActions: string[];
  "Name of Child ": string;
  "Background of the Child ": string;
  "Problems in Home ": string;
  "Behavioral Impact": string;
  "Reason for such role model ": string;
}

interface PsychiatricInsightsProps {
  surveyData: SurveyData;
}

interface NavLinkProps {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}

function NavLink({ children, active, onClick }: NavLinkProps) {
  return (
    <button
      onClick={onClick}
      className={`text-sm font-medium ${
        active ? 'text-purple-600' : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      {children}
    </button>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="bg-gray-50 rounded-xl p-6">
      <div className="flex items-center mb-4">{icon}</div>
      <h3 className="text-gray-900 font-medium mb-2">{title}</h3>
      <p className="text-gray-500 text-sm">{description}</p>
    </div>
  );
}

const NavButton = ({ to, label }: { to: string; label: string }) => (
  <Link
    to={to}
    className="text-sm font-medium text-gray-500 hover:text-purple-600 transition-colors"
  >
    {label}
  </Link>
);

const Navbar = ({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (tab: string) => void }) => {
  const navigate = useNavigate();
  
  const handleNavigation = (path: string, tab: string) => {
    navigate(path);
    setActiveTab(tab);
  };
  
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Brain className="h-8 w-8 text-purple-600" />
            <span className="ml-2 text-xl font-bold">
              <span className="text-purple-600">Vision</span>
              <span className="text-orange-500">Path</span>
            </span>
            <span className="ml-3 text-sm text-gray-500 hidden md:block">
              Career Guidance for Every Student
            </span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <button 
              onClick={() => handleNavigation('/dashboard', 'dashboard')}
              className={`text-sm font-medium ${
                activeTab === 'dashboard' ? 'text-purple-600' : 'text-gray-500 hover:text-purple-600 transition-colors'
              }`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => handleNavigation('/resources', 'resources')}
              className={`text-sm font-medium ${
                activeTab === 'resources' ? 'text-purple-600' : 'text-gray-500 hover:text-purple-600 transition-colors'
              }`}
            >
              Resources
            </button>
            <button 
              onClick={() => handleNavigation('/about', 'about')}
              className={`text-sm font-medium ${
                activeTab === 'about' ? 'text-purple-600' : 'text-gray-500 hover:text-purple-600 transition-colors'
              }`}
            >
              About
            </button>
            <button 
              onClick={() => handleNavigation('/survey', 'survey')}
              className={`text-sm font-medium ${
                activeTab === 'survey' ? 'text-purple-600' : 'text-gray-500 hover:text-purple-600 transition-colors'
              }`}
            >
              Take Survey
            </button>
            <button 
              onClick={() => handleNavigation('/', 'home')}
              className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
            >
              Home
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [surveyData, setSurveyData] = useState<SurveyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysisData();
    fetchSurveyData();
  }, []);

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/analysis/complete');
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setError('Failed to load analysis data. Please check your connection or try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSurveyData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/get-surveys');
      if (!response.ok) throw new Error('Survey fetch failed');
      const data = await response.json();
      setSurveyData(data);
    } catch (error) {
      console.error('Error fetching surveys:', error);
    }
  };

  const handleSurveySubmitSuccess = () => {
    fetchAnalysisData();
    fetchSurveyData();
    setActiveTab('dashboard');
  };

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Routes>
            <Route path="/" element={
              <>
                <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
                  <div className="max-w-3xl">
                    <div className="flex items-center mb-6">
                      <Brain className="h-10 w-10 text-purple-600" />
                      <h1 className="text-2xl font-bold ml-4">Visionary Career Assistance</h1>
                    </div>
                    <p className="text-gray-600 mb-6">
                      Empowering students through personalized, data-driven career guidance
                    </p>
                    <p className="text-gray-500 text-sm mb-8">
                      We use advanced analytics and psychological insights to understand your unique circumstances,
                      identify challenges, and guide you toward a career path aligned with your strengths and interests.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                      <FeatureCard
                        icon={<Brain className="h-6 w-6 text-purple-600" />}
                        title="Psychological Insights"
                        description="Detect hidden potential through advanced sentiment analysis"
                      />
                      <FeatureCard
                        icon={<BarChart3 className="h-6 w-6 text-purple-600" />}
                        title="Data-Driven Paths"
                        description="Personalized career recommendations based on your unique profile"
                      />
                      <FeatureCard
                        icon={<Users className="h-6 w-6 text-purple-600" />}
                        title="Mentor Connections"
                        description="Connect with professionals who understand your journey"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className="flex items-center justify-center space-x-2 bg-purple-100 hover:bg-purple-200 text-purple-700 p-4 rounded-xl transition-colors"
                  >
                    <BarChart3 className="h-5 w-5" />
                    <span>Dashboard</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('survey')}
                    className="flex items-center justify-center space-x-2 bg-blue-100 hover:bg-blue-200 text-blue-700 p-4 rounded-xl transition-colors"
                  >
                    <BookOpen className="h-5 w-5" />
                    <span>Take Survey</span>
                  </button>
                </div>
              </>
            } />
            <Route 
              path="/dashboard" 
              element={
                <div className="space-y-8">
                  <AnalyticsDashboard data={analysisData} />
                  <PsychiatricInsights 
                    surveyData={surveyData[surveyData.length - 1]} 
                  />
                </div>
              } 
            />
            <Route path="/survey" element={<SurveyForm onSubmitSuccess={handleSurveySubmitSuccess} />} />
            <Route path="/resources" element={<ResourcesPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;