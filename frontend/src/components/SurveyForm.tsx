import React, { useEffect, useMemo, useState } from 'react';
import { Send } from 'lucide-react';
import { apiRequest } from '../utils/api';
import { useLocation, useNavigate } from 'react-router-dom';

interface FormData {
  "Name of Child ": string;
  "Age": string;
  "Class (बच्चे की कक्षा)": string;
  "Background of the Child ": string;
  "Problems in Home ": string;
  "Behavioral Impact": string;
  "Academic Performance ": string;
  "Family Income ": string;
  "Role models": string;
  "Reason for role model ": string;
  "Counselling Needed "?: string;
  [key: string]: string | undefined;
}

interface FormErrors {
  [key: string]: string;
}

// Define props interface to fix TypeScript error
interface SurveyFormProps {
  onSubmitSuccess?: () => void;
}

// Validation helper functions
const validateName = (name: string): boolean => {
  return /^[a-zA-Z\s]*$/.test(name);
};

const validateAge = (age: number): boolean => {
  return age >= 5 && age <= 18;
};

const validateClass = (classNum: number): boolean => {
  return classNum >= 1 && classNum <= 12;
};

const validateAcademicPerformance = (performance: number): boolean => {
  return performance >= 0 && performance <= 100;
};

const validateFamilyIncome = (income: number): boolean => {
  return income > 0;
};

interface SubmitSurveyResponse {
  success: boolean;
  message: string;
  analysis: any;
  assessmentId?: number;
}

const SurveyForm: React.FC<SurveyFormProps> = ({ onSubmitSuccess }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { studentId: initialStudentId, studentName: initialStudentName, studentAge: initialStudentAge, studentClass: initialStudentClass } =
    (location.state as { studentId?: number; studentName?: string; studentAge?: number; studentClass?: string } | null) ||
    {};
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const studentIdQuery = searchParams.get('studentId');
  const studentNameQuery = searchParams.get('studentName');
  const studentAgeQuery = searchParams.get('studentAge');
  const studentClassQuery = searchParams.get('studentClass');
  const resolvedStudentId = useMemo(() => {
    if (typeof initialStudentId === 'number') {
      return initialStudentId;
    }
    if (studentIdQuery) {
      const parsed = Number.parseInt(studentIdQuery, 10);
      return Number.isNaN(parsed) ? undefined : parsed;
    }
    return undefined;
  }, [initialStudentId, studentIdQuery]);
  const resolvedStudentName = initialStudentName ?? studentNameQuery ?? undefined;
  const resolvedStudentAge = useMemo(() => {
    if (typeof initialStudentAge === 'number') {
      return String(initialStudentAge);
    }
    if (studentAgeQuery) {
      return studentAgeQuery;
    }
    return undefined;
  }, [initialStudentAge, studentAgeQuery]);
  const resolvedStudentClass = useMemo(() => {
    if (typeof initialStudentClass === 'string' && initialStudentClass.trim() !== '') {
      return initialStudentClass;
    }
    if (studentClassQuery) {
      return studentClassQuery;
    }
    return undefined;
  }, [initialStudentClass, studentClassQuery]);

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    "Name of Child ": "",
    "Age": "",
    "Class (बच्चे की कक्षा)": "",
    "Background of the Child ": "",
    "Problems in Home ": "",
    "Behavioral Impact": "",
    "Academic Performance ": "",
    "Family Income ": "",
    "Role models": "",
    "Reason for role model ": "",
    "Counselling Needed ": "",
  });
  const [errors, setErrors] = useState<FormErrors>({});

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      "Name of Child ": resolvedStudentName ?? prev["Name of Child "],
      "Age": resolvedStudentAge ?? prev["Age"],
      "Class (बच्चे की कक्षा)": resolvedStudentClass ?? prev["Class (बच्चे की कक्षा)"],
    }));
  }, [resolvedStudentName, resolvedStudentAge, resolvedStudentClass]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation checks
    const newErrors: FormErrors = {};
    
    if (!formData["Name of Child "].trim()) {
      newErrors["Name of Child "] = "Name is required";
    } else if (!validateName(formData["Name of Child "])) {
      newErrors["Name of Child "] = "Please enter a valid name (letters and spaces only)";
    }
    
    const age = Number(formData["Age"]);
    if (isNaN(age) || !validateAge(age)) {
      newErrors["Age"] = "Age must be between 5 and 18";
    }
    
    const classNum = Number(formData["Class (बच्चे की कक्षा)"]);
    if (isNaN(classNum) || !validateClass(classNum)) {
      newErrors["Class (बच्चे की कक्षा)"] = "Class must be between 1 and 12";
    }
    
    const performance = Number(formData["Academic Performance "]);
    if (isNaN(performance) || !validateAcademicPerformance(performance)) {
      newErrors["Academic Performance "] = "Academic Performance must be between 0 and 100";
    }
    
    const income = Number(formData["Family Income "]);
    if (isNaN(income) || !validateFamilyIncome(income)) {
      newErrors["Family Income "] = "Family Income must be greater than 0";
    }
    
    // Check for required fields
    const requiredFields = [
      "Name of Child ",
      "Age",
      "Class (बच्चे की कक्षा)",
      "Background of the Child ",
      "Problems in Home ",
      "Behavioral Impact",
      "Academic Performance ",
      "Family Income ",
      "Role models",
      "Counselling Needed ",
    ];
    
    requiredFields.forEach(field => {
      if (!formData[field]?.trim()) {
        newErrors[field] = `${field.trim()} is required`;
      }
    });
    
    // If there are errors, display them and stop submission
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});

    setLoading(true);
    
    try {
      // Format data for backend
      const submissionData = {
        ...formData,
        "Age": parseFloat(formData["Age"]),
        "Class (बच्चे की कक्षा)": parseFloat(formData["Class (बच्चे की कक्षा)"]),
        "Academic Performance ": parseFloat(formData["Academic Performance "]),
        "Family Income ": parseFloat(formData["Family Income "])
      };

      // Submit to backend
      const submissionDataWithStudent = {
        ...submissionData,
        ...(resolvedStudentId ? { studentId: resolvedStudentId } : {}),
      };

      const response = await apiRequest<SubmitSurveyResponse>(
        '/api/submit-survey',
        {
          method: 'POST',
          body: JSON.stringify(submissionDataWithStudent),
        }
      );

      if (response.success) {
        const successNotice =
          response.message ||
          (response.assessmentId
            ? 'Survey submitted and assessment saved!'
            : 'Survey submitted successfully!');
        alert(successNotice);
        
        // Clear form
        setFormData({
          "Name of Child ": "",
          "Age": "",
          "Class (बच्चे की कक्षा)": "",
          "Background of the Child ": "",
          "Problems in Home ": "",
          "Behavioral Impact": "",
          "Academic Performance ": "",
          "Family Income ": "",
          "Role models": "",
          "Reason for role model ": "",
          "Counselling Needed ": ""
        });
        setErrors({});
        
        onSubmitSuccess?.();

        if (typeof window !== 'undefined' && (window as any).refreshDashboard) {
          (window as any).refreshDashboard();
        }

        if (resolvedStudentId) {
          navigate('/student-assessment', {
            state: { focusStudentId: resolvedStudentId },
            replace: true,
          });
        }
      } else {
        throw new Error('Failed to submit survey');
      }
    } catch (error: any) {
      console.error('Error submitting survey:', error);
      alert(error.message || 'Failed to submit survey. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setErrors((prev) => {
      if (!prev[name]) return prev;
      const updated = { ...prev };
      delete updated[name];
      return updated;
    });
  };

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm p-5 sm:p-8 mt-6 sm:mt-8">
      {resolvedStudentName && (
        <div className="mb-6 rounded-xl border border-purple-200 bg-purple-50 p-4 text-sm text-purple-800">
          Recording assessment for <span className="font-semibold">{resolvedStudentName}</span>.
          Results will be visible only to the associated school admin.
        </div>
      )}
      <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Career Guidance Survey</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Child Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name of Child *
            </label>
            <input
              id="name"
              type="text"
              name="Name of Child "
              value={formData["Name of Child "]}
              onChange={handleChange}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Name of Child "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
              aria-required="true"
              aria-invalid={Boolean(errors["Name of Child "])}
            />
            {errors["Name of Child "] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Name of Child "]}. Please enter letters and spaces only.
              </p>
            )}
          </div>
          <div>
            <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-1">
              Age *
            </label>
            <input
              id="age"
              type="number"
              name="Age"
              value={formData["Age"]}
              onChange={handleChange}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Age"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
              aria-required="true"
              aria-invalid={Boolean(errors["Age"])}
            />
            {errors["Age"] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Age"]}. Enter a number between 5 and 18.
              </p>
            )}
          </div>
        </div>

        <div>
          <label htmlFor="class" className="block text-sm font-medium text-gray-700 mb-1">
            Class (बच्चे की कक्षा) *
          </label>
          <input
            id="class"
            type="number"
            name="Class (बच्चे की कक्षा)"
            value={formData["Class (बच्चे की कक्षा)"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Class (बच्चे की कक्षा)"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Class (बच्चे की कक्षा)"])}
          />
          {errors["Class (बच्चे की कक्षा)"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Class (बच्चे की कक्षा)"]}. Use a number between 1 and 12.
            </p>
          )}
        </div>

        {/* Background and Environment */}
        <div>
          <label htmlFor="background" className="block text-sm font-medium text-gray-700 mb-1">
            Background of the Child (e.g., Middle Class, Labour, Private Job) *
          </label>
          <input
            id="background"
            type="text"
            name="Background of the Child "
            value={formData["Background of the Child "]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Background of the Child "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Background of the Child "] )}
          />
          {errors["Background of the Child "] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Background of the Child "]}. Describe briefly (e.g. "Middle class family").
            </p>
          )}
        </div>

        <div>
          <label htmlFor="problems" className="block text-sm font-medium text-gray-700 mb-1">
            Problems in Home (e.g., Financial, Family, Health) *
          </label>
          <input
            id="problems"
            type="text"
            name="Problems in Home "
            value={formData["Problems in Home "]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Problems in Home "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Problems in Home "] )}
          />
          {errors["Problems in Home "] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Problems in Home "]}. Mention any major challenges (financial, family, etc.).
            </p>
          )}
        </div>

        <div>
          <label htmlFor="behavior" className="block text-sm font-medium text-gray-700 mb-1">
            Behavioral Impact *
          </label>
          <textarea
            id="behavior"
            name="Behavioral Impact"
            value={formData["Behavioral Impact"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Behavioral Impact"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            rows={3}
            placeholder="Describe the child's behavior (e.g., Lack of Confidence, No effect, Aggressive)"
            aria-required="true"
            aria-invalid={Boolean(errors["Behavioral Impact"])}
          />
          {errors["Behavioral Impact"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Behavioral Impact"]}. Share how the situation affects the child.
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          <div>
            <label htmlFor="academic" className="block text-sm font-medium text-gray-700 mb-1">
              Academic Performance (Scale 1-10)
            </label>
            <input
              id="academic"
              type="number"
              name="Academic Performance "
              value={formData["Academic Performance "]}
              onChange={handleChange}
              min="1"
              max="10"
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Academic Performance "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            />
            {errors["Academic Performance "] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Academic Performance "]}. Enter a score between 1 and 10.
              </p>
            )}
          </div>
          <div>
            <label htmlFor="income" className="block text-sm font-medium text-gray-700 mb-1">
              Family Income (Monthly in Rupees)
            </label>
            <input
              id="income"
              type="number"
              name="Family Income "
              value={formData["Family Income "]}
              onChange={handleChange}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Family Income "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            />
            {errors["Family Income "] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Family Income "]}. Provide a positive monthly amount.
              </p>
            )}
          </div>
        </div>

        {/* Role Models */}
        <div>
          <label htmlFor="roleModels" className="block text-sm font-medium text-gray-700 mb-1">
            Role Models (e.g., Teacher, Doctor, Army, Guardian)
          </label>
          <input
            id="roleModels"
            type="text"
            name="Role models"
            value={formData["Role models"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Role models"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
          />
          {errors["Role models"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Role models"]}. Mention who inspires the student.
            </p>
          )}
        </div>

        {/* Counselling Needed */}
        <div>
          <label htmlFor="counsellingNeeded" className="block text-sm font-medium text-gray-700 mb-1">
            Counselling Needed *
          </label>
          <select
            id="counsellingNeeded"
            name="Counselling Needed "
            value={formData["Counselling Needed "] ?? ''}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Counselling Needed "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Counselling Needed "] )}
          >
            <option value="">Select an option</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
            <option value="Maybe">Maybe</option>
          </select>
          {errors["Counselling Needed "] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Counselling Needed "]}. Choose whether the student needs counselling support.
            </p>
          )}
        </div>

        {/* Reason for role model */}
        <div>
          <label htmlFor="Reason for role model" className="block text-sm font-medium text-gray-700 mb-1">
            Reason for role model *
          </label>
          <input
            id="reasonforrolemodel"
            type="text"
            name="Reason for role model "
            value={formData["Reason for role model "]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Reason for role model "] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            placeholder="e.g., Yes, No, Maybe"
            aria-required="true"
            aria-invalid={Boolean(errors["Reason for role model "] )}
          />
          {errors["Reason for role model "] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Reason for role model "]}. Say why this role model matters.
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2 min-h-[48px]"
        >
          {loading ? (
            <span>Processing...</span>
          ) : (
            <>
              <Send className="h-5 w-5" />
              <span>Submit Survey</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default SurveyForm;
