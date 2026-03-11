import React, { useEffect, useState, useMemo, useCallback } from 'react';
import Sentiment from 'sentiment';
import {
  formatInsightScore,
  formatInsightSource,
  INSIGHT_TITLES,
} from '../utils/insightPresentation';

interface SurveyData {
  [key: string]: any;
}

type GlobalAnalysisData = {
  rolemodel?: {
    sentimentScore?: number;
  };
};

type SentimentEntry = {
  score: number;
  source?: 'lexicon'| 'backend' | 'domain' | 'global' ;
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

const getSurveyValue = (surveyData: SurveyData, ...keys: string[]) => {
  for (const key of keys) {
    const value = surveyData?.[key];
    if (value !== null && value !== undefined) {
      return value;
    }
  }
  return null;
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
      /\bviolent attitude\b/,
      /\bbad attitude\b/,
      /\baggression\b/,
      /\baggressive\b/,
      /\bhome aggression\b/,
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
    keywords: [/\bgangster\b/, /\bcriminal\b/, /\bmafia\b/, /\bdon\b/, /\bgoon\b/, /\bthief\b/, /\bsteal(?:ing)?\b/],
    score: 1.2,
  },
  {
    keywords: [/\bgambling\b/, /\bgambler\b/, /\bbetting\b/, /\bcasino\b/, /\bbookie\b/],
    score: 1.6,
  },
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

const BEHAVIORAL_IMPACT_RULES: KeywordRule[] = [
  {
    keywords: [
      /\bnot interested in anything\b/,
      /\bnot interested\b/,
      /\bno interest\b/,
      /\blost interest\b/,
      /\buninterested\b/,
      /\bdisinterested\b/,
      /\bapathetic\b/,
    ],
    score: 1.4,
  },
];

const toBackendScore = (value: unknown): number | undefined => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return undefined;
  }
  return Number(numericValue.toFixed(2));
};

const getSentimentBadgeClass = (score?: number): string => {
  if (typeof score !== 'number') {
    return 'bg-gray-100 text-gray-600';
  }
  if (score >= 4) {
    return 'bg-green-100 text-green-700';
  }
  if (score >= 3) {
    return 'bg-blue-100 text-blue-700';
  }
  if (score >= 2) {
    return 'bg-amber-100 text-amber-700';
  }
  return 'bg-rose-100 text-rose-700';
};

const PsychiatricInsights: React.FC<{ surveyData?: SurveyData; analysisData?: GlobalAnalysisData | null }> = ({
  surveyData,
  analysisData,
}) => {
  const [sentiments, setSentiments] = useState<{
    background?: SentimentEntry;
    problems?: SentimentEntry;
    behavior?: SentimentEntry;
    reason?: SentimentEntry;
  }>({});
  const [insightsVisible, setInsightsVisible] = useState(false);

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

  const analyzeFieldWithLexicon = useCallback(
    (value: unknown): SentimentEntry | undefined => {
      if (value === null || value === undefined) {
        return undefined;
      }

      const text = String(value).trim();
      if (!text) {
        return undefined;
      }

      const genericResult = sentimentAnalyzer.analyze(text);
      if (typeof genericResult?.score !== 'number') {
        return undefined;
      }

      return {
        score: clampScore(3 + genericResult.score),
        source: 'lexicon',
      };
    },
    [sentimentAnalyzer],
  );

  const analyzeRoleModelField = useCallback(
    (value: unknown): SentimentEntry | undefined => {
      const ruleBasedSentiment = analyzeFieldWithRules(value, ROLE_MODEL_RULES);
      if (ruleBasedSentiment) {
        return {
          ...ruleBasedSentiment,
          source: 'domain',
        };
      }

      return analyzeFieldWithLexicon(value);
    },
    [analyzeFieldWithLexicon, analyzeFieldWithRules],
  );

  useEffect(() => {
    if (surveyData) {
      const backendAnalysis = (surveyData as any)?.analysis;
      const roleReasonSource = getSurveyValue(
        surveyData,
        'Reason for such role model ',
        'Reason for Such Role Model',
        'Role models',
        'Role Models',
      );

      // Backend-derived scores when available
      const bgScore =
        backendAnalysis?.background?.analysis?.background_details?.[0]?.score ??
        backendAnalysis?.background?.analysis?.average_score;
      const behaviorScore = backendAnalysis?.behavioral?.analysis?.average_score;
      const homeProblemsAnalysis =
        backendAnalysis?.homeProblems?.analysis ??
        backendAnalysis?.home_problems?.analysis ??
        null;
      const backendHomeScore = toBackendScore(homeProblemsAnalysis?.average_score);

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
          getSurveyValue(
            surveyData,
            'Background of the Child ',
            'Background of the Child',
          ),
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
          BEHAVIORAL_IMPACT_RULES,
        );
        if (fallbackBehavior) {
          nextSentiments.behavior = fallbackBehavior;
        }
      }

      if (backendHomeScore !== undefined) {
        nextSentiments.problems = {
          score: backendHomeScore,
          source: 'backend',
        };
      } else {
        const homeEnvironmentSentiment = analyzeFieldWithRules(
          getSurveyValue(surveyData, 'Problems in Home ', 'Problems in Home'),
          HOME_ENVIRONMENT_RULES,
        );
        if (homeEnvironmentSentiment) {
          nextSentiments.problems = homeEnvironmentSentiment;
        }
      }

      const roleModelSentiment = analyzeRoleModelField(roleReasonSource);
      if (roleModelSentiment) {
        nextSentiments.reason = roleModelSentiment;
      }

      setSentiments(nextSentiments);
    }
  }, [surveyData, analysisData, analyzeRoleModelField, analyzeFieldWithRules]);

  useEffect(() => {
    if (!surveyData) {
      setInsightsVisible(false);
      return;
    }
    setInsightsVisible(false);
    const timer = window.setTimeout(() => setInsightsVisible(true), 30);
    return () => window.clearTimeout(timer);
  }, [surveyData, sentiments]);

  if (!surveyData) return null;

  const getDisplayValue = (value: any) => {
    if (value === null || value === undefined) return 'Not provided';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'string' && value.trim() === '') return 'Not provided';
    return value;
  };

  const insights = [
    {
      key: 'role-model',
      title: INSIGHT_TITLES.roleModel,
      value: getDisplayValue(
        getSurveyValue(
          surveyData,
          'Reason for such role model ',
          'Reason for Such Role Model',
          'Role models',
          'Role Models',
        )
      ),
      sentiment: sentiments.reason,
    },
    {
      key: 'background',
      title: INSIGHT_TITLES.background,
      value: getDisplayValue(
        getSurveyValue(
          surveyData,
          'Background of the Child ',
          'Background of the Child',
        )
      ),
      sentiment: sentiments.background,
    },
    {
      key: 'behavior',
      title: INSIGHT_TITLES.behavioral,
      value: getDisplayValue(surveyData['Behavioral Impact']),
      sentiment: sentiments.behavior,
    },
    {
      key: 'home-problems',
      title: INSIGHT_TITLES.homeProblems,
      value: getDisplayValue(
        getSurveyValue(surveyData, 'Problems in Home ', 'Problems in Home')
      ),
      sentiment: sentiments.problems,
    },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 mt-6 sm:mt-8 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <h3 className="text-lg sm:text-xl font-semibold text-gray-900">Psychological Insights</h3>
        <p className="text-xs sm:text-sm text-gray-500">Adaptive insights for mobile and desktop</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
        {insights.map((insight, index) => (
          <div
            key={insight.key}
            className={`p-4 bg-gray-50 rounded-xl transition-all duration-300 hover:shadow-sm ${
              insightsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
            }`}
            style={{ transitionDelay: `${index * 55}ms` }}
          >
            <div className="flex items-center justify-between gap-2">
              <h4 className="font-medium text-sm sm:text-base text-gray-900">{insight.title}</h4>
              <span className={`inline-flex rounded-full px-2 py-1 text-[11px] sm:text-xs font-medium transition-all duration-300 ${getSentimentBadgeClass(insight.sentiment?.score)}`}>
                {formatInsightScore(insight.sentiment?.score)}
              </span>
            </div>
            <p className="mt-2 text-gray-600 text-sm sm:text-base leading-relaxed break-words">
              {insight.value}
            </p>
            <p className="mt-2 text-xs sm:text-sm text-gray-500">
              Sentiment source: {formatInsightSource(insight.sentiment?.source)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PsychiatricInsights;