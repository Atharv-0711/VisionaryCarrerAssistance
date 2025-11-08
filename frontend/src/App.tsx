import React, { useState, useEffect } from 'react';
import { Brain, BarChart3, BookOpen, Users, Menu, X } from 'lucide-react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import io from 'socket.io-client';
import SurveyForm from './components/SurveyForm';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ResourcesPage from './Resources';
import AboutPage from './About';
import PsychiatricInsights from './components/psychatric_insights'; // Ensure this file exists or correct the path
import DataDrivenPaths from './components/DataDrivenPaths';
import MentorConnections from './components/MentorConnections';
import LoginPage from './components/auth/LoginPage';
import SignupPage from './components/auth/SignupPage';
import VerifyEmailPage from './components/auth/VerifyEmailPage';
import { API_BASE_URL, apiRequest } from './utils/api';
import MyAssessments from './components/MyAssessments';
import StudentAssessment from './components/StudentAssessment';

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

type UserRole = 'school_admin' | 'mentor';

interface AuthUser {
  email: string;
  role: UserRole;
  token: string;
}

interface ProtectedRouteProps {
  user: AuthUser | null;
  allowedRoles?: UserRole[];
  children: React.ReactNode;
}

const ProtectedRoute = ({ user, allowedRoles, children }: ProtectedRouteProps) => {
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const Navbar = ({ activeTab, setActiveTab, user, onLogout }: { activeTab: string, setActiveTab: (tab: string) => void, user: AuthUser | null, onLogout: () => void }) => {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const handleNavigation = (path: string, tab: string) => {
    navigate(path);
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  const userLinks = user
    ? [
        {
          key: 'dashboard',
          label: 'Dashboard',
          path: '/dashboard',
        },
        {
          key: 'data-driven',
          label: 'Data-Driven Paths',
          path: '/data-driven',
        },
        {
          key: 'mentors',
          label: 'Mentor Connections',
          path: '/mentors',
        },
        ...(user.role === 'school_admin'
          ? [
              {
                key: 'student-assessment',
                label: 'Take Survey',
                path: '/student-assessment',
              },
            ]
          : []),
        {
          key: 'home',
          label: 'Home',
          path: '/home',
        },
      ]
    : [];

  const guestLinks = [
    { key: 'login', label: 'Login', path: '/login' },
    { key: 'signup', label: 'Sign Up', path: '/signup' },
  ];
  
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
            <span className="ml-3 text-xs sm:text-sm text-gray-500 hidden sm:block">
              Career Guidance for Every Student
            </span>
          </div>

          <div className="md:hidden">
            {user ? (
              <button
                type="button"
                onClick={() => setMobileMenuOpen((prev) => !prev)}
                className="inline-flex items-center justify-center rounded-md p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
                aria-label="Toggle navigation"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="text-sm font-medium text-gray-500 hover:text-purple-600 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>

          <div className="hidden md:flex items-center space-x-8">
            {user ? (
              <>
                {userLinks.map((link) => (
                  <button
                    key={link.key}
                    onClick={() => handleNavigation(link.path, link.key)}
                    className={`text-sm font-medium ${
                      activeTab === link.key
                        ? 'text-purple-600'
                        : 'text-gray-500 hover:text-purple-600 transition-colors'
                    }`}
                  >
                    {link.label}
                  </button>
                ))}
                <button
                  onClick={() => {
                    onLogout();
                    navigate('/login');
                  }}
                  className="text-sm font-medium text-red-500 hover:text-red-600 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              guestLinks.map((link) => (
                <Link
                  key={link.key}
                  to={link.path}
                  className={`text-sm font-medium ${
                    link.key === 'signup'
                      ? 'text-purple-600 hover:text-purple-700'
                      : 'text-gray-500 hover:text-purple-600 transition-colors'
                  }`}
                >
                  {link.label}
                </Link>
              ))
            )}
          </div>
        </div>
      </div>

      {user && mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white shadow-inner">
          <div className="space-y-1 px-4 py-3">
            {userLinks.map((link) => (
              <button
                key={link.key}
                onClick={() => handleNavigation(link.path, link.key)}
                className={`block w-full rounded-md px-3 py-2 text-left text-sm font-medium ${
                  activeTab === link.key
                    ? 'bg-purple-100 text-purple-700'
                    : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
                }`}
              >
                {link.label}
              </button>
            ))}
            <button
              onClick={() => {
                onLogout();
                setMobileMenuOpen(false);
                navigate('/login');
              }}
              className="block w-full rounded-md px-3 py-2 text-left text-sm font-medium text-red-500 hover:bg-red-50 hover:text-red-600"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [surveyData, setSurveyData] = useState<SurveyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [socket, setSocket] = useState<any>(null);
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    const stored = window.localStorage.getItem('authUser');
    if (!stored) {
      return null;
    }
    try {
      const parsed = JSON.parse(stored) as Partial<AuthUser>;
      if (
        parsed &&
        typeof parsed.email === 'string' &&
        (parsed.role === 'school_admin' || parsed.role === 'mentor') &&
        typeof parsed.token === 'string'
      ) {
        return parsed as AuthUser;
      }
      return null;
    } catch (err) {
      console.warn('Failed to parse stored auth user', err);
      return null;
    }
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    if (user) {
      window.localStorage.setItem('authUser', JSON.stringify(user));
    } else {
      window.localStorage.removeItem('authUser');
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      if (socket) {
        socket.disconnect();
        setSocket(null);
      }
      setAnalysisData(null);
      setSurveyData([]);
      return;
    }

    fetchAnalysisData();
    fetchSurveyData();

    const socketConnection = io(API_BASE_URL);
    setSocket(socketConnection);

    socketConnection.on('survey_submitted', (data: any) => {
      setAnalysisData((prevData) => {
        if (!prevData) return prevData;
        return {
          ...prevData,
          totalSurveys: data.totalSurveys,
        };
      });
      fetchSurveyData();
    });

    return () => {
      socketConnection.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchAnalysisData = async () => {
    if (!user) return;
    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest<AnalysisData>(
        `/api/analysis/complete`,
        {
          authToken: user.token,
        }
      );
      setAnalysisData(data);
    } catch (err) {
      console.error('Error fetching analysis:', err);
      setError('Failed to load analysis data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSurveyData = async () => {
    if (!user) return;
    try {
      const data = await apiRequest<any[]>(
        `/api/get-surveys`,
        {
          authToken: user.token,
        }
      );
      setSurveyData(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching surveys:', err);
    }
  };

  const handleSurveySubmitSuccess = () => {
    fetchAnalysisData();
    fetchSurveyData();
    setActiveTab('dashboard');
  };

  const handleLoginSuccess = (authUser: AuthUser): string => {
    setUser(authUser);
    const nextTab = authUser.role === 'school_admin' ? 'dashboard' : 'mentors';
    setActiveTab(nextTab);
    return nextTab === 'dashboard' ? '/dashboard' : '/mentors';
  };

  const handleLogout = () => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
    }
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('authUser');
    }
    setUser(null);
    setActiveTab('home');
    setAnalysisData(null);
    setSurveyData([]);
    setError(null);
    setLoading(false);
  };

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 overflow-x-hidden">
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          user={user}
          onLogout={handleLogout}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-10">
          <Routes>
            <Route
              path="/"
              element={
                <Navigate to={user ? '/home' : '/login'} replace />
              }
            />
            <Route
              path="/login"
              element={<LoginPage onLoginSuccess={handleLoginSuccess} />}
            />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/verify" element={<VerifyEmailPage />} />
            <Route
              path="/home"
              element={
                <ProtectedRoute user={user}>
                  <HomePage setActiveTab={setActiveTab} user={user} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute user={user} allowedRoles={['school_admin']}>
                  <div className="space-y-8">
                    {error && (
                      <div className="rounded-md border border-red-100 bg-red-50 p-4 text-sm text-red-600">
                        {error}
                      </div>
                    )}
                    {loading && !error && (
                      <div className="rounded-md border border-blue-100 bg-blue-50 p-4 text-sm text-blue-600">
                        Loading the latest analytics overview...
                      </div>
                    )}
                    <AnalyticsDashboard data={analysisData} />
                    {surveyData.length > 0 ? (
                      <PsychiatricInsights
                        surveyData={surveyData[surveyData.length - 1]}
                      />
                    ) : (
                      <div className="rounded-md border border-purple-100 bg-white p-6 text-sm text-gray-500">
                        No survey data available yet. Submit a survey to see
                        detailed insights.
                      </div>
                    )}
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/data-driven"
              element={
                <ProtectedRoute user={user}>
                  <DataDrivenPaths />
                </ProtectedRoute>
              }
            />
            <Route
              path="/mentors"
              element={
                <ProtectedRoute user={user}>
                  <MentorConnections />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student-assessment"
              element={
                <ProtectedRoute user={user} allowedRoles={['school_admin']}>
                  {user ? <StudentAssessment authToken={user.token} /> : null}
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessments"
              element={
                <ProtectedRoute user={user}>
                  {user ? <MyAssessments authToken={user.token} /> : null}
                </ProtectedRoute>
              }
            />
            <Route
              path="/survey"
              element={
                <ProtectedRoute user={user} allowedRoles={['school_admin']}>
                  <SurveyForm onSubmitSuccess={handleSurveySubmitSuccess} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resources"
              element={
                <ProtectedRoute user={user}>
                  <ResourcesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/about"
              element={
                <ProtectedRoute user={user}>
                  <AboutPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="*"
              element={
                <Navigate to={user ? '/home' : '/login'} replace />
              }
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

// New HomePage component
const HomePage = ({ setActiveTab, user }: { setActiveTab: (tab: string) => void; user: AuthUser | null }) => {
  const navigate = useNavigate();

  const handleNavigation = (path: string, tab: string) => {
    navigate(path);
    setActiveTab(tab);
  };

  return (
    <>
      <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8 mb-6 sm:mb-8">
        <div className="max-w-3xl">
          <div className="flex items-center mb-5 sm:mb-6">
            <Brain className="h-8 w-8 sm:h-10 sm:w-10 text-purple-600" />
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold ml-3 sm:ml-4 text-gray-900">
              Visionary Career Assistance
            </h1>
          </div>
          <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 leading-relaxed">
            Empowering students through personalized, data-driven career guidance
          </p>
          <p className="text-xs sm:text-sm text-gray-500 mb-6 sm:mb-8 leading-relaxed">
            We use advanced analytics and psychological insights to understand your unique circumstances,
            identify challenges, and guide you toward a career path aligned with your strengths and interests.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            <div 
              className="bg-gray-50 rounded-xl p-5 sm:p-6 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleNavigation('/dashboard', 'dashboard')}
            >
              <div className="flex items-center mb-4">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-gray-900 font-medium mb-1 sm:mb-2 text-sm sm:text-base">
                Psychological Insights
              </h3>
              <p className="text-gray-500 text-xs sm:text-sm leading-relaxed">
                Detect hidden potential through advanced sentiment analysis
              </p>
            </div>

            <div 
              className="bg-gray-50 rounded-xl p-5 sm:p-6 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleNavigation('/data-driven', 'data-driven')}
            >
              <div className="flex items-center mb-4">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-gray-900 font-medium mb-1 sm:mb-2 text-sm sm:text-base">
                Data-Driven Paths
              </h3>
              <p className="text-gray-500 text-xs sm:text-sm leading-relaxed">
                Personalized career recommendations based on your unique profile
              </p>
            </div>

            <div 
              className="bg-gray-50 rounded-xl p-5 sm:p-6 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleNavigation('/mentors', 'mentors')}
            >
              <div className="flex items-center mb-4">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-gray-900 font-medium mb-1 sm:mb-2 text-sm sm:text-base">
                Mentor Connections
              </h3>
              <p className="text-gray-500 text-xs sm:text-sm leading-relaxed">
                Connect with professionals who understand your journey
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <button
          onClick={() => handleNavigation('/dashboard', 'dashboard')}
          className="flex items-center justify-center space-x-2 bg-purple-100 hover:bg-purple-200 text-purple-700 px-4 py-3 sm:p-4 rounded-xl transition-colors text-sm sm:text-base"
        >
          <BarChart3 className="h-5 w-5" />
          <span>Dashboard</span>
        </button>
        {user?.role === 'school_admin' && (
          <button
            onClick={() => handleNavigation('/student-assessment', 'student-assessment')}
            className="flex items-center justify-center space-x-2 bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-3 sm:p-4 rounded-xl transition-colors text-sm sm:text-base"
          >
            <BookOpen className="h-5 w-5" />
            <span>Take Survey</span>
          </button>
        )}
      </div>
    </>
  );
};

export default App;