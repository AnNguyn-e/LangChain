import React from 'react';

interface RoleBadgeProps {
  role: 'USER' | 'MANAGER' | 'ADMIN';
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role }) => {
  const getRoleColor = () => {
    switch (role) {
      case 'ADMIN':
        return 'bg-red-100 text-red-800';
      case 'MANAGER':
        return 'bg-purple-100 text-purple-800';
      case 'USER':
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleColor()}`}>
      {role}
    </span>
  );
};
