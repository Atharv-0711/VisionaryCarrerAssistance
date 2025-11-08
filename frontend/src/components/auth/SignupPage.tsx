import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../utils/api';

type UserRole = 'school_admin' | 'mentor';

interface SignupResponse {
  message: string;
  verificationUrl?: string;
  verificationToken?: string;
  emailDelivery?: {
    status: 'sent' | 'not_sent';
    error?: string;
  };
}

interface VerificationResponse {
  message?: string;
  error?: string;
}

const roleOptions: Array<{ value: UserRole; label: string }> = [
  { value: 'school_admin', label: 'School Admin' },
  { value: 'mentor', label: 'Mentor' },
];

const SignupPage: React.FC = () => {
  const [formState, setFormState] = useState({
    email: '',
    password: '',
    role: roleOptions[0].value,
  });
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [verificationUrl, setVerificationUrl] = useState<string | null>(null);
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [emailDeliveryInfo, setEmailDeliveryInfo] = useState<string | null>(null);
  const [manualVerifyStatus, setManualVerifyStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [manualVerifyMessage, setManualVerifyMessage] = useState<string | null>(null);

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
    setSuccessMessage(null);
    setVerificationUrl(null);
    setVerificationToken(null);
    setEmailDeliveryInfo(null);
    setManualVerifyStatus('idle');
    setManualVerifyMessage(null);

    try {
      const response = await apiRequest<SignupResponse>('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify(formState),
        authToken: null,
      });
      setSuccessMessage(response.message);
      setVerificationUrl(response.verificationUrl ?? null);
      setVerificationToken(response.verificationToken ?? null);

      if (response.emailDelivery?.status === 'not_sent') {
        const reason =
          response.emailDelivery.error ??
          'Email delivery is not configured. Use the verification button below.';
        setEmailDeliveryInfo(reason);
      } else if (response.emailDelivery?.status === 'sent') {
        setEmailDeliveryInfo(
          'A verification email has been sent. Please check your inbox (and spam folder).'
        );
      }

      setFormState({
        email: '',
        password: '',
        role: roleOptions[0].value,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign up.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualVerification = async () => {
    if (!verificationToken) {
      return;
    }

    setManualVerifyStatus('loading');
    setManualVerifyMessage(null);

    try {
      const response = await apiRequest<VerificationResponse>(
        `/api/auth/verify/${verificationToken}`,
        { method: 'GET', authToken: null }
      );
      setManualVerifyStatus('success');
      setManualVerifyMessage(response.message ?? 'Account verified successfully.');
    } catch (err) {
      setManualVerifyStatus('error');
      setManualVerifyMessage(
        err instanceof Error ? err.message : 'Verification failed. Please try again.'
      );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center px-4">
      <div className="w-full max-w-xl bg-white shadow-xl rounded-2xl p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Create your Visionary Career Assistance account
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Join as a School Admin or Mentor to unlock personalized student
            insights and collaboration tools.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700">
            <p>{successMessage}</p>
            {emailDeliveryInfo && (
              <p className="mt-2 text-gray-700">{emailDeliveryInfo}</p>
            )}
            {verificationToken && (
              <div className="mt-4 space-y-3 rounded-md border border-green-200 bg-white p-4 text-left">
                <p className="text-sm text-gray-600">
                  You can also verify instantly using the button below if the email
                  hasn&apos;t arrived yet.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handleManualVerification}
                    disabled={manualVerifyStatus === 'loading' || manualVerifyStatus === 'success'}
                    className="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {manualVerifyStatus === 'loading'
                      ? 'Verifying...'
                      : manualVerifyStatus === 'success'
                      ? 'Verified'
                      : 'Verify Now'}
                  </button>
                  {verificationUrl && (
                    <a
                      href={verificationUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-medium text-purple-600 hover:text-purple-700"
                    >
                      Open verification link
                    </a>
                  )}
                </div>
                {manualVerifyMessage && (
                  <div
                    className={`text-sm ${
                      manualVerifyStatus === 'success'
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {manualVerifyMessage}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="grid gap-5 md:grid-cols-2">
            <div className="md:col-span-2">
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
                value={formState.email}
                onChange={handleChange('email')}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
              />
            </div>

            <div className="md:col-span-2">
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
                value={formState.password}
                onChange={handleChange('password')}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
              />
            </div>

            <div className="md:col-span-2">
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700"
              >
                Sign up as
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
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-purple-600 py-2.5 text-white font-semibold hover:bg-purple-700 transition-colors disabled:opacity-60"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <div className="mt-6 text-sm text-gray-500 text-center">
          Already have an account?{' '}
          <Link
            to="/login"
            className="text-purple-600 hover:text-purple-700 font-medium"
          >
            Login here
          </Link>
          .
          <div className="mt-2 text-xs">
            We will send you a verification email. You must confirm your email
            before logging in.
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;


