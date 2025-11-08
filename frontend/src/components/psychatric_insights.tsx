import React, { useEffect, useState, useMemo, useCallback } from 'react';
import Sentiment from 'sentiment';

interface SurveyData {
  [key: string]: any;
}

type SentimentEntry = {
  score: number;
  source?: 'backend' | 'domain' | 'lexicon';
};

type KeywordRule = {
  keywords: (string | RegExp)[];
  score: number;
};

const clampScore = (score: number): number =>
  Number(Math.min(5, Math.max(1, score)).toFixed(2));

const matchesKeyword = (text: string, keyword: string | RegExp): boolean => {
  if (keyword instanceof RegExp) {
    return keyword.test(text);
  }

  const sanitizedKeyword = keyword.trim().toLowerCase();
  if (!sanitizedKeyword) {
    return false;
  }

  const escapedKeyword = sanitizedKeyword
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\s+/g, '\\s+');
  const pattern = new RegExp(`\\b${escapedKeyword}\\b`, 'i');
  return pattern.test(text);
};

const scoreFromRules = (text: string, rules: KeywordRule[]): number | null => {
  if (!rules.length) {
    return null;
  }

  const normalizedText = text.toLowerCase();
  let total = 0;
  let matches = 0;

  for (const rule of rules) {
    if (rule.keywords.some((keyword) => matchesKeyword(normalizedText, keyword))) {
      total += rule.score;
      matches += 1;
    }
  }

  if (!matches) {
    return null;
  }

  const average = total / matches;
  return clampScore(average);
};

const HOME_ENVIRONMENT_RULES: KeywordRule[] = [
  {
    keywords: [
      /\bfinancial\b/,
      /\bmoney\b/,
      /\bdebt\b/,
      /\bpoverty\b/,
      /\bloan\b/,
      /\beconomic\b/,
      /\bjob loss\b/,
      /\bunemployment\b/,
      /\bmonetary\b/,
    ],
    score: 2,
  },
  {
    keywords: [
      /\bviolence\b/,
      /\bviolent\b/,
      /\babuse\b/,
      /\babusive\b/,
      /\btoxic\b/,
      /\bunsafe\b/,
      /\baddiction\b/,
      /\balcohol\b/,
      /\bdrugs?\b/,
      /\bneglect\b/,
    ],
    score: 1,
  },
  {
    keywords: [
      /\bsupportive\b/,
      /\bloving\b/,
      /\bcaring\b/,
      /\bnurturing\b/,
      /\bsafe\b/,
      /\bsecure\b/,
      /\bstable\b/,
      /\bpeaceful\b/,
      /\bhealthy\b/,
      /\bpositive\b/,
      /\bencouraging\b/,
      /\bharmonious\b/,
      /\bcalm\b/,
    ],
    score: 4.5,
  },
  {
    keywords: [
      /\bconflict\b/,
      /\barguments?\b/,
      /\bfights?\b/,
      /\bstress\b/,
      /\billness\b/,
      /\bill\b/,
      /\bsick\b/,
      /\bcrowded\b/,
      /\black of\b/,
    ],
    score: 2.5,
  },
  {
    keywords: [
      /\bnone\b/,
      /\bno problem\b/,
      /\bnot applicable\b/,
      /\bnothing\b/,
      /\bna\b/,
    ],
    score: 3,
  },
];

const ROLE_MODEL_RULES: KeywordRule[] = [
  {
    keywords: [/\bteacher\b/, /\bprofessor\b/, /\beducator\b/, /\binstructor\b/, /\bmentor\b/],
    score: 5,
  },
  {
    keywords: [/\barmy\b/, /\bsoldier\b/, /\bdefence\b/, /\bdefense\b/, /\bnavy\b/, /\bair force\b/],
    score: 4.5,
  },
  {
    keywords: [/\bdoctor\b/, /\bnurse\b/, /\bmedical\b/, /\bhealthcare\b/, /\bsurgeon\b/],
    score: 5,
  },
  {
    keywords: [/\bscientist\b/, /\bengineer\b/, /\bresearcher\b/, /\binnovator\b/, /\btechnologist\b/],
    score: 4.5,
  },
  {
    keywords: [/\bentrepreneur\b/, /\bbusiness\b/, /\bfounder\b/, /\bstartup\b/],
    score: 4,
  },
  {
    keywords: [/\bparent\b/, /\bmother\b/, /\bfather\b/, /\bguardian\b/, /\bfamily\b/],
    score: 4,
  },
  {
    keywords: [/\bpolice\b/, /\bias\b/, /\bips\b/, /\bcivil servant\b/, /\bcollector\b/],
    score: 4.5,
  },
  {
    keywords: [/\bathlete\b/, /\bsportsperson\b/, /\bplayer\b/, /\bcricketer\b/, /\bfootballer\b/],
    score: 4,
  },
  {
    keywords: [/\bartist\b/, /\bactor\b/, /\bsinger\b/, /\bdancer\b/, /\bcelebrity\b/],
    score: 3.5,
  },
  {
    keywords: [/\binspiration\b/, /\bmotivated\b/, /\binspire\b/, /\bvisionary\b/],
    score: 4,
  },
  {
    keywords: [/\bnone\b/, /\bnot sure\b/, /\bnothing\b/, /\bna\b/],
    score: 2.5,
  },
];

const toBackendScore = (value: unknown): number | undefined => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return undefined;
  }
  return Number(numericValue.toFixed(2));
};

const PsychiatricInsights: React.FC<{ surveyData?: SurveyData }> = ({ surveyData }) => {
  const [sentiments, setSentiments] = useState<{
    background?: SentimentEntry;
    problems?: SentimentEntry;
    behavior?: SentimentEntry;
    reason?: SentimentEntry;
  }>({});

  const sentimentAnalyzer = useMemo(() => new Sentiment(), []);

  const analyzeFieldWithRules = useCallback(
    (value: unknown, rules?: KeywordRule[]): SentimentEntry | undefined => {
      if (value === null || value === undefined) {
        return undefined;
      }

      const text = String(value).trim();
      if (!text) {
        return undefined;
      }

      const ruleScore =
        rules && rules.length > 0 ? scoreFromRules(text, rules) : null;

      if (ruleScore !== null) {
        return { score: ruleScore, source: 'domain' };
      }

      const genericResult = sentimentAnalyzer.analyze(text);
      if (typeof genericResult?.score === 'number') {
        const fivePointScore = clampScore(3 + genericResult.score);
        return { score: fivePointScore, source: 'lexicon' };
      }

      return undefined;
    },
    [sentimentAnalyzer],
  );

  useEffect(() => {
    if (surveyData) {
      const backendAnalysis = (surveyData as any)?.analysis;
      const roleReasonSource =
        (surveyData['Reason for such role model '] ?? surveyData['Role models']) ||
        null;

      // Backend-derived scores when available
      const bgScore =
        backendAnalysis?.background?.analysis?.background_details?.[0]?.score ??
        backendAnalysis?.background?.analysis?.average_score;
      const behaviorScore = backendAnalysis?.behavioral?.analysis?.average_score;

      const nextSentiments: {
        background?: SentimentEntry;
        problems?: SentimentEntry;
        behavior?: SentimentEntry;
        reason?: SentimentEntry;
      } = {};

      const backendBackgroundScore = toBackendScore(bgScore);
      if (backendBackgroundScore !== undefined) {
        nextSentiments.background = {
          score: backendBackgroundScore,
          source: 'backend',
        };
      } else {
        const fallbackBackground = analyzeFieldWithRules(
          surveyData['Background of the Child '] || null,
        );
        if (fallbackBackground) {
          nextSentiments.background = fallbackBackground;
        }
      }

      const backendBehaviorScore = toBackendScore(behaviorScore);
      if (backendBehaviorScore !== undefined) {
        nextSentiments.behavior = {
          score: backendBehaviorScore,
          source: 'backend',
        };
      } else {
        const fallbackBehavior = analyzeFieldWithRules(
          surveyData['Behavioral Impact'] || null,
        );
        if (fallbackBehavior) {
          nextSentiments.behavior = fallbackBehavior;
        }
      }

      const homeEnvironmentSentiment = analyzeFieldWithRules(
        surveyData['Problems in Home '] || null,
        HOME_ENVIRONMENT_RULES,
      );
      if (homeEnvironmentSentiment) {
        nextSentiments.problems = homeEnvironmentSentiment;
      }

      const roleModelSentiment = analyzeFieldWithRules(
        roleReasonSource,
        ROLE_MODEL_RULES,
      );
      if (roleModelSentiment) {
        nextSentiments.reason = roleModelSentiment;
      }

      setSentiments(nextSentiments);
    }
  }, [surveyData, analyzeFieldWithRules]);

  if (!surveyData) return null;

  const getDisplayValue = (value: any) => {
    if (value === null || value === undefined) return 'Not provided';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'string' && value.trim() === '') return 'Not provided';
    return value;
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 mt-6 sm:mt-8 space-y-4">
      <h3 className="text-lg sm:text-xl font-semibold text-gray-900">Psychological Insights</h3>
      
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <h4 className="font-medium text-sm sm:text-base mb-2 text-gray-900">Child Background</h4>
            <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
              {getDisplayValue(surveyData["Background of the Child "])}
            </p>
            <p className="mt-2 text-xs sm:text-sm text-gray-500">
              Sentiment: {sentiments.background?.score ?? 'N/A'}
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-xl">
            <h4 className="font-medium text-sm sm:text-base mb-2 text-gray-900">Home Environment</h4>
            <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
              {getDisplayValue(surveyData["Problems in Home "])}
            </p>
            <p className="mt-2 text-xs sm:text-sm text-gray-500">
              Sentiment: {sentiments.problems?.score ?? 'N/A'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <h4 className="font-medium text-sm sm:text-base mb-2 text-gray-900">Behavioral Impact</h4>
            <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
              {getDisplayValue(surveyData["Behavioral Impact"])}
            </p>
            <p className="mt-2 text-xs sm:text-sm text-gray-500">
              Sentiment: {sentiments.behavior?.score ?? 'N/A'}
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-xl">
            <h4 className="font-medium text-sm sm:text-base mb-2 text-gray-900">Role Model Influence</h4>
            <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
              {getDisplayValue(surveyData["Reason for such role model "] ?? surveyData["Role models"])}
            </p>
            <p className="mt-2 text-xs sm:text-sm text-gray-500">
              Sentiment: {sentiments.reason?.score ?? 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PsychiatricInsights;