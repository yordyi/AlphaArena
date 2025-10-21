import { NextResponse } from 'next/server'

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5000'

export async function GET() {
  try {
    const response = await fetch(`${PYTHON_API_URL}/api/positions`, {
      cache: 'no-store',
    })

    if (!response.ok) {
      throw new Error(`Python API error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching positions:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch positions' },
      { status: 500 }
    )
  }
}
