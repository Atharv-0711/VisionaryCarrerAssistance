import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiRequest } from '../../utils/api';

interface VerificationResponse {
  message?: string;
  error?: string;
}

const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(
    'loading'
  );
  const [message, setMessage] = useState<string>('Verifying your account...');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('Verification token is missing.');
      return;
    }

    const verify = async () => {
      try {
        const response = await apiRequest<VerificationResponse>(
          `/api/auth/verify/${token}`,
          {
            method: 'GET',
            authToken: null,
          }
        );

        setStatus('success');
        setMessage(response.message || 'Account verified successfully.');
      } catch (err) {
        setStatus('error');
        setMessage(
          err instanceof Error
            ? err.message
            : 'We could not verify your account.'
        );
      }
    };

    verify();
  }, [searchParams]);

  const isSuccess = status === 'success';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center px-4">
      <div className="w-full max-w-lg bg-white shadow-xl rounded-2xl p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Email Verification
        </h1>
        <p
          className={`text-sm mb-6 ${
            isSuccess ? 'text-green-600' : 'text-gray-600'
          }`}
        >
          {message}
        </p>

        <div className="space-y-3 text-sm">
          {isSuccess ? (
            <>
              <p>Your account is ready. You can now sign in.</p>
              <Link
                to="/login"
                className="inline-block rounded-lg bg-purple-600 px-4 py-2 text-white font-semibold hover:bg-purple-700 transition-colors"
              >
                Go to Login
              </Link>
            </>
          ) : status === 'loading' ? (
            <p>Please wait while we confirm your email...</p>
          ) : (
            <>
              <p>
                We could not verify your account. Make sure you opened the most
                recent verification email.
              </p>
              <Link
                to="/signup"
                className="inline-block rounded-lg bg-purple-600 px-4 py-2 text-white font-semibold hover:bg-purple-700 transition-colors"
              >
                Back to Signup
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailPage;


