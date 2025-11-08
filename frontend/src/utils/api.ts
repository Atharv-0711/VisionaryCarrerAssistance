const getDefaultApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const { origin } = window.location;
    if (
      origin &&
      origin !== 'file://' &&
      !origin.includes('localhost') &&
      !origin.includes('127.0.0.1')
    ) {
      return origin;
    }
  }
  return 'http://localhost:5000';
};

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? getDefaultApiBaseUrl();

interface ApiErrorPayload {
  error?: string;
  message?: string;
}

export interface ApiRequestOptions extends RequestInit {
  /**
   * When provided, overrides the auth token sent with the request.
   * - set to `null` to explicitly omit a token
   * - set to a string to use that token
   * - leave undefined to automatically use the stored token (if any)
   */
  authToken?: string | null;
}

const getStoredAuthToken = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.localStorage.getItem('authUser');
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    return typeof parsed?.token === 'string' ? parsed.token : null;
  } catch (error) {
    console.warn('Failed to read stored auth token', error);
    return null;
  }
};

const mergeHeaders = (
  base: Record<string, string>,
  incoming?: HeadersInit
): Record<string, string> => {
  if (!incoming) {
    return base;
  }

  if (incoming instanceof Headers) {
    incoming.forEach((value, key) => {
      base[key] = value;
    });
  } else if (Array.isArray(incoming)) {
    incoming.forEach(([key, value]) => {
      base[key] = value;
    });
  } else {
    Object.assign(base, incoming);
  }

  return base;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const { authToken, headers, ...fetchOptions } = options;
  const combinedHeaders = mergeHeaders(
    {
      'Content-Type': 'application/json',
    },
    headers
  );

  let tokenToUse: string | null;
  if (authToken === null) {
    tokenToUse = null;
  } else if (typeof authToken === 'string') {
    tokenToUse = authToken;
  } else {
    tokenToUse = getStoredAuthToken();
  }

  if (tokenToUse) {
    combinedHeaders['X-Auth-Token'] = tokenToUse;
  } else {
    delete combinedHeaders['X-Auth-Token'];
  }

  const requestInit: RequestInit = {
    headers: combinedHeaders,
    ...fetchOptions,
  };

  const attemptFetch = (base: string) =>
    fetch(`${base}${path}`, requestInit);

  let response: Response;

  try {
    response = await attemptFetch(API_BASE_URL);
  } catch (error) {
    const shouldRetryWithOrigin =
      typeof window !== 'undefined' &&
      API_BASE_URL !== window.location.origin &&
      (error instanceof TypeError || error instanceof Error);

    if (shouldRetryWithOrigin) {
      response = await attemptFetch(window.location.origin);
    } else {
      throw error;
    }
  }

  let parsedBody: ApiErrorPayload | string | null = null;
  const responseType = response.headers.get('content-type');

  if (responseType && responseType.includes('application/json')) {
    parsedBody = await response.json();
  } else {
    parsedBody = await response.text();
  }

  if (!response.ok) {
    const message =
      (parsedBody &&
        typeof parsedBody === 'object' &&
        (parsedBody.error || parsedBody.message)) ||
      (typeof parsedBody === 'string' ? parsedBody : 'Request failed');
    throw new Error(message);
  }

  return parsedBody as T;
}


