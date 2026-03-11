import React, { useMemo, useState } from 'react';
import { Briefcase, GraduationCap, Star, Award } from 'lucide-react';
import Sentiment from 'sentiment';

type Mentor = {
  name: string;
  image: string;
  role: string;
  company: string;
  experience: string;
  expertise: string[];
  education: string;
  achievements: string;
};

type MentorCategory = {
  category: string;
  description: string;
  mentors: Mentor[];
};

type MentorAnalysisData = {
  rolemodel?: {
    sentimentScore?: number;
    academicCorrelation?: number;
  };
  background?: {
    average_score?: number;
    academic_correlation?: number;
  };
  behavioral?: {
    average_score?: number;
    academic_correlation?: number;
  };
  home_problems?: {
    average_score?: number;
    academic_correlation?: number;
  };
};

type MentorConnectionsProps = {
  analysisData?: MentorAnalysisData | null;
  surveyData?: SurveyEntry[];
};

type SurveyEntry = {
  id?: string;
  _id?: string;
  timestamp?: string;
  createdAt?: string;
  sentimentScore?: number | string;
  studentName?: string;
  name?: string;
  "Name of Child "?: string;
  "Name of Child"?: string;
  "Reason for such role model "?: string;
  "Reason for such role model"?: string;
  "Background of the Child "?: string;
  "Background of the Child"?: string;
  "Behavioral Impact"?: string;
  "Behavioral Impact "?: string;
  "Problems in Home "?: string;
  "Problems in Home"?: string;
  analysis?: {
    roleModel?: { analysis?: { sentimentScore?: number } };
    rolemodel?: { analysis?: { sentimentScore?: number } };
    background?: { analysis?: { average_score?: number; academic_correlation?: number } };
    behavioral?: { analysis?: { average_score?: number; academic_correlation?: number } };
    homeProblems?: { analysis?: { average_score?: number; academic_correlation?: number } };
    home_problems?: { analysis?: { average_score?: number; academic_correlation?: number } };
  };
};

type RoleModelRule = {
  keywords: RegExp[];
  score: number;
};

const mentorCategories: MentorCategory[] = [
  {
    category: "Academic Mentor",
    description: "Supports subjects, grades, study strategy, research, and higher education planning.",
    mentors: [
  {
    name: "Dr. Rajesh Kumar",
    image: "https://xsgames.co/randomusers/assets/avatars/male/1.jpg",
        role: "Professor of Computer Science",
        company: "National Institute of Technology",
    experience: "15+ years",
        expertise: ["Study Planning", "Research Guidance", "Exam Strategy"],
    education: "Ph.D. in Computer Science",
        achievements: "Mentored 300+ students for M.Tech and Ph.D. admissions",
  },
  {
    name: "Dr. Priya Sharma",
    image: "https://xsgames.co/randomusers/assets/avatars/female/1.jpg",
        role: "Academic Advisor",
        company: "Scholars Development Center",
    experience: "12+ years",
        expertise: ["GPA Improvement", "Time Management", "Higher Studies"],
        education: "Ph.D. in Educational Psychology",
        achievements: "Helped students improve semester scores by an average of 18%",
      },
      {
        name: "Prof. Sandeep Verma",
        image: "https://xsgames.co/randomusers/assets/avatars/male/3.jpg",
        role: "Research Mentor",
        company: "Innovation Research Lab",
        experience: "11+ years",
        expertise: ["Research Writing", "Paper Publication", "Project Mentoring"],
        education: "Ph.D. in Electronics",
        achievements: "Guided 80+ student research papers",
  },
  {
    name: "Dr. Meera Reddy",
    image: "https://xsgames.co/randomusers/assets/avatars/female/2.jpg",
    role: "Education Specialist",
    company: "Learning Excellence Center",
    experience: "18+ years",
        expertise: ["Concept Clarity", "Academic Discipline", "Learning Systems"],
    education: "Ph.D. in Education",
        achievements: "Designed outcome-based study frameworks used by 20+ colleges",
      },
    ],
  },
  {
    category: "Career Mentor",
    description: "Guides internships, placements, resume building, and long-term career direction.",
    mentors: [
      {
        name: "Amit Patel",
        image: "https://xsgames.co/randomusers/assets/avatars/male/2.jpg",
        role: "Senior Career Consultant",
        company: "Career Growth Partners",
        experience: "10+ years",
        expertise: ["Placement Strategy", "Resume Building", "Interview Preparation"],
        education: "MBA from IIM",
        achievements: "Supported 1200+ successful campus placements",
      },
      {
        name: "Neha Bansal",
        image: "https://xsgames.co/randomusers/assets/avatars/female/4.jpg",
        role: "Talent Acquisition Lead",
        company: "Innotech Solutions",
        experience: "9+ years",
        expertise: ["ATS Resumes", "Job Role Mapping", "HR Interviews"],
        education: "MBA in Human Resources",
        achievements: "Conducted 3000+ fresher interviews",
      },
      {
        name: "Rohan Malhotra",
        image: "https://xsgames.co/randomusers/assets/avatars/male/5.jpg",
        role: "Industry Mentor",
        company: "FutureSkills Network",
        experience: "13+ years",
        expertise: ["Internship Guidance", "Industry Trends", "Career Roadmaps"],
        education: "B.Tech, PMP Certified",
        achievements: "Built structured career plans for 500+ students",
      },
      {
        name: "Kavya Iyer",
        image: "https://xsgames.co/randomusers/assets/avatars/female/5.jpg",
        role: "Placement Coach",
        company: "LaunchPad Careers",
        experience: "8+ years",
        expertise: ["Group Discussion", "Mock Interviews", "Offer Negotiation"],
        education: "M.A. in Organizational Psychology",
        achievements: "Achieved 92% placement success for mentored batches",
      },
    ],
  },
  {
    category: "Skill Mentor",
    description: "Focuses on practical skill-building like coding, speaking, writing, design, and exams.",
    mentors: [
      {
        name: "Arjun Nair",
        image: "https://xsgames.co/randomusers/assets/avatars/male/6.jpg",
        role: "Full Stack Skill Coach",
        company: "CodeSprint Academy",
        experience: "7+ years",
        expertise: ["DSA", "Web Development", "System Design Basics"],
        education: "B.Tech in Information Technology",
        achievements: "Trained 2000+ learners in coding fundamentals",
      },
      {
        name: "Simran Kaur",
        image: "https://xsgames.co/randomusers/assets/avatars/female/6.jpg",
        role: "Communication Trainer",
        company: "SpeakRight Institute",
        experience: "10+ years",
        expertise: ["Public Speaking", "Presentation", "Professional Writing"],
        education: "M.A. in English Literature",
        achievements: "Coached students for 150+ debate and speaking events",
      },
      {
        name: "Vivek Sinha",
        image: "https://xsgames.co/randomusers/assets/avatars/male/7.jpg",
        role: "Competitive Exam Mentor",
        company: "RankMasters",
        experience: "9+ years",
        expertise: ["Aptitude", "Reasoning", "Exam Planning"],
        education: "B.Sc. Mathematics",
        achievements: "Mentored top-500 results across national level exams",
      },
      {
        name: "Ananya Das",
        image: "https://xsgames.co/randomusers/assets/avatars/female/7.jpg",
        role: "Design & Creativity Mentor",
        company: "CreativeForge Studio",
        experience: "6+ years",
        expertise: ["UI Basics", "Visual Storytelling", "Portfolio Building"],
        education: "Bachelor of Design",
        achievements: "Helped students build 400+ design portfolios",
      },
    ],
  },
  {
    category: "Personal Development Mentor",
    description: "Develops confidence, discipline, emotional stability, and communication skills.",
    mentors: [
      {
        name: "Dr. Nisha Arora",
        image: "https://xsgames.co/randomusers/assets/avatars/female/8.jpg",
        role: "Mindset Coach",
        company: "InnerGrowth Studio",
        experience: "14+ years",
        expertise: ["Self-Confidence", "Mindset Reset", "Goal Setting"],
        education: "Ph.D. in Counseling Psychology",
        achievements: "Conducted 500+ personal growth workshops",
      },
      {
        name: "Rahul Menon",
        image: "https://xsgames.co/randomusers/assets/avatars/male/8.jpg",
        role: "Discipline and Productivity Coach",
        company: "PeakHabits Lab",
        experience: "11+ years",
        expertise: ["Habit Building", "Daily Routine", "Focus Training"],
        education: "M.Sc. in Behavioral Science",
        achievements: "Designed productivity systems used by 1000+ students",
      },
      {
        name: "Sneha Kulkarni",
        image: "https://xsgames.co/randomusers/assets/avatars/female/9.jpg",
        role: "Emotional Wellness Guide",
        company: "CalmMind Collective",
        experience: "9+ years",
        expertise: ["Stress Management", "Emotional Balance", "Resilience"],
        education: "M.Phil. in Clinical Psychology",
        achievements: "Supported 700+ students in stress-reduction programs",
      },
      {
        name: "Harsh Vardhan",
        image: "https://xsgames.co/randomusers/assets/avatars/male/9.jpg",
        role: "Communication Mentor",
        company: "LeadWithClarity",
        experience: "8+ years",
        expertise: ["Interpersonal Skills", "Conflict Resolution", "Confidence Speaking"],
        education: "MBA in Leadership Communication",
        achievements: "Improved communication outcomes for 300+ student leaders",
      },
    ],
  },
  {
    category: "Peer Mentor",
    description: "Senior students or classmates who help with adjustment, campus life, and practical advice.",
    mentors: [
      {
        name: "Aditya Singh",
        image: "https://xsgames.co/randomusers/assets/avatars/male/10.jpg",
        role: "Final Year CSE Student",
        company: "Campus Peer Network",
        experience: "3+ years",
        expertise: ["Campus Navigation", "Seniors Network", "Semester Planning"],
        education: "B.Tech in Computer Science (Pursuing)",
        achievements: "Onboarded 250+ first-year students smoothly",
      },
      {
        name: "Pooja Nair",
        image: "https://xsgames.co/randomusers/assets/avatars/female/10.jpg",
        role: "Peer Study Mentor",
        company: "Student Learning Circle",
        experience: "2+ years",
        expertise: ["Study Groups", "Assignment Planning", "Exam Week Strategy"],
        education: "B.Sc. Data Science (Pursuing)",
        achievements: "Managed peer learning sessions across 6 departments",
      },
      {
        name: "Karan Joshi",
        image: "https://xsgames.co/randomusers/assets/avatars/male/11.jpg",
        role: "Campus Life Mentor",
        company: "University Student Council",
        experience: "4+ years",
        expertise: ["Hostel Adjustment", "Clubs and Activities", "Time Balance"],
        education: "BBA (Pursuing)",
        achievements: "Helped freshmen participation grow by 40%",
      },
      {
        name: "Ishita Rao",
        image: "https://xsgames.co/randomusers/assets/avatars/female/11.jpg",
        role: "Peer Support Lead",
        company: "Buddy Mentorship Program",
        experience: "3+ years",
        expertise: ["Practical Advice", "Academic Adjustment", "Campus Resources"],
        education: "B.Com (Pursuing)",
        achievements: "Created peer mentor handbook adopted by her college",
      },
    ],
  },
  {
    category: "Entrepreneurship Mentor",
    description: "Helps students interested in startups, business models, product building, and fundraising basics.",
    mentors: [
      {
        name: "Manish Gupta",
        image: "https://xsgames.co/randomusers/assets/avatars/male/12.jpg",
        role: "Startup Advisor",
        company: "Founders Bridge",
        experience: "12+ years",
        expertise: ["Startup Validation", "MVP Planning", "Pitch Decks"],
        education: "MBA in Entrepreneurship",
        achievements: "Mentored 60+ student startup teams",
      },
      {
        name: "Ritika Sen",
        image: "https://xsgames.co/randomusers/assets/avatars/female/12.jpg",
        role: "Product Strategy Mentor",
        company: "BuildFirst Labs",
        experience: "9+ years",
        expertise: ["Product Thinking", "User Research", "Go-to-Market"],
        education: "B.Tech + PGDM",
        achievements: "Helped launch 25+ student-led MVP products",
      },
      {
        name: "Sahil Kapoor",
        image: "https://xsgames.co/randomusers/assets/avatars/male/13.jpg",
        role: "Business Model Coach",
        company: "Venture Ignition Hub",
        experience: "8+ years",
        expertise: ["Unit Economics", "Business Strategy", "Revenue Models"],
        education: "Chartered Financial Analyst (Level II)",
        achievements: "Coached teams that won 15+ startup competitions",
      },
      {
        name: "Diya Chakraborty",
        image: "https://xsgames.co/randomusers/assets/avatars/female/13.jpg",
        role: "Funding Readiness Mentor",
        company: "EarlyStage Catalyst",
        experience: "7+ years",
        expertise: ["Investor Pitching", "Fundraising Basics", "Founder Mindset"],
        education: "M.S. in Innovation Management",
        achievements: "Prepared 40+ student ventures for investor demo days",
      },
    ],
  },
  {
    category: "Wellness Mentor",
    description: "Supports healthy routines, stress control, and sustainable performance during student life.",
    mentors: [
      {
        name: "Dr. Aisha Khan",
        image: "https://xsgames.co/randomusers/assets/avatars/female/14.jpg",
        role: "Student Wellness Coach",
        company: "Balanced Minds Clinic",
        experience: "13+ years",
        expertise: ["Stress Care", "Sleep Hygiene", "Work-Life Balance"],
        education: "M.D. in Community Medicine",
        achievements: "Created wellness modules used in 10+ universities",
      },
      {
        name: "Nitin Arora",
        image: "https://xsgames.co/randomusers/assets/avatars/male/14.jpg",
        role: "Fitness and Routine Mentor",
        company: "Campus Fit Program",
        experience: "8+ years",
        expertise: ["Daily Fitness", "Energy Management", "Habit Tracking"],
        education: "B.P.Ed.",
        achievements: "Helped 900+ students adopt active daily routines",
      },
      {
        name: "Reema Thomas",
        image: "https://xsgames.co/randomusers/assets/avatars/female/15.jpg",
        role: "Mindfulness Trainer",
        company: "MindEase Collective",
        experience: "10+ years",
        expertise: ["Meditation Basics", "Focus Breathing", "Anxiety Reduction"],
        education: "M.A. in Psychology",
        achievements: "Delivered 300+ guided mindfulness sessions",
      },
      {
        name: "Yash Bhatia",
        image: "https://xsgames.co/randomusers/assets/avatars/male/15.jpg",
        role: "Nutrition and Wellness Mentor",
        company: "HealthyHabits Studio",
        experience: "6+ years",
        expertise: ["Student Nutrition", "Meal Planning", "Exam-Time Wellness"],
        education: "B.Sc. Nutrition and Dietetics",
        achievements: "Built affordable nutrition plans for hostel students",
      },
    ],
  },
];

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

const normalizeSentiment = (score: number): number => {
  if (!Number.isFinite(score)) return 0;
  // Backend scores are generally on 1-5; convert to -1..1.
  if (score >= -1 && score <= 1) return score;
  return clamp((score - 3) / 2, -1, 1);
};

const parseExperienceYears = (value: string): number => {
  const match = value.match(/\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
};

const getStringField = (row: SurveyEntry, keys: string[]): string => {
  const data = row as unknown as Record<string, unknown>;
  for (const key of keys) {
    const value = data[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return '';
};

const hasInformativeText = (value: string): boolean => {
  const cleaned = value.trim().toLowerCase();
  if (!cleaned) return false;
  return !['not provided', 'none', 'n/a', 'na', 'null', 'nil', 'unknown'].includes(cleaned);
};

const normalizeComparativeSentiment = (value: number): number => clamp(value / 2, -1, 1);

const ROLE_MODEL_RULES: RoleModelRule[] = [
  {
    keywords: [/\bgangster\b/, /\bcriminal\b/, /\bmafia\b/, /\bdon\b/, /\bgoon\b/, /\bthief\b/, /\bsteal(?:ing)?\b/],
    score: -0.9,
  },
  {
    keywords: [/\bgambling\b/, /\bgambler\b/, /\bbetting\b/, /\bcasino\b/, /\bbookie\b/],
    score: -0.7,
  },
  {
    keywords: [/\bteacher\b/, /\bprofessor\b/, /\beducator\b/, /\binstructor\b/, /\bmentor\b/],
    score: 1,
  },
  {
    keywords: [/\bdoctor\b/, /\bnurse\b/, /\bmedical\b/, /\bhealthcare\b/, /\bsurgeon\b/],
    score: 1,
  },
  {
    keywords: [/\bscientist\b/, /\bengineer\b/, /\bresearcher\b/, /\binnovator\b/, /\btechnologist\b/],
    score: 0.8,
  },
];

const cosineSimilarity = (a: number[], b: number[]): number => {
  if (a.length !== b.length || a.length === 0) return 0;
  const dot = a.reduce((sum, value, index) => sum + value * b[index], 0);
  const magA = Math.sqrt(a.reduce((sum, value) => sum + value * value, 0));
  const magB = Math.sqrt(b.reduce((sum, value) => sum + value * value, 0));
  if (magA === 0 || magB === 0) return 0;
  return dot / (magA * magB);
};

const CATEGORY_PROFILES: Record<string, number[]> = {
  "Academic Mentor": [0.2, 0.45, 0.1, 0.25],
  "Career Mentor": [0.5, 0.1, 0.25, 0.15],
  "Skill Mentor": [0.2, 0.1, 0.55, 0.15],
  "Personal Development Mentor": [0.1, 0.1, 0.45, 0.35],
  "Peer Mentor": [0.1, 0.35, 0.2, 0.35],
  "Entrepreneurship Mentor": [0.6, 0.15, 0.2, 0.05],
  "Wellness Mentor": [0.05, 0.1, 0.4, 0.45],
};

const MODULE_LABELS: Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', string> = {
  rolemodel: 'Role Model',
  background: 'Background',
  behavioral: 'Behavioral',
  home_problems: 'Home Environment',
};

const SIGNAL_SOURCE_LABELS: Record<'backend' | 'rule' | 'text' | 'missing', string> = {
  backend: 'Backend analysis',
  rule: 'Rule-based text analysis',
  text: 'Generic text sentiment',
  missing: 'Missing input',
};

const MentorConnections: React.FC<MentorConnectionsProps> = ({ analysisData, surveyData = [] }) => {
  const sentimentAnalyzer = useMemo(() => new Sentiment(), []);
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>('');

  const studentOptions = useMemo(() => {
    return surveyData.map((entry, index) => {
      const name = getStringField(entry, ['Name of Child ', 'Name of Child', 'studentName', 'name']) || `Student ${index + 1}`;
      const id =
        getStringField(entry, ['id', '_id']) ||
        `${name}-${getStringField(entry, ['timestamp', 'createdAt']) || index}`;
      const timestamp = getStringField(entry, ['timestamp', 'createdAt']);
      return { id, name, timestamp, entry };
    });
  }, [surveyData]);

  const selectedSurvey = useMemo(() => {
    if (studentOptions.length === 0) return null;
    if (!selectedSurveyId) return studentOptions[studentOptions.length - 1];
    return studentOptions.find((option) => option.id === selectedSurveyId) ?? studentOptions[studentOptions.length - 1];
  }, [studentOptions, selectedSurveyId]);

  const individualSentiments = useMemo(() => {
    const entry = selectedSurvey?.entry;
    if (!entry) {
      return {
        rolemodel: { value: 0, available: false, confidence: 0, source: 'missing' as const },
        background: { value: 0, available: false, confidence: 0, source: 'missing' as const },
        behavioral: { value: 0, available: false, confidence: 0, source: 'missing' as const },
        home_problems: { value: 0, available: false, confidence: 0, source: 'missing' as const },
      };
    }

    const roleModelText = getStringField(entry, [
      'Reason for such role model ',
      'Reason for such role model',
      'Reason for Such Role Model',
      'Role models',
      'Role Models',
    ]);
    const backgroundText = getStringField(entry, ['Background of the Child ', 'Background of the Child']);
    const behavioralText = getStringField(entry, ['Behavioral Impact', 'Behavioral Impact ']);
    const homeProblemsText = getStringField(entry, ['Problems in Home ', 'Problems in Home']);
    const backendAnalysis = entry.analysis;
    const roleModelScore = Number(
      backendAnalysis?.roleModel?.analysis?.sentimentScore ??
      backendAnalysis?.rolemodel?.analysis?.sentimentScore ??
      NaN
    );
    const backgroundScore = Number(
      backendAnalysis?.background?.analysis?.average_score ??
      NaN
    );
    const behavioralScore = Number(
      backendAnalysis?.behavioral?.analysis?.average_score ??
      NaN
    );
    const homeProblemsScore = Number(
      backendAnalysis?.homeProblems?.analysis?.average_score ??
      backendAnalysis?.home_problems?.analysis?.average_score ??
      NaN
    );
    const scoreForText = (text: string) =>
      hasInformativeText(text) ? normalizeComparativeSentiment(sentimentAnalyzer.analyze(text).comparative) : 0;
    const getRoleModelRuleScore = (text: string): number | null => {
      if (!hasInformativeText(text)) {
        return null;
      }

      const normalizedText = text.trim().toLowerCase();
      const matchedRuleScores = ROLE_MODEL_RULES
        .filter((rule) => rule.keywords.some((keyword) => keyword.test(normalizedText)))
        .map((rule) => rule.score);

      if (matchedRuleScores.length === 0) {
        return null;
      }

      const averageRuleScore =
        matchedRuleScores.reduce((sum, score) => sum + score, 0) / matchedRuleScores.length;
      return clamp(averageRuleScore, -1, 1);
    };
    const buildSignal = (backendScore: number, text: string) => {
      if (Number.isFinite(backendScore)) {
        return { value: normalizeSentiment(backendScore), available: true, confidence: 1, source: 'backend' as const };
      }
      if (hasInformativeText(text)) {
        return { value: scoreForText(text), available: true, confidence: 0.7, source: 'text' as const };
      }
      return { value: 0, available: false, confidence: 0, source: 'missing' as const };
    };
    const buildRoleModelSignal = (backendScore: number, text: string) => {
      const ruleScore = getRoleModelRuleScore(text);
      if (ruleScore !== null) {
        return {
          value: ruleScore,
          available: true,
          confidence: 0.95,
          source: 'rule' as const,
        };
      }
      if (Number.isFinite(backendScore)) {
        return { value: normalizeSentiment(backendScore), available: true, confidence: 1, source: 'backend' as const };
      }
      if (hasInformativeText(text)) {
        return {
          value: scoreForText(text),
          available: true,
          confidence: 0.7,
          source: 'text' as const,
        };
      }
      return { value: 0, available: false, confidence: 0, source: 'missing' as const };
    };

    return {
      rolemodel: buildRoleModelSignal(roleModelScore, roleModelText),
      background: buildSignal(backgroundScore, backgroundText),
      behavioral: buildSignal(behavioralScore, behavioralText),
      home_problems: buildSignal(homeProblemsScore, homeProblemsText),
    };
  }, [selectedSurvey, sentimentAnalyzer]);

  const moduleContributions = useMemo(() => {
    const entryAnalysis = selectedSurvey?.entry?.analysis;
    const rawModules = [
      {
        key: 'rolemodel',
        label: 'Role Model',
        sentiment: individualSentiments.rolemodel.value,
        available: individualSentiments.rolemodel.available,
        confidence: individualSentiments.rolemodel.confidence,
        source: individualSentiments.rolemodel.source,
        correlation:
          entryAnalysis?.roleModel?.analysis?.sentimentScore !== undefined
            ? analysisData?.rolemodel?.academicCorrelation
            : analysisData?.rolemodel?.academicCorrelation,
      },
      {
        key: 'background',
        label: 'Background',
        sentiment: individualSentiments.background.value,
        available: individualSentiments.background.available,
        confidence: individualSentiments.background.confidence,
        source: individualSentiments.background.source,
        correlation:
          entryAnalysis?.background?.analysis?.academic_correlation ??
          analysisData?.background?.academic_correlation,
      },
      {
        key: 'behavioral',
        label: 'Behavioral',
        sentiment: individualSentiments.behavioral.value,
        available: individualSentiments.behavioral.available,
        confidence: individualSentiments.behavioral.confidence,
        source: individualSentiments.behavioral.source,
        correlation:
          entryAnalysis?.behavioral?.analysis?.academic_correlation ??
          analysisData?.behavioral?.academic_correlation,
      },
      {
        key: 'home_problems',
        label: 'Home Problems',
        sentiment: individualSentiments.home_problems.value,
        available: individualSentiments.home_problems.available,
        confidence: individualSentiments.home_problems.confidence,
        source: individualSentiments.home_problems.source,
        correlation:
          entryAnalysis?.homeProblems?.analysis?.academic_correlation ??
          entryAnalysis?.home_problems?.analysis?.academic_correlation ??
          analysisData?.home_problems?.academic_correlation,
      },
    ] as const;

    return rawModules.map((module) => {
      const normalizedSentiment = normalizeSentiment(module.sentiment);
      const correlation = Number.isFinite(module.correlation as number)
        ? clamp(Number(module.correlation), -1, 1)
        : NaN;
      const correlationWeight = Number.isFinite(correlation) ? clamp(Math.abs(correlation), 0.35, 1) : 0.6;
      const reliabilityWeight = module.available ? module.confidence * correlationWeight : 0;
      return {
        ...module,
        normalizedSentiment,
        weighted: normalizedSentiment * reliabilityWeight,
        reliabilityWeight,
      };
    });
  }, [analysisData, individualSentiments, selectedSurvey]);

  const overallWeightedSentiment = useMemo(() => {
    if (moduleContributions.length === 0) return 0;
    const total = moduleContributions.reduce((acc, module) => acc + module.weighted, 0);
    return total / moduleContributions.length;
  }, [moduleContributions]);

  const overallWeightedSentimentScore = useMemo(() => {
    // Convert internal -1..1 weighted value to 1..5 display scale.
    return clamp(((overallWeightedSentiment + 1) / 2) * 4 + 1, 1, 5);
  }, [overallWeightedSentiment]);

  const categoryScores = useMemo(() => {
    const weightedByKey = Object.fromEntries(
      moduleContributions.map((module) => [module.key, module.weighted])
    ) as Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', number>;

    const needVector = [
      Math.max(0, -weightedByKey.rolemodel),
      Math.max(0, -weightedByKey.background),
      Math.max(0, -weightedByKey.behavioral),
      Math.max(0, -weightedByKey.home_problems),
    ];
    const growthVector = [
      Math.max(0, weightedByKey.rolemodel),
      Math.max(0, weightedByKey.background),
      Math.max(0, weightedByKey.behavioral),
      Math.max(0, weightedByKey.home_problems),
    ];

    const hasNeed = needVector.some((value) => value > 0);
    const studentVector = hasNeed ? needVector : growthVector;

    const scores = Object.fromEntries(
      Object.entries(CATEGORY_PROFILES).map(([category, profile]) => {
        const similarity = cosineSimilarity(studentVector, profile);
        return [category, similarity];
      })
    ) as Record<string, number>;

    const allZero = Object.values(scores).every((score) => score === 0);
    if (allZero) scores["Career Mentor"] = 0.01;

    return scores;
  }, [moduleContributions]);

  const bestCategory = useMemo(() => {
    const ranked = Object.entries(categoryScores).sort((a, b) => b[1] - a[1]);
    return ranked[0]?.[0] ?? "Career Mentor";
  }, [categoryScores]);

  const bestCategoryData = useMemo(
    () => mentorCategories.find((group) => group.category === bestCategory) ?? mentorCategories[0],
    [bestCategory]
  );

  const bestMentor = useMemo(() => {
    return bestCategoryData.mentors.reduce((best, current) => {
      return parseExperienceYears(current.experience) > parseExperienceYears(best.experience) ? current : best;
    }, bestCategoryData.mentors[0]);
  }, [bestCategoryData]);

  const overallTone =
    overallWeightedSentimentScore <= 2.5
      ? "Support Needed"
      : overallWeightedSentimentScore >= 3.5
      ? "Growth Ready"
      : "Balanced";

  const studentReport = useMemo(() => {
    const modules = moduleContributions.map((module) => {
      const scoreOnFive = clamp(((module.normalizedSentiment + 1) / 2) * 4 + 1, 1, 5);
      const key = module.key as 'rolemodel' | 'background' | 'behavioral' | 'home_problems';
      return {
        key,
        label: MODULE_LABELS[key],
        scoreOnFive,
        weighted: module.weighted,
        available: module.available,
        source: module.source,
        confidence: module.confidence,
      };
    });
    const availableModules = modules.filter((module) => module.available);

    const scoreBand = (score: number) => {
      if (score >= 4.2) return "High Strength";
      if (score >= 3.35) return "Moderate Strength";
      if (score >= 2.75) return "Watch Zone";
      if (score >= 2.0) return "Support Required";
      return "Critical Support";
    };

    const observationByModule: Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', string> = {
      rolemodel: "Track motivation consistency, role-model quality, and clarity of aspiration.",
      background: "Track financial/household pressure, education support, and study environment stability.",
      behavioral: "Track attendance, discipline, focus time, and assignment completion consistency.",
      home_problems: "Track home conflict frequency, emotional safety, and impact on concentration.",
    };

    const reasonByModule: Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', string> = {
      rolemodel: "Strong aspiration quality improves persistence and long-term academic direction.",
      background: "Background stress directly affects bandwidth for learning and attendance.",
      behavioral: "Behavioral consistency is the fastest lever for short-term academic improvement.",
      home_problems: "Home instability can reduce performance even when capability is high.",
    };

    const strengths = availableModules
      .filter((module) => module.scoreOnFive >= 3.35)
      .sort((a, b) => b.scoreOnFive - a.scoreOnFive)
      .slice(0, 3)
      .map(
        (module) =>
          `${module.label}: ${module.scoreOnFive.toFixed(2)}/5 (${scoreBand(module.scoreOnFive)}). Source used: ${SIGNAL_SOURCE_LABELS[module.source]}. Why this is a strength: ${reasonByModule[module.key]}. What this usually means: ${observationByModule[module.key]}`
      );

    const concernRiskByModule: Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', string> = {
      rolemodel: "aspiration drift or weak inspiration quality may reduce long-term consistency",
      background: "economic/environment stress may limit study bandwidth and regularity",
      behavioral: "irregular routines can quickly translate into lower academic outcomes",
      home_problems: "home instability can affect concentration, emotional safety, and retention",
    };

    const actionPlanByModule: Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', string> = {
      rolemodel: "Define a realistic role-model path, set monthly milestones, and review motivation triggers weekly.",
      background: "Provide structured study support, reduce environmental friction, and add practical resource planning.",
      behavioral: "Implement a daily routine with attendance/focus tracking and short accountability check-ins.",
      home_problems: "Start emotional-support and conflict-mitigation interventions with regular well-being check-ins.",
    };

    const supportPriority = (score: number) => {
      if (score <= 2.0) return "High Priority";
      if (score <= 2.75) return "Priority";
      if (score <= 3.35) return "Preventive Watch";
      return "Monitor";
    };

    const sortedByRisk = availableModules.slice().sort((a, b) => a.scoreOnFive - b.scoreOnFive);
    const criticalConcerns = sortedByRisk.filter((module) => module.scoreOnFive <= 2.75).slice(0, 3);
    const watchConcerns = sortedByRisk.filter((module) => module.scoreOnFive > 2.75 && module.scoreOnFive < 3.35).slice(0, 3);
    const concernTargets = criticalConcerns.length > 0 ? criticalConcerns : watchConcerns;

    const concerns = concernTargets.map((module) => {
      const gapToStable = Math.max(0, 3.35 - module.scoreOnFive);
      return `${module.label}: ${module.scoreOnFive.toFixed(2)}/5 (${scoreBand(module.scoreOnFive)} | ${supportPriority(module.scoreOnFive)}). Source used: ${SIGNAL_SOURCE_LABELS[module.source]}. Why this needs attention: ${concernRiskByModule[module.key]}. What to monitor now: ${observationByModule[module.key]}. Improvement needed to reach the stable band: ${gapToStable.toFixed(2)} points. Suggested next step: ${actionPlanByModule[module.key]}`;
    });

    const strengthsFallback =
      strengths.length > 0
        ? strengths
        : [
            `${availableModules.slice().sort((a, b) => b.scoreOnFive - a.scoreOnFive)[0]?.label ?? 'Overall profile'} is currently the strongest observed area. Source used: ${SIGNAL_SOURCE_LABELS[availableModules.slice().sort((a, b) => b.scoreOnFive - a.scoreOnFive)[0]?.source ?? 'missing']}. Keep this area steady for the next 4-6 weeks, because strengths usually help the student improve weaker dimensions as well.`,
          ];
    const concernsFallback =
      concerns.length > 0
        ? concerns
        : [
            availableModules.length > 0
              ? `${availableModules.slice().sort((a, b) => a.scoreOnFive - b.scoreOnFive)[0]?.label ?? 'Overall profile'} is currently the weakest area, so it should be treated as an early support priority. Source used: ${SIGNAL_SOURCE_LABELS[availableModules.slice().sort((a, b) => a.scoreOnFive - b.scoreOnFive)[0]?.source ?? 'missing']}. Watch this area closely over the next 2-4 weeks and intervene early if the trend drops further.`
              : 'There is not enough input data to score risks clearly. Add missing Background, Behavioral, and Home Environment details to make mentor matching and support advice more reliable.',
          ];

    const sourceSummary = modules.map((module) => {
      const sourceLabel = SIGNAL_SOURCE_LABELS[module.source];
      const confidencePercent = Math.round(module.confidence * 100);
      return `${module.label}: ${sourceLabel}${module.available ? ` (confidence ${confidencePercent}%)` : ''}`;
    });

    const weightedByKey = Object.fromEntries(
      moduleContributions.map((module) => [module.key, module.weighted])
    ) as Record<'rolemodel' | 'background' | 'behavioral' | 'home_problems', number>;

    const needVector = [
      Math.max(0, -weightedByKey.rolemodel),
      Math.max(0, -weightedByKey.background),
      Math.max(0, -weightedByKey.behavioral),
      Math.max(0, -weightedByKey.home_problems),
    ];
    const growthVector = [
      Math.max(0, weightedByKey.rolemodel),
      Math.max(0, weightedByKey.background),
      Math.max(0, weightedByKey.behavioral),
      Math.max(0, weightedByKey.home_problems),
    ];
    const hasNeed = needVector.some((value) => value > 0);
    const studentVector = hasNeed ? needVector : growthVector;
    const bestProfile = CATEGORY_PROFILES[bestCategory] ?? [0, 0, 0, 0];

    const dimensions: Array<'rolemodel' | 'background' | 'behavioral' | 'home_problems'> = [
      'rolemodel',
      'background',
      'behavioral',
      'home_problems',
    ];
    const alignment = dimensions
      .map((dimension, index) => ({
        label: MODULE_LABELS[dimension],
        signal: studentVector[index] * bestProfile[index],
      }))
      .sort((a, b) => b.signal - a.signal)
      .slice(0, 2)
      .filter((item) => item.signal > 0);

    const readingGuide = [
      "Start with the Overall Weighted Score (1-5). This gives a quick summary of the student's current position across all four dimensions.",
      "Next, read the dimension scores. Scores above 3.35 usually show usable strengths, while scores at or below 2.75 usually need focused support.",
      "Finally, read Why This Mentor. It explains why this mentor category fits the student's strongest needs instead of showing a random recommendation.",
    ];

    const whyMentor = [
      `Best-fit mentor category: ${bestCategory} (match score ${((categoryScores[bestCategory] ?? 0) * 100).toFixed(1)}%).`,
      alignment.length > 0
        ? `This category matches best because the strongest student signals right now are ${alignment.map((item) => `${item.label} (${item.signal.toFixed(2)})`).join(' and ')}.`
        : 'This category was selected as the closest available fit from the current student profile.',
      `Recommended mentor: ${bestMentor.name}, ${bestMentor.role}, with ${bestMentor.experience} of experience. This mentor was chosen as the strongest profile match within the selected category.`,
      "In the next review, check whether the lowest-scoring dimensions move closer to 3.0 or higher. That is the clearest sign that the mentor match is helping.",
    ];

    return {
      readingGuide,
      sourceSummary,
      strengths: strengthsFallback,
      concerns: concernsFallback,
      whyMentor,
    };
  }, [moduleContributions, bestCategory, categoryScores, bestMentor]);

  return (
    <div className="container mx-auto px-4 py-6 sm:py-8 space-y-6 sm:space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3 sm:mb-4">Connect with Expert Mentors</h1>
        <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
          Get guidance from experienced professionals who understand your journey and can help shape your career path.
        </p>
      </div>

      <section className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 space-y-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900">AI Mentor Matching</h2>
        <p className="text-sm sm:text-base text-gray-600">
          Student-specific matching uses cosine similarity between student sentiment-need vector and mentor-category profiles.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="student-selector" className="block text-sm font-medium text-gray-700 mb-1">
              Select Student
            </label>
            <select
              id="student-selector"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={selectedSurveyId}
              onChange={(event) => setSelectedSurveyId(event.target.value)}
              disabled={studentOptions.length === 0}
            >
              {studentOptions.length === 0 ? (
                <option value="">No student surveys available</option>
              ) : (
                studentOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}{option.timestamp ? ` - ${new Date(option.timestamp).toLocaleDateString()}` : ''}
                  </option>
                ))
              )}
            </select>
          </div>
          <div className="rounded-xl bg-gray-50 border border-gray-200 p-3">
            <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold">Current Student</p>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {selectedSurvey?.name ?? 'Not selected'}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl bg-purple-50 border border-purple-100 p-4">
            <p className="text-xs uppercase tracking-wide text-purple-600 font-semibold">Overall Weighted Sentiment</p>
            <p className="text-2xl font-bold text-purple-700 mt-1">{overallWeightedSentimentScore.toFixed(2)} / 5</p>
            <p className="text-sm text-gray-600 mt-1">Status: {overallTone}</p>
          </div>
          <div className="rounded-xl bg-blue-50 border border-blue-100 p-4">
            <p className="text-xs uppercase tracking-wide text-blue-600 font-semibold">Best Category Match</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{bestCategory}</p>
          </div>
          <div className="rounded-xl bg-green-50 border border-green-100 p-4">
            <p className="text-xs uppercase tracking-wide text-green-700 font-semibold">Best Mentor Match</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{bestMentor.name}</p>
            <p className="text-sm text-gray-600">{bestMentor.role}</p>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 sm:p-5 space-y-4">
          <h3 className="text-sm sm:text-base font-semibold text-gray-900">Student Sentiment Report</h3>
          <div className="rounded-lg bg-white border border-purple-100 p-3">
            <p className="text-xs uppercase tracking-wide text-purple-700 font-semibold">How to Read This Report</p>
            <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc list-inside">
              {studentReport.readingGuide.map((item, index) => (
                <li key={`guide-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg bg-white border border-slate-200 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-700 font-semibold">Scoring Sources</p>
            <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc list-inside">
              {studentReport.sourceSummary.map((item, index) => (
                <li key={`source-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg bg-white border border-green-100 p-3">
              <p className="text-xs uppercase tracking-wide text-green-700 font-semibold">Pros</p>
              <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc list-inside">
                {studentReport.strengths.map((item, index) => (
                  <li key={`pro-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg bg-white border border-amber-100 p-3">
              <p className="text-xs uppercase tracking-wide text-amber-700 font-semibold">Cons / Support Areas</p>
              <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc list-inside">
                {studentReport.concerns.map((item, index) => (
                  <li key={`con-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg bg-white border border-blue-100 p-3">
              <p className="text-xs uppercase tracking-wide text-blue-700 font-semibold">Why This Mentor</p>
              <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc list-inside">
                {studentReport.whyMentor.map((item, index) => (
                  <li key={`why-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <div className="space-y-8">
        {mentorCategories.map((group, groupIndex) => (
          <section key={group.category}>
            <div className="mb-4">
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900">
                {groupIndex + 1}. {group.category}
                {group.category === bestCategoryData.category ? (
                  <span className="ml-2 align-middle inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    Recommended
                  </span>
                ) : null}
              </h2>
              <p className="text-sm sm:text-base text-gray-600 mt-1">{group.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
              {group.mentors.map((mentor, index) => (
                <div
                  key={`${group.category}-${index}`}
                  className={`bg-white rounded-2xl shadow-sm overflow-hidden border ${
                    group.category === bestCategoryData.category && mentor.name === bestMentor.name
                      ? 'border-green-300 ring-1 ring-green-200'
                      : 'border-gray-100'
                  }`}
                >
            <div className="md:flex">
              <div className="md:flex-shrink-0">
                <img
                  className="h-48 w-full object-cover md:w-48"
                  src={mentor.image}
                  alt={mentor.name}
                />
              </div>
              <div className="p-5 sm:p-8 space-y-3">
                <div className="flex items-center">
                        <h3 className="text-lg sm:text-xl font-semibold text-gray-900">{mentor.name}</h3>
                  <Star className="h-5 w-5 text-yellow-400 ml-2" fill="currentColor" />
                        {group.category === bestCategoryData.category && mentor.name === bestMentor.name ? (
                          <span className="ml-2 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                            Best Match
                          </span>
                        ) : null}
                </div>
                
                <div className="flex items-center text-gray-600 text-sm sm:text-base">
                  <Briefcase className="h-4 w-4 mr-2 shrink-0" />
                  <p className="leading-relaxed">{mentor.role} at {mentor.company}</p>
                </div>
                
                <div className="flex items-center text-gray-600 text-sm sm:text-base">
                  <GraduationCap className="h-4 w-4 mr-2 shrink-0" />
                  <p className="leading-relaxed">{mentor.education}</p>
                </div>

                <div className="flex items-center text-gray-600 text-sm sm:text-base">
                  <Award className="h-4 w-4 mr-2 shrink-0" />
                  <p>{mentor.experience} experience</p>
                </div>

                <div className="mt-4">
                        <h4 className="text-sm font-semibold text-gray-900">Expertise:</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {mentor.expertise.map((skill, skillIndex) => (
                      <span
                        key={skillIndex}
                        className="inline-flex items-center px-3 py-1 rounded-full text-xs sm:text-sm font-medium bg-purple-100 text-purple-800"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4">
                  <p className="text-sm text-gray-600 leading-relaxed">
                    <strong>Key Achievement:</strong> {mentor.achievements}
                  </p>
                </div>

                <button className="mt-4 inline-flex items-center justify-center px-4 py-2 min-h-[44px] border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                  Connect with Mentor
                </button>
              </div>
            </div>
          </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};

export default MentorConnections; 