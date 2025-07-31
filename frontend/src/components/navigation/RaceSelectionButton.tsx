'use client';

import React, { useState } from 'react';
import { Calendar, X } from 'lucide-react';
import RaceSelectionHub from '../race/RaceSelectionHub';

const RaceSelectionButton: React.FC = () => {
  const [showRaceSelection, setShowRaceSelection] = useState(false);

  return (
    <>
      {/* レース選択ボタン */}
      <button
        onClick={() => setShowRaceSelection(true)}
        className="flex items-center px-4 py-2 text-gray-700 hover:text-blue-600 transition-colors font-medium"
      >
        <Calendar className="w-5 h-5 mr-2" />
        レース選択
      </button>

      {/* モーダル表示 */}
      {showRaceSelection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg max-w-7xl w-full max-h-[95vh] overflow-auto mx-4">
            <div className="p-4 border-b flex justify-between items-center bg-white sticky top-0 z-10">
              <h2 className="text-xl font-semibold">レース選択</h2>
              <button
                onClick={() => setShowRaceSelection(false)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <RaceSelectionHub />
          </div>
        </div>
      )}
    </>
  );
};

export default RaceSelectionButton; 