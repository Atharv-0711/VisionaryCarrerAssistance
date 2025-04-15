import React from 'react';
import { BarChart3, Users, Brain, School } from 'lucide-react';
import DataChartComponent from './DataChartComponent';

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
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
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

      {/* Charts Section */}
      <DataChartComponent 
        data={{
          ...data,
          income: {
            below_poverty_line: data.income?.below_poverty_line || 0,
            below_average: data.income?.below_average || 0,
            average: data.income?.average || 0,
            above_average: data.income?.above_average || 0,
            high_income: data.income?.high_income || 0,
          }
        }} 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
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
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex flex-col">
        <div className={`p-3 rounded-full inline-block ${colorClasses[color]}`}>
          {icon}
        </div>
        <div className="mt-4">
          <h3 className="text-gray-500 text-sm font-medium">
            {title}
          </h3>
          <p className="text-2xl font-bold">
            {value}
          </p>
          {label && <p className="text-gray-500 text-sm">
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
    <div className={`bg-white rounded-lg shadow p-6 border-l-4 ${colorClasses[color]}`}>
      <h3 className="text-lg font-medium mb-4">{title}</h3>
      <div className="divide-y">
        {data && Object.entries(data).map(([key, value]) => (
          // Skip background_details entries completely - THIS IS ANOTHER OPTION
          key !== 'background_details' ? (
            <div key={key} className="py-2">
              <div className="flex justify-between">
                <span className="font-medium">{key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1)}</span>
                {typeof value !== 'object' && <span>{renderValue(key, value)}</span>}
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
