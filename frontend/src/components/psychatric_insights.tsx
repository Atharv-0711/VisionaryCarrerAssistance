import React, { useEffect, useState } from 'react';
import Sentiment from 'sentiment';

interface SurveyData {
  [key: string]: any;
}

const PsychiatricInsights: React.FC<{ surveyData?: SurveyData }> = ({ surveyData }) => {
  const [sentiments, setSentiments] = useState<{
    background?: { score: number };
    problems?: { score: number };
    behavior?: { score: number };
    reason?: { score: number };
  }>({});

  useEffect(() => {
    if (surveyData) {
      const sentiment = new Sentiment();
      const analyzeField = (field: string | null | undefined) => 
        field ? sentiment.analyze(field) : undefined;

      setSentiments({
        background: analyzeField(surveyData["Background of the Child "] || null),
        problems: analyzeField(surveyData["Problems in Home "] || null),
        behavior: analyzeField(surveyData["Behavioral Impact"] || null),
        reason: analyzeField(surveyData["Reason for such role model "] || null)
      });
    }
  }, [surveyData]);

  if (!surveyData) return null;

  const getDisplayValue = (value: any) => {
    if (value === null || value === undefined) return 'Not provided';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'string' && value.trim() === '') return 'Not provided';
    return value;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-8">
      <h3 className="text-xl font-semibold mb-4">Psychological Insights</h3>
      
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Child Background</h4>
            <p className="text-gray-600">
              {getDisplayValue(surveyData["Background of the Child "])}
            </p>
            <p className="mt-2 text-sm">
              Sentiment: {sentiments.background?.score ?? 'N/A'}
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Home Environment</h4>
            <p className="text-gray-600">
              {getDisplayValue(surveyData["Problems in Home "])}
            </p>
            <p className="mt-2 text-sm">
              Sentiment: {sentiments.problems?.score ?? 'N/A'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Behavioral Impact</h4>
            <p className="text-gray-600">
              {getDisplayValue(surveyData["Behavioral Impact"])}
            </p>
            <p className="mt-2 text-sm">
              Sentiment: {sentiments.behavior?.score ?? 'N/A'}
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Role Model Influence</h4>
            <p className="text-gray-600">
              {getDisplayValue(surveyData["Reason for such role model "])}
            </p>
            <p className="mt-2 text-sm">
              Sentiment: {sentiments.reason?.score ?? 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PsychiatricInsights;