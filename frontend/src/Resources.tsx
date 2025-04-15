import React from 'react';

const ResourcesPage = () => {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <h2 className="text-2xl font-semibold text-purple-700 mb-4">Resources for Students</h2>
      <p className="text-gray-600 mb-4">
        Here are some helpful resources to guide you through your academic and career journey.
      </p>
      <ul className="list-disc ml-6 space-y-2 text-gray-700">
        <li>Psychometric Test Guidelines & Sample Papers</li>
        <li>Career Exploration Guides by Subject</li>
        <li>Scholarship & Financial Aid Programs for Underprivileged Students</li>
        <li>Recommended Online Learning Platforms (Coursera, Khan Academy, NPTEL)</li>
        <li>Time Management & Mental Wellness Resources</li>
        <li>Access to Real Stories from Inspiring Mentors</li>
      </ul>
    </div>
  );
};

export default ResourcesPage;
