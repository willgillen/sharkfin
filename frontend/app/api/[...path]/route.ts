import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PUT');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PATCH');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'DELETE');
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  // Get backend URL at runtime
  const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:5499';

  const path = pathSegments.join('/');
  const url = new URL(request.url);

  // Build backend URL with query params - add /api prefix since our catch-all removes it
  const backendUrl = `${BACKEND_URL}/api/${path}${url.search}`;

  // Get request body if present
  let body: string | undefined;
  if (method !== 'GET' && method !== 'DELETE') {
    try {
      body = await request.text();
    } catch (e) {
      // No body
    }
  }

  // Forward headers (excluding some that shouldn't be forwarded)
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!['host', 'connection', 'content-length'].includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  try {
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
    });

    // Get response body
    const responseBody = await response.text();

    // Create response with same status and headers
    const nextResponse = new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
    });

    // Copy relevant response headers
    response.headers.forEach((value, key) => {
      if (!['connection', 'transfer-encoding'].includes(key.toLowerCase())) {
        nextResponse.headers.set(key, value);
      }
    });

    return nextResponse;
  } catch (error) {
    console.error('Proxy error - Backend URL:', backendUrl);
    console.error('Proxy error - Error details:', error);
    console.error('Proxy error - BACKEND_URL env:', process.env.BACKEND_URL);
    return NextResponse.json(
      {
        error: 'Backend service unavailable',
        details: error instanceof Error ? error.message : 'Unknown error',
        backendUrl: backendUrl
      },
      { status: 503 }
    );
  }
}
