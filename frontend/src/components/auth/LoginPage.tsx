import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest } from '../../utils/api';

type UserRole = 'school_admin' | 'mentor';

interface LoginResponse {
  message: string;
  user: {
    email: string;
    role: UserRole;
    token: string;
  };
}

interface LoginPageProps {
  onLoginSuccess: (user: LoginResponse['user']) => string;
}

const roleOptions: Array<{ value: UserRole; label: string }> = [
  { value: 'school_admin', label: 'School Admin' },
  { value: 'mentor', label: 'Mentor' },
];

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [formState, setFormState] = useState({
    email: '',
    password: '',
    role: roleOptions[0].value,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (field: 'email' | 'password' | 'role') => (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormState((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiRequest<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(formState),
        authToken: null,
      });

      const nextPath = onLoginSuccess(response.user);
      navigate(nextPath, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white shadow-xl rounded-2xl p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome Back to Visionary Career Assistance
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Login to continue as a School Admin or Mentor, or{' '}
            <Link
              to="/signup"
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              create a new account
            </Link>
            .
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email address
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={formState.email}
              onChange={handleChange('email')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={formState.password}
              onChange={handleChange('password')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
            />
          </div>

          <div>
            <label
              htmlFor="role"
              className="block text-sm font-medium text-gray-700"
            >
              Login as
            </label>
            <select
              id="role"
              value={formState.role}
              onChange={handleChange('role')}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
            >
              {roleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-purple-600 py-2.5 text-white font-semibold hover:bg-purple-700 transition-colors disabled:opacity-60"
          >
            {loading ? 'Signing you in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-xs text-gray-500 text-center">
          Having trouble logging in? Make sure you have verified your email via
          the link we sent after signup.
        </div>
      </div>
    </div>
  );
};

export default LoginPage;


