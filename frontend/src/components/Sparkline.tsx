import { Line, LineChart, ResponsiveContainer } from 'recharts'

export function Sparkline({ data, color }: { data: number[]; color: string }) {
  const points = data.map((value, i) => ({ i, value }))
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={points} margin={{ top: 4, right: 2, bottom: 4, left: 2 }}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
