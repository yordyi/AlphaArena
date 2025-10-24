import { NextResponse } from 'next/server';
import { createBinanceClient } from '@/lib/binance';

export async function GET() {
  try {
    const client = createBinanceClient();
    const positions = await client.getPositions();

    // Fetch current prices for all positions
    const positionsWithPrices = await Promise.all(
      positions.map(async (position) => {
        const currentPrice = await client.getPrice(position.symbol);
        const entryPrice = parseFloat(position.entryPrice);
        const positionAmt = parseFloat(position.positionAmt);
        const unrealizedProfit = parseFloat(position.unRealizedProfit);

        // Calculate profit percentage
        const profitPct = entryPrice > 0
          ? ((currentPrice - entryPrice) / entryPrice) * 100 * (positionAmt > 0 ? 1 : -1)
          : 0;

        return {
          ...position,
          currentPrice: currentPrice.toString(),
          profitPct: profitPct.toFixed(2),
        };
      })
    );

    return NextResponse.json({ positions: positionsWithPrices });
  } catch (error: any) {
    console.error('Failed to fetch positions:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch positions' },
      { status: 500 }
    );
  }
}
