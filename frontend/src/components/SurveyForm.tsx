import React, { useEffect, useMemo, useState } from 'react';
import { Send } from 'lucide-react';
import { apiRequest } from '../utils/api';
import { useLocation, useNavigate } from 'react-router-dom';

interface FormData {
  "Timestamp": string;
  "Name of Child": string;
  "Age": string;
  "Date of Birth": string;
  "Class (बच्चे की कक्षा)": string;
  "Background of the Child": string;
  "Problems in Home": string;
  "Behavioral Impact": string;
  "Academic Performance": string;
  "Family Income": string;
  "Role Models": string;
  "Reason for Such Role Model": string;
  [key: string]: string;
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

const formatDateTimeLocalValue = (isoValue: string): string => {
  if (!isoValue) return '';

  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  const pad = (value: number) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
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
  const {
    studentId: initialStudentId,
    studentName: initialStudentName,
    studentAge: initialStudentAge,
    studentDob: initialStudentDob,
    studentClass: initialStudentClass,
  } =
    (location.state as {
      studentId?: number;
      studentName?: string;
      studentAge?: number;
      studentDob?: string;
      studentClass?: string;
    } | null) ||
    {};
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const studentIdQuery = searchParams.get('studentId');
  const studentNameQuery = searchParams.get('studentName');
  const studentAgeQuery = searchParams.get('studentAge');
  const studentDobQuery = searchParams.get('studentDob');
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
  const resolvedStudentDob = useMemo(() => {
    if (typeof initialStudentDob === 'string' && initialStudentDob.trim() !== '') {
      return initialStudentDob;
    }
    if (studentDobQuery) {
      return studentDobQuery;
    }
    return undefined;
  }, [initialStudentDob, studentDobQuery]);
  const isStudentNameFixed = Boolean(resolvedStudentId && resolvedStudentName);
  const isStudentDobFixed = Boolean(resolvedStudentId && resolvedStudentDob);

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    "Timestamp": new Date().toISOString(),
    "Name of Child": "",
    "Age": "",
    "Date of Birth": "",
    "Class (बच्चे की कक्षा)": "",
    "Background of the Child": "",
    "Problems in Home": "",
    "Behavioral Impact": "",
    "Academic Performance": "",
    "Family Income": "",
    "Role Models": "",
    "Reason for Such Role Model": "",
  });
  const [errors, setErrors] = useState<FormErrors>({});

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      "Name of Child": resolvedStudentName ?? prev["Name of Child"],
      "Age": resolvedStudentAge ?? prev["Age"],
      "Date of Birth": resolvedStudentDob ?? prev["Date of Birth"],
      "Class (बच्चे की कक्षा)": resolvedStudentClass ?? prev["Class (बच्चे की कक्षा)"],
    }));
  }, [resolvedStudentName, resolvedStudentAge, resolvedStudentDob, resolvedStudentClass]);

  useEffect(() => {
    const updateTimestamp = () => {
      setFormData((prev) => ({
        ...prev,
        Timestamp: new Date().toISOString(),
      }));
    };

    updateTimestamp();
    const timer = window.setInterval(updateTimestamp, 1000);

    return () => window.clearInterval(timer);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation checks
    const newErrors: FormErrors = {};
    
    if (!formData["Name of Child"].trim()) {
      newErrors["Name of Child"] = "Name is required";
    } else if (!validateName(formData["Name of Child"])) {
      newErrors["Name of Child"] = "Please enter a valid name (letters and spaces only)";
    }
    
    const age = Number(formData["Age"]);
    if (isNaN(age) || !validateAge(age)) {
      newErrors["Age"] = "Age must be between 5 and 18";
    }
    
    const classNum = Number(formData["Class (बच्चे की कक्षा)"]);
    if (isNaN(classNum) || !validateClass(classNum)) {
      newErrors["Class (बच्चे की कक्षा)"] = "Class must be between 1 and 12";
    }
    
    const performance = Number(formData["Academic Performance"]);
    if (isNaN(performance) || !validateAcademicPerformance(performance)) {
      newErrors["Academic Performance"] = "Academic Performance must be between 0 and 100";
    }
    
    const income = Number(formData["Family Income"]);
    if (isNaN(income) || !validateFamilyIncome(income)) {
      newErrors["Family Income"] = "Family Income must be greater than 0";
    }
    
    // Check for required fields
    const requiredFields = [
      "Timestamp",
      "Name of Child",
      "Age",
      "Date of Birth",
      "Class (बच्चे की कक्षा)",
      "Background of the Child",
      "Problems in Home",
      "Behavioral Impact",
      "Academic Performance",
      "Family Income",
      "Role Models",
      "Reason for Such Role Model",
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
        "Academic Performance": parseFloat(formData["Academic Performance"]),
        "Family Income": parseFloat(formData["Family Income"])
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
          "Timestamp": new Date().toISOString(),
          "Name of Child": "",
          "Age": "",
          "Date of Birth": "",
          "Class (बच्चे की कक्षा)": "",
          "Background of the Child": "",
          "Problems in Home": "",
          "Behavioral Impact": "",
          "Academic Performance": "",
          "Family Income": "",
          "Role Models": "",
          "Reason for Such Role Model": ""
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
          {isStudentDobFixed ? ' Date of birth is locked to the student profile.' : ' Results will be visible only to the associated school admin.'}
        </div>
      )}
      <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Career Guidance Survey</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Child Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          <div>
            <label htmlFor="timestamp" className="block text-sm font-medium text-gray-700 mb-1">
              Timestamp *
            </label>
            <input
              id="timestamp"
              type="datetime-local"
              name="Timestamp"
              value={formatDateTimeLocalValue(formData["Timestamp"])}
              readOnly
              step={1}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Timestamp"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            />
            <p className="mt-1 text-xs text-gray-500">
              This timestamp updates automatically in real time.
            </p>
          </div>
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name of Child *
            </label>
            <input
              id="name"
              type="text"
              name="Name of Child"
              value={formData["Name of Child"]}
              onChange={handleChange}
              disabled={isStudentNameFixed}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Name of Child"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
              aria-required="true"
              aria-invalid={Boolean(errors["Name of Child"])}
            />
            {isStudentNameFixed && (
              <p className="mt-1 text-xs text-gray-500">
                This name comes from the selected student profile and cannot be changed here.
              </p>
            )}
            {errors["Name of Child"] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Name of Child"]}. Please enter letters and spaces only.
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
          <label htmlFor="dob" className="block text-sm font-medium text-gray-700 mb-1">
            Date of Birth *
          </label>
          <input
            id="dob"
            type="date"
            name="Date of Birth"
            value={formData["Date of Birth"]}
            onChange={handleChange}
            disabled={isStudentDobFixed}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Date of Birth"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
          />
          {isStudentDobFixed && (
            <p className="mt-1 text-xs text-gray-500">
              This date of birth comes from the selected student profile and cannot be changed here.
            </p>
          )}
          {errors["Date of Birth"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Date of Birth"]}.
            </p>
          )}
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
            name="Background of the Child"
            value={formData["Background of the Child"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Background of the Child"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Background of the Child"] )}
          />
          {errors["Background of the Child"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Background of the Child"]}. Describe briefly (e.g. "Middle class family").
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
            name="Problems in Home"
            value={formData["Problems in Home"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Problems in Home"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            aria-required="true"
            aria-invalid={Boolean(errors["Problems in Home"] )}
          />
          {errors["Problems in Home"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Problems in Home"]}. Mention any major challenges (financial, family, etc.).
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
              Academic Performance *
            </label>
            <input
              id="academic"
              type="number"
              name="Academic Performance"
              value={formData["Academic Performance"]}
              onChange={handleChange}
              min="1"
              max="100"
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Academic Performance"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            />
            {errors["Academic Performance"] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Academic Performance"]}. Enter a score between 0 and 100.
              </p>
            )}
          </div>
          <div>
            <label htmlFor="income" className="block text-sm font-medium text-gray-700 mb-1">
              Family Income *
            </label>
            <input
              id="income"
              type="number"
              name="Family Income"
              value={formData["Family Income"]}
              onChange={handleChange}
              required
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Family Income"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            />
            {errors["Family Income"] && (
              <p className="mt-1 text-xs text-red-600">
                {errors["Family Income"]}. Provide a positive monthly amount.
              </p>
            )}
          </div>
        </div>

        {/* Role Models */}
        <div>
          <label htmlFor="roleModels" className="block text-sm font-medium text-gray-700 mb-1">
            Role Models *
          </label>
          <input
            id="roleModels"
            type="text"
            name="Role Models"
            value={formData["Role Models"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Role Models"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
          />
          {errors["Role Models"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Role Models"]}. Mention who inspires the student.
            </p>
          )}
        </div>

        {/* Reason for role model */}
        <div>
          <label htmlFor="reasonForRoleModel" className="block text-sm font-medium text-gray-700 mb-1">
            Reason for Such Role Model *
          </label>
          <input
            id="reasonForRoleModel"
            type="text"
            name="Reason for Such Role Model"
            value={formData["Reason for Such Role Model"]}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${errors["Reason for Such Role Model"] ? 'border-red-400 focus:ring-red-400' : 'border-gray-200 focus:ring-purple-500'}`}
            placeholder="Explain why this role model inspires the child"
            aria-required="true"
            aria-invalid={Boolean(errors["Reason for Such Role Model"] )}
          />
          {errors["Reason for Such Role Model"] && (
            <p className="mt-1 text-xs text-red-600">
              {errors["Reason for Such Role Model"]}. Say why this role model matters.
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
