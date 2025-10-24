import { NextResponse } from 'next/server';
import { createBinanceClient } from '@/lib/binance';

export async function GET() {
  try {
    const client = createBinanceClient();
    const [accountInfo, balances, positions] = await Promise.all([
      client.getAccountInfo(),
      client.getBalances(),
      client.getPositions(),
    ]);

    return NextResponse.json({
      account: accountInfo,
      balances,
      positions,
    });
  } catch (error: any) {
    console.error('Failed to fetch account data:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch account data' },
      { status: 500 }
    );
  }
}
