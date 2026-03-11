export const INSIGHT_TITLES = {
  background: 'Background Analysis',
  behavioral: 'Behavioral Impact',
  roleModel: 'Role Model Analysis',
  homeProblems: 'Problems in Home Analysis',
  income: 'Income Distribution',
} as const;

export const formatInsightScore = (value: unknown, fallback = 'N/A'): string => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return fallback;
  }
  return numericValue.toFixed(2);
};

export const formatCount = (value: unknown, fallback = 'N/A'): string => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return fallback;
  }
  return numericValue.toLocaleString();
};

export const formatPercent = (value: unknown, digits = 1, fallback = 'N/A'): string => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return fallback;
  }
  return `${numericValue.toFixed(digits)}%`;
};

export const formatCorrelation = (value: unknown, fallback = 'N/A'): string => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return fallback;
  }
  return `${numericValue.toFixed(3)} (${numericValue >= 0 ? '+' : ''}${(numericValue * 100).toFixed(1)}%)`;
};

export const formatInsightSource = (source?: string): string => {
  switch (source) {
    case 'backend':
      return 'Backend';
    case 'domain':
      return 'Domain Rules';
    case 'lexicon':
      return 'Lexicon';
    case 'global':
      return 'Global Analysis';
    default:
      return 'Unavailable';
  }
};
