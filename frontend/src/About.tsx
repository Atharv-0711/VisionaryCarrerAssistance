const AboutPage = () => {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-8 space-y-4">
      <h2 className="text-xl sm:text-2xl font-semibold text-purple-700">About Visionary Career Assistance</h2>
      <p className="text-gray-700 text-sm sm:text-base leading-relaxed space-y-4">
        Many underprivileged students struggle due to a lack of a supportive home environment, proper mentorship,
        and career guidance, often leading them to lose direction in life.
        <br /><br />
        Our <strong>Visionary Career Assistance</strong> project aims to bridge this gap by leveraging
        <em> data-driven insights</em> to understand students’ psychology, identify their challenges, and guide
        them toward the right career path.
        <br /><br />
        The project begins by collecting detailed student information — backgrounds, interests, academic performance,
        and aspirations. With <strong>ML and NLP</strong> techniques, we analyze this data to detect psychological
        barriers and generate personalized roadmaps. Students are matched with mentors and counselors who guide them,
        while an AI-powered tracker monitors engagement and well-being through sentiment analysis.
        <br /><br />
        We also collaborate with <strong>NGOs, schools, and CSR initiatives</strong> to provide scholarships and
        skill-building resources. Our goal is to offer long-term mentorship that empowers students to overcome
        obstacles and achieve success.
      </p>
    </div>
  );
};

export default AboutPage;
