import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DataDrivenPaths from '../DataDrivenPaths';

// Mock the fetch function
global.fetch = jest.fn();

describe('DataDrivenPaths Component', () => {
  const mockAnalysisData = {
    roleModel: {
      positiveImpact: 60,
      neutralImpact: 30,
      negativeImpact: 10,
      influentialCount: 5,
      totalTraits: 10,
      topTraits: {
        leadership: 8,
        communication: 7,
      },
    },
    background: {
      positive_count: 20,
      negative_count: 5,
      neutral_count: 15,
      average_score: 7.5,
      highly_positive: 10,
      positive: 10,
      neutral: 15,
      negative: 5,
      highly_negative: 0,
    },
    behavioral: {
      highly_positive_count: 15,
      positive_count: 20,
      neutral_count: 10,
      negative_count: 5,
      highly_negative_count: 0,
      average_score: 8.2,
      total_responses: 50,
    },
    income: {
      below_poverty_line: 5,
      low_income: 10,
      below_average: 15,
      average: 20,
      above_average: 10,
      averageIncome: 50000,
      total_households: 60,
      current_thresholds: {
        poverty_line: 20000,
        low_income: 30000,
        below_average: 40000,
        average: 50000,
      },
    },
  };

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<DataDrivenPaths />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders error state when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch'));
    
    render(<DataDrivenPaths />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load analysis data. Please try again later.')).toBeInTheDocument();
    });
  });

  it('renders data successfully when fetch succeeds', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalysisData),
    });

    render(<DataDrivenPaths />);

    await waitFor(() => {
      expect(screen.getByText('Data-Driven Career Insights')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive analysis of student backgrounds, behaviors, and aspirations to provide personalized career guidance.')).toBeInTheDocument();
    });
  });

  it('fetches data on component mount', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalysisData),
    });

    render(<DataDrivenPaths />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5000/api/analysis/complete');
    });
  });
}); 