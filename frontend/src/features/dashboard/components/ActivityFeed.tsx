import React from 'react';
import { RecentDocument } from '../models/stats';

interface ActivityFeedProps {
  documents: RecentDocument[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return <div className="text-gray-500 italic">Chưa có hoạt động nào gần đây.</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800">Tài liệu mới tải lên</h3>
      </div>
      <ul className="divide-y divide-gray-200">
        {documents.map((doc) => (
          <li key={doc.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 truncate" style={{ maxWidth: '300px' }}>{doc.filename}</p>
                <p className="text-xs text-gray-500" suppressHydrationWarning>{new Date(doc.created_at).toLocaleString('vi-VN')}</p>
              </div>
            </div>
            <div>
              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                doc.status === 'completed' ? 'bg-green-100 text-green-800' :
                doc.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {doc.status}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
