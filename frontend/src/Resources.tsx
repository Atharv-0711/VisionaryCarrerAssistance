const ResourcesPage = () => {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-8 space-y-4">
      <h2 className="text-xl sm:text-2xl font-semibold text-purple-700">Resources for Students</h2>
      <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
        Here are some helpful resources to guide you through your academic and career journey.
      </p>
      <ul className="list-disc pl-5 sm:pl-6 space-y-2 text-gray-700 text-sm sm:text-base leading-relaxed">
        <li>Psychometric Test Guidelines &amp; Sample Papers</li>
        <li>Career Exploration Guides by Subject</li>
        <li>Scholarship &amp; Financial Aid Programs for Underprivileged Students</li>
        <li>Recommended Online Learning Platforms (Coursera, Khan Academy, NPTEL)</li>
        <li>Time Management &amp; Mental Wellness Resources</li>
        <li>Access to Real Stories from Inspiring Mentors</li>
      </ul>
    </div>
  );
};

export default ResourcesPage;
