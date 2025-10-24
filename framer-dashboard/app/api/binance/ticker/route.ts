import { NextResponse } from 'next/server';
import { createBinanceClient } from '@/lib/binance';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get('symbol');

    const client = createBinanceClient();
    const ticker = await client.get24hrTicker(symbol || undefined);

    return NextResponse.json({ ticker });
  } catch (error: any) {
    console.error('Failed to fetch ticker:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch ticker data' },
      { status: 500 }
    );
  }
}
