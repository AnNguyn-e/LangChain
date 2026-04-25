import React from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  colorClass?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, colorClass = "bg-blue-500" }) => {
  return (
    <div className={`p-6 rounded-lg shadow-md text-white ${colorClass}`}>
      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm opacity-80 uppercase font-semibold">{title}</p>
          <h3 className="text-3xl font-bold mt-2">{value}</h3>
        </div>
        {icon && <div className="text-4xl opacity-50">{icon}</div>}
      </div>
    </div>
  );
};
