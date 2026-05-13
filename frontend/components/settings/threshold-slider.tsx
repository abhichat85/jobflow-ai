"use client";

interface Props {
  label: string;
  value: number;
  min?: number;
  max?: number;
  onChange: (v: number) => void;
  hint?: string;
}

export function ThresholdSlider({ label, value, min = 50, max = 90, onChange, hint }: Props) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-gray-600">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      {hint && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  );
}
