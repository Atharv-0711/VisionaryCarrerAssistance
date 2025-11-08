import React from 'react';
import { Briefcase, GraduationCap, Star, Award } from 'lucide-react';

const mentors = [
  {
    name: "Dr. Rajesh Kumar",
    image: "https://xsgames.co/randomusers/assets/avatars/male/1.jpg",
    role: "Senior Software Engineer",
    company: "Tech Innovations India",
    experience: "15+ years",
    expertise: ["Career Guidance", "Technology", "Leadership"],
    education: "Ph.D. in Computer Science",
    achievements: "Led 50+ successful projects",
  },
  {
    name: "Dr. Priya Sharma",
    image: "https://xsgames.co/randomusers/assets/avatars/female/1.jpg",
    role: "Career Counselor",
    company: "Career Development Institute",
    experience: "12+ years",
    expertise: ["Student Counseling", "Career Planning", "Academic Guidance"],
    education: "Ph.D. in Psychology",
    achievements: "Guided 1000+ students successfully",
  },
  {
    name: "Amit Patel",
    image: "https://xsgames.co/randomusers/assets/avatars/male/2.jpg",
    role: "Business Consultant",
    company: "Global Consulting Group",
    experience: "10+ years",
    expertise: ["Business Strategy", "Entrepreneurship", "Mentoring"],
    education: "MBA from IIM",
    achievements: "Founded 2 successful startups",
  },
  {
    name: "Dr. Meera Reddy",
    image: "https://xsgames.co/randomusers/assets/avatars/female/2.jpg",
    role: "Education Specialist",
    company: "Learning Excellence Center",
    experience: "18+ years",
    expertise: ["Educational Psychology", "Student Development", "Career Mapping"],
    education: "Ph.D. in Education",
    achievements: "Published research in top journals",
  }
];

const MentorConnections: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Connect with Expert Mentors</h1>
        <p className="text-gray-600">
          Get guidance from experienced professionals who understand your journey and can help shape your career path.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {mentors.map((mentor, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="md:flex">
              <div className="md:flex-shrink-0">
                <img
                  className="h-48 w-full object-cover md:w-48"
                  src={mentor.image}
                  alt={mentor.name}
                />
              </div>
              <div className="p-8">
                <div className="flex items-center">
                  <h2 className="text-xl font-semibold text-gray-900">{mentor.name}</h2>
                  <Star className="h-5 w-5 text-yellow-400 ml-2" fill="currentColor" />
                </div>
                
                <div className="mt-2 flex items-center text-gray-600">
                  <Briefcase className="h-4 w-4 mr-2" />
                  <p>{mentor.role} at {mentor.company}</p>
                </div>
                
                <div className="mt-2 flex items-center text-gray-600">
                  <GraduationCap className="h-4 w-4 mr-2" />
                  <p>{mentor.education}</p>
                </div>

                <div className="mt-2 flex items-center text-gray-600">
                  <Award className="h-4 w-4 mr-2" />
                  <p>{mentor.experience} experience</p>
                </div>

                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-gray-900">Expertise:</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {mentor.expertise.map((skill, skillIndex) => (
                      <span
                        key={skillIndex}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4">
                  <p className="text-sm text-gray-600">
                    <strong>Key Achievement:</strong> {mentor.achievements}
                  </p>
                </div>

                <button className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                  Connect with Mentor
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MentorConnections; 