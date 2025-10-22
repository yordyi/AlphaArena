import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // 从Flask后端获取图表数据
    const response = await fetch('http://localhost:5001/api/chart')
    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching chart data:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch chart data' },
      { status: 500 }
    )
  }
}
