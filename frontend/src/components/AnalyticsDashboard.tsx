import React from 'react';
import { BarChart3, Users, Brain, School } from 'lucide-react';

// Define TypeScript interfaces for our data structure
interface BackgroundDetail {
  background: string;
  score: number;
  category: string;
}

interface BackgroundData {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  average_score: number;
  highly_positive: number;
  positive: number;
  neutral: number;
  negative: number;
  highly_negative: number;
  background_details?: BackgroundDetail[];
}

interface BehavioralData {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  [key: string]: any;
}

interface RoleModelData {
  influentialCount: number;
  [key: string]: any;
}

interface IncomeData {
  averageIncome: number;
  [key: string]: any;
}

interface AnalyticsData {
  totalSurveys: number;
  background: BackgroundData;
  behavioral: BehavioralData;
  rolemodel: RoleModelData;
  income: IncomeData;
}

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: number | string;
  label?: string;
  color: 'purple' | 'blue' | 'green' | 'orange';
}

interface AnalysisCardProps {
  title: string;
  data: any;
  color: 'purple' | 'blue' | 'green' | 'orange';
}

const AnalyticsDashboard: React.FC<{ data: AnalyticsData | null }> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-lg text-gray-500">Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard 
          icon={<Users size={24} />}
          title="Total Surveys"
          value={data.totalSurveys}
          color="purple"
        />
        <StatCard 
          icon={<Brain size={24} />}
          title="Behavioral Analysis"
          value={data.behavioral?.positive_count || 0}
          label="Positive Responses"
          color="blue"
        />
        <StatCard 
          icon={<School size={24} />}
          title="Role Models"
          value={data.rolemodel?.influentialCount || 0}
          label="Influential Figures"
          color="green"
        />
        <StatCard 
          icon={<BarChart3 size={24} />}
          title="Family Income"
          value={data.income?.averageIncome?.toFixed(2) || 0}
          label="Average Monthly"
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <AnalysisCard 
          title="Background Analysis" 
          data={data.background} 
          color="purple" 
        />
        <AnalysisCard 
          title="Behavioral Impact" 
          data={data.behavioral} 
          color="blue" 
        />
        <AnalysisCard 
          title="Role Model Influence" 
          data={data.rolemodel} 
          color="green" 
        />
        <AnalysisCard 
          title="Family Income Analysis" 
          data={data.income} 
          color="orange" 
        />
      </div>
    </div>
  );
};

const StatCard: React.FC<StatCardProps> = ({ icon, title, value, label, color }) => {
  const colorClasses = {
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 h-full">
      <div className="flex flex-col">
        <div className={`p-2.5 sm:p-3 rounded-full inline-block ${colorClasses[color]}`}>
          {icon}
        </div>
        <div className="mt-3 sm:mt-4">
          <h3 className="text-gray-500 text-xs sm:text-sm font-medium">
            {title}
          </h3>
          <p className="text-xl sm:text-2xl font-bold leading-tight">
            {value}
          </p>
          {label && <p className="text-gray-500 text-xs sm:text-sm">
            {label}
          </p>}
        </div>
      </div>
    </div>
  );
};

const AnalysisCard: React.FC<AnalysisCardProps> = ({ title, data, color }) => {
  const colorClasses = {
    purple: 'border-purple-200',
    blue: 'border-blue-200',
    green: 'border-green-200',
    orange: 'border-orange-200',
  };

  // Function to handle rendering of values that might be objects
  const renderValue = (key: string, value: any) => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    // Skip rendering background_details completely - THIS IS THE CHANGE
    if (key === 'background_details') {
      return null;
    }
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      // If the value is an object (but not an array), render it as a nested list
      return (
        <div className="pl-4 mt-2">
          {Object.entries(value).map(([nestedKey, nestedValue]) => (
            <div key={nestedKey} className="flex justify-between py-1">
              <span className="font-medium text-gray-600">{nestedKey.replace(/_/g, ' ')}</span>
              <span>{typeof nestedValue === 'number' ? (nestedValue as number).toFixed(2) : String(nestedValue)}</span>
            </div>
          ))}
        </div>
      );
    }
    
    // Format numbers to 2 decimal places if they're numbers
    return typeof value === 'number' ? (value as number).toFixed(2) : String(value);
  };

  return (
    <div className={`bg-white rounded-2xl shadow-sm p-5 sm:p-6 border-l-4 ${colorClasses[color]}`}>
      <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">{title}</h3>
      <div className="divide-y">
        {data && Object.entries(data).map(([key, value]) => (
          // Skip background_details entries completely - THIS IS ANOTHER OPTION
          key !== 'background_details' ? (
            <div key={key} className="py-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2">
                <span className="font-medium text-sm sm:text-base">{key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1)}</span>
                {typeof value !== 'object' && <span className="text-xs sm:text-sm text-gray-600">{renderValue(key, value)}</span>}
              </div>
              {typeof value === 'object' && value !== null && renderValue(key, value)}
            </div>
          ) : null
        ))}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
