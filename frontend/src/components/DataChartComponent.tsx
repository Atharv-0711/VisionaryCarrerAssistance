import React from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const DataChartComponent = ({ data }) => {
  if (!data) return null;

  // Prepare data for behavioral sentiment chart
  const behavioralChartData = {
    labels: ['Positive', 'Neutral', 'Negative', 'Highly Positive', 'Highly Negative'],
    datasets: [
      {
        label: 'Behavioral Impact',
        data: [
          data.behavioral?.positive_count || 0,
          data.behavioral?.neutral_count || 0,
          data.behavioral?.negative_count || 0,
          data.behavioral?.highly_positive_count || 0,
          data.behavioral?.highly_negative_count || 0,
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
      },
    ],
  };

  // Prepare data for income distribution chart
  const incomeChartData = {
    labels: ['Below Poverty', 'Below Average', 'Average', 'Above Average', 'High Income'],
    datasets: [
      {
        label: 'Income Distribution',
        data: [
          data.income?.below_poverty_line || 0,
          data.income?.below_average || 0,
          data.income?.average || 0,
          data.income?.above_average || 0,
          data.income?.high_income || 0,
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(54, 162, 235, 0.6)',
        ],
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Behavioral Impact Distribution</h3>
        <Bar data={behavioralChartData} options={options} />
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Income Distribution</h3>
        <Bar data={incomeChartData} options={options} />
      </div>
    </div>
  );
};

export default DataChartComponent;