import React from 'react';

const StatusIndicator = ({ message }) => {
  if (!message) return null;

  return (
    <div className="status-indicator show">
      {message}
    </div>
  );
};

export default StatusIndicator;