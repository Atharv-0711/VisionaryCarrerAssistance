import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  UserPlus,
  Users,
  ClipboardList,
  GraduationCap,
  Mail,
  RefreshCcw,
  Search,
  Trash2,
  UserCheck,
} from 'lucide-react';
import { apiRequest } from '../utils/api';

interface Student {
  id: number;
  school_number?: string | null;
  full_name: string;
  unique_code: string;
  age?: number | null;
  date_of_birth?: string | null;
  class_level?: string | null;
  guardian_contact?: string | null;
  additional_info?: string | null;
  created_at: string;
}

interface StudentAssessmentProps {
  authToken: string;
}

interface AssessmentSummary {
  id: number;
  created_at: string;
  headline?: string | null;
  backgroundAverageScore?: number | null;
  student_id?: number | null;
}

interface StudentMentorMatch {
  assessmentId?: number;
  basedOnTrait?: string | null;
  backgroundScore?: number | null;
  recommendations: string[];
}

const emptyFormState = {
  full_name: '',
  age: '',
  date_of_birth: '',
  class_level: '',
  guardian_contact: '',
  additional_info: '',
};

const StudentAssessment: React.FC<StudentAssessmentProps> = ({
  authToken,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [students, setStudents] = useState<Student[]>([]);
  const [formState, setFormState] = useState(emptyFormState);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lookupCode, setLookupCode] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [mentorMatch, setMentorMatch] = useState<StudentMentorMatch | null>(null);
  const [loadingMentorMatch, setLoadingMentorMatch] = useState(false);
  const [deletingStudent, setDeletingStudent] = useState(false);

  const focusStudentId = useMemo(() => {
    const state = location.state as { focusStudentId?: number } | null;
    if (state?.focusStudentId) {
      return state.focusStudentId;
    }
    const params = new URLSearchParams(location.search);
    const studentId = params.get('studentId');
    if (studentId) {
      const parsed = Number.parseInt(studentId, 10);
      return Number.isNaN(parsed) ? undefined : parsed;
    }
    return undefined;
  }, [location]);

  const fetchStudents = useCallback(async () => {
    setLoadingStudents(true);
    setError(null);
    try {
      const result = await apiRequest<Student[]>('/api/students', {
        authToken,
      });
      setStudents(result);
      if (result.length > 0) {
        const target = focusStudentId
          ? result.find((student) => student.id === focusStudentId)
          : result.find((student) => student.id === selectedStudent?.id);
        setSelectedStudent(target ?? result[0]);
      } else {
        setSelectedStudent(null);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to load students.';
      setError(message);
      setStudents([]);
    } finally {
      setLoadingStudents(false);
    }
  }, [authToken, focusStudentId, selectedStudent?.id]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const handleInputChange = (
    field: keyof typeof emptyFormState,
    value: string
  ) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleRegisterStudent = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!formState.full_name.trim()) {
      alert('Student name is required.');
      return;
    }

    setFormSubmitting(true);
    setError(null);

    try {
      const payload = {
        full_name: formState.full_name.trim(),
        age: formState.age ? Number.parseInt(formState.age, 10) : undefined,
        date_of_birth: formState.date_of_birth || undefined,
        class_level: formState.class_level.trim(),
        guardian_contact: formState.guardian_contact.trim(),
        additional_info: formState.additional_info.trim(),
      };

      const response = await apiRequest<{
        message: string;
        student: Student;
      }>('/api/students', {
        method: 'POST',
        body: JSON.stringify(payload),
        authToken,
      });

      alert(
        `${response.message}\nStudent Code: ${response.student.unique_code}`
      );
      setFormState(emptyFormState);
      setStudents((prev) => [response.student, ...prev]);
      setSelectedStudent(response.student);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to register student.';
      setError(message);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleLookupStudent = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!lookupCode.trim()) {
      alert('Enter the student code to continue.');
      return;
    }

    setError(null);
    try {
      const student = await apiRequest<Student>('/api/students/lookup', {
        method: 'POST',
        body: JSON.stringify({ code: lookupCode.trim() }),
        authToken,
      });
      setSelectedStudent(student);
      if (!students.find((item) => item.id === student.id)) {
        setStudents((prev) => [student, ...prev]);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to find student.';
      setError(message);
    }
  };

  const handleSelectStudent = (student: Student) => {
    setSelectedStudent(student);
  };

  const handleTakeSurvey = () => {
    if (!selectedStudent) return;
    navigate('/survey', {
      state: {
        studentId: selectedStudent.id,
        studentName: selectedStudent.full_name,
        studentAge: selectedStudent.age ?? undefined,
        studentDob: selectedStudent.date_of_birth ?? undefined,
        studentClass: selectedStudent.class_level ?? undefined,
      },
    });
  };

  const handleViewAssessments = () => {
    if (!selectedStudent) return;
    navigate(
      `/assessments?studentId=${selectedStudent.id}&studentName=${encodeURIComponent(
        selectedStudent.full_name
      )}`
    );
  };

  const buildMentorRecommendations = (assessment?: AssessmentSummary): StudentMentorMatch => {
    if (!assessment) {
      return {
        recommendations: [
          'No assessment data yet. Take a survey to unlock student-specific mentor matching.',
          'Start with a General Academic Mentor for baseline guidance.',
        ],
      };
    }

    const trait = (assessment.headline || '').toLowerCase();
    const recommendations: string[] = [];

    if (trait.includes('lead')) recommendations.push('Leadership Mentor');
    if (trait.includes('commun')) recommendations.push('Communication Coach');
    if (trait.includes('analyt')) recommendations.push('STEM / Problem-Solving Mentor');
    if (trait.includes('creativ') || trait.includes('express'))
      recommendations.push('Creative Arts Mentor');
    if (trait.includes('empath')) recommendations.push('Wellbeing Counselor');

    const bg = assessment.backgroundAverageScore;
    if (typeof bg === 'number' && bg < 2.8) {
      recommendations.push('Psychosocial Support Mentor');
    }
    if (typeof bg === 'number' && bg >= 3.8) {
      recommendations.push('Career Acceleration Mentor');
    }
    if (recommendations.length === 0) {
      recommendations.push('General Academic Mentor');
      recommendations.push('Career Guidance Mentor');
    }

    return {
      assessmentId: assessment.id,
      basedOnTrait: assessment.headline ?? null,
      backgroundScore: assessment.backgroundAverageScore ?? null,
      recommendations: Array.from(new Set(recommendations)).slice(0, 4),
    };
  };

  const fetchMentorMatch = useCallback(async () => {
    if (!selectedStudent) {
      setMentorMatch(null);
      return;
    }

    setLoadingMentorMatch(true);
    try {
      const assessments = await apiRequest<AssessmentSummary[]>(
        `/api/assessments?student_id=${selectedStudent.id}`,
        { authToken }
      );
      const latest = Array.isArray(assessments) && assessments.length > 0 ? assessments[0] : undefined;
      setMentorMatch(buildMentorRecommendations(latest));
    } catch (_err) {
      setMentorMatch({
        recommendations: ['Unable to load mentor matching right now.'],
      });
    } finally {
      setLoadingMentorMatch(false);
    }
  }, [authToken, selectedStudent]);

  useEffect(() => {
    fetchMentorMatch();
  }, [fetchMentorMatch]);

  const handleDeleteStudent = async () => {
    if (!selectedStudent) return;

    const confirmed = window.confirm(
      `Delete ${selectedStudent.full_name}? This removes the student profile. Existing assessments stay available but become unlinked.`
    );
    if (!confirmed) return;

    setDeletingStudent(true);
    setError(null);
    try {
      try {
        await apiRequest<{ message: string }>(`/api/students/${selectedStudent.id}`, {
          method: 'DELETE',
          authToken,
        });
      } catch (primaryError) {
        const message =
          primaryError instanceof Error ? primaryError.message.toLowerCase() : '';
        const shouldFallback =
          message.includes('method') ||
          message.includes('not allowed') ||
          message.includes('405');

        if (!shouldFallback) {
          throw primaryError;
        }

        try {
          await apiRequest<{ message: string }>(`/api/students/${selectedStudent.id}`, {
            method: 'POST',
            authToken,
          });
        } catch (secondaryError) {
          const secondaryMessage =
            secondaryError instanceof Error ? secondaryError.message.toLowerCase() : '';
          const shouldUseLegacyFallback =
            secondaryMessage.includes('method') ||
            secondaryMessage.includes('not allowed') ||
            secondaryMessage.includes('405');

          if (!shouldUseLegacyFallback) {
            throw secondaryError;
          }

          await apiRequest<{ message: string }>(
            `/api/students/${selectedStudent.id}/delete`,
            {
              method: 'POST',
              authToken,
            }
          );
        }
      }

      setStudents((prev) => {
        const remaining = prev.filter((student) => student.id !== selectedStudent.id);
        setSelectedStudent(remaining.length > 0 ? remaining[0] : null);
        return remaining;
      });
      setMentorMatch(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to delete student.';
      setError(message);
    } finally {
      setDeletingStudent(false);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <div className="rounded-2xl bg-white shadow-sm p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 flex items-center space-x-2">
            <GraduationCap className="h-6 w-6 text-purple-600" />
            <span>Student Assessment Hub</span>
          </h1>
          <button
            onClick={fetchStudents}
            disabled={loadingStudents}
            className="inline-flex items-center justify-center space-x-2 rounded-lg border border-purple-200 px-3 py-2 min-h-[44px] text-sm font-medium text-purple-600 hover:bg-purple-50 disabled:opacity-60"
          >
            <RefreshCcw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
        <p className="mt-2 text-sm text-gray-500 leading-relaxed">
          Register new students or locate existing profiles. Each student
          receives a unique code that can be used to track assessments and
          progress. Assessment results remain visible only to school admins.
        </p>
        {error && (
          <div className="mt-4 rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}
      </div>

      <div className="grid gap-6 sm:gap-8 md:grid-cols-5">
        <div className="md:col-span-2 space-y-6">
          <div className="rounded-2xl border border-gray-100 bg-white p-5 sm:p-6 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              <UserPlus className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Register New Student
              </h2>
            </div>
            <form className="space-y-4" onSubmit={handleRegisterStudent}>
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formState.full_name}
                  onChange={(event) =>
                    handleInputChange('full_name', event.target.value)
                  }
                  required
                  className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Age
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formState.age}
                    onChange={(event) =>
                      handleInputChange('age', event.target.value)
                    }
                    className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={formState.date_of_birth}
                    onChange={(event) =>
                      handleInputChange('date_of_birth', event.target.value)
                    }
                    className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Class / Grade
                  </label>
                  <input
                    type="text"
                    value={formState.class_level}
                    onChange={(event) =>
                      handleInputChange('class_level', event.target.value)
                    }
                    className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Guardian Contact
                  </label>
                  <input
                    type="text"
                    value={formState.guardian_contact}
                    onChange={(event) =>
                      handleInputChange('guardian_contact', event.target.value)
                    }
                    className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Notes
                  </label>
                  <textarea
                    value={formState.additional_info}
                    onChange={(event) =>
                      handleInputChange('additional_info', event.target.value)
                    }
                    rows={3}
                    className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={formSubmitting}
                className="w-full rounded-md bg-purple-600 px-4 py-2 min-h-[44px] text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-60"
              >
                {formSubmitting ? 'Registering...' : 'Register Student'}
              </button>
            </form>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-5 sm:p-6 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              <Search className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Find Student by Code
              </h2>
            </div>
            <form className="space-y-3" onSubmit={handleLookupStudent}>
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Student Code
                </label>
                <input
                  type="text"
                  value={lookupCode}
                  onChange={(event) => setLookupCode(event.target.value)}
                  className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm uppercase focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
              </div>
              <button
                type="submit"
                className="w-full rounded-md border border-purple-200 px-4 py-2 min-h-[44px] text-sm font-semibold text-purple-600 hover:bg-purple-50"
              >
                Lookup Student
              </button>
            </form>
          </div>
        </div>

        <div className="md:col-span-3 space-y-6">
          <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow">
            <div className="flex items-center space-x-2 mb-4">
              <Users className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Students ({students.length})
              </h2>
            </div>
            <div className="max-h-[320px] overflow-y-auto divide-y divide-gray-100">
              {loadingStudents ? (
                <div className="py-12 text-center text-sm text-gray-500">
                  Loading students...
                </div>
              ) : students.length === 0 ? (
                <div className="py-12 text-center text-sm text-gray-500">
                  No students registered yet.
                </div>
              ) : (
                students.map((student) => {
                  const isActive = selectedStudent?.id === student.id;
                  return (
                    <button
                      key={student.id}
                      onClick={() => handleSelectStudent(student)}
                      className={`w-full px-3 sm:px-4 py-3 text-left transition-colors ${
                        isActive
                          ? 'bg-purple-50 border-l-4 border-purple-400'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {student.full_name}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            Code: {student.unique_code}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            School No: {student.school_number || 'N/A'}
                          </p>
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(student.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      {(student.age || student.class_level) && (
                        <p className="mt-1 text-xs text-gray-500">
                          {student.age ? `Age: ${student.age}` : ''}
                          {student.age && student.class_level ? ' · ' : ''}
                          {student.class_level ? `Class: ${student.class_level}` : ''}
                        </p>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {selectedStudent && (
            <div className="rounded-2xl border border-purple-200 bg-white p-5 sm:p-6 shadow-sm space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedStudent.full_name}
                </h3>
                <p className="text-sm text-gray-500">
                  Student Code: <span className="font-medium">{selectedStudent.unique_code}</span>
                </p>
                <p className="text-sm text-gray-500">
                  School Number: <span className="font-medium">{selectedStudent.school_number || 'N/A'}</span>
                </p>
                <p className="text-sm text-gray-500">
                  Date of Birth: <span className="font-medium">{selectedStudent.date_of_birth || 'Not set'}</span>
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <button
                  onClick={handleTakeSurvey}
                  className="rounded-lg bg-purple-600 px-4 py-3 min-h-[44px] text-sm font-semibold text-white hover:bg-purple-700 flex items-center justify-center space-x-2"
                >
                  <ClipboardList className="h-4 w-4" />
                  <span>Take Survey</span>
                </button>
                <button
                  onClick={handleViewAssessments}
                  className="rounded-lg border border-purple-200 px-4 py-3 min-h-[44px] text-sm font-semibold text-purple-600 hover:bg-purple-50 flex items-center justify-center space-x-2"
                >
                  <Mail className="h-4 w-4" />
                  <span>View Assessments</span>
                </button>
              </div>
              <button
                onClick={handleDeleteStudent}
                disabled={deletingStudent}
                className="w-full rounded-lg border border-red-200 px-4 py-3 min-h-[44px] text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-60 flex items-center justify-center space-x-2"
              >
                <Trash2 className="h-4 w-4" />
                <span>{deletingStudent ? 'Deleting Student...' : 'Delete Student'}</span>
              </button>
              {selectedStudent.guardian_contact && (
                <div className="rounded-lg bg-purple-50 p-4 text-sm text-purple-800">
                  Guardian Contact: {selectedStudent.guardian_contact}
                </div>
              )}
              {selectedStudent.additional_info && (
                <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800 whitespace-pre-wrap">
                  {selectedStudent.additional_info}
                </div>
              )}
              <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <UserCheck className="h-4 w-4 text-green-700" />
                  <p className="text-sm font-semibold text-green-800">
                    Mentor Matching for this Student
                  </p>
                </div>
                {loadingMentorMatch ? (
                  <p className="text-sm text-green-700">Loading mentor matching...</p>
                ) : (
                  <div className="space-y-2">
                    {mentorMatch?.basedOnTrait && (
                      <p className="text-xs text-green-700">
                        Based on top trait: <span className="font-medium">{mentorMatch.basedOnTrait}</span>
                      </p>
                    )}
                    {typeof mentorMatch?.backgroundScore === 'number' && (
                      <p className="text-xs text-green-700">
                        Background score: <span className="font-medium">{mentorMatch.backgroundScore.toFixed(2)}</span>
                      </p>
                    )}
                    <ul className="text-sm text-green-800 list-disc pl-5 space-y-1">
                      {(mentorMatch?.recommendations || ['No mentor suggestions available yet.']).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentAssessment;


