import React, { useState, useEffect } from 'react';
import { Brain, BarChart3, BookOpen, Users, LogIn } from 'lucide-react';
import SurveyForm from './components/SurveyForm';
import AnalyticsDashboard from './components/AnalyticsDashboard';

// Define types for the API response data based on backend structure
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

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysisData();
  }, []);

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('http://localhost:5000/api/analysis/complete');
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Fetched analysis data:', data);
      setAnalysisData(data);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setError('Failed to load analysis data. Please check your connection or try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSurveySubmitSuccess = () => {
    // Refresh data after survey submission
    fetchAnalysisData();
    // Switch to dashboard view to show updated results
    setActiveTab('dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Navigation */}
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
              <NavLink active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')}>
                Dashboard
              </NavLink>
              <NavLink active={activeTab === 'resources'} onClick={() => setActiveTab('resources')}>
                Resources
              </NavLink>
              <NavLink active={activeTab === 'mentors'} onClick={() => setActiveTab('mentors')}>
                Mentors
              </NavLink>
              <NavLink active={activeTab === 'about'} onClick={() => setActiveTab('about')}>
                About
              </NavLink>
              <button className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors">
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {activeTab === 'home' && (
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
        )}

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

        {activeTab === 'survey' && <SurveyForm onSubmitSuccess={handleSurveySubmitSuccess} />}
        {activeTab === 'dashboard' && <AnalyticsDashboard data={analysisData} />}
      </main>
    </div>
  );
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

export default App;
