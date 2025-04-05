import React from 'react';
import { FaShieldAlt, FaCheckCircle } from 'react-icons/fa';
import './AnalysisView.css';

const AnalysisView = ({ analysis }) => {
  // Check if analysis exists and has dangerous content
  if (!analysis || !analysis.is_dangerous) {
    return (
      <div className="no-issues">
        <FaCheckCircle />
        <span>No potentially dangerous content detected.</span>
      </div>
    );
  }

  const getSeverityClass = (severity) => {
    return `severity-${Math.min(severity, 4)}`;
  };

  return (
    <div className="analysis-results">
      <div className="analysis-header">
        <h3>
          <FaShieldAlt /> 
          Content Analysis Results
        </h3>
        <div 
          className={`severity-indicator ${getSeverityClass(analysis.highest_severity)}`}
        >
          Severity: {analysis.highest_severity}/4
        </div>
      </div>
      
      <div className="categories">
        <h4>Detected Categories:</h4>
        <ul className="categories-list">
          {/* Make sure dangerous_categories exists before mapping */}
          {analysis.dangerous_categories && analysis.dangerous_categories.map((category, index) => {
            // Check if matches exists and contains this category
            const matchInfo = analysis.matches && analysis.matches[category];
            
            // If no match info is available, provide fallback values
            const severity = matchInfo ? matchInfo.severity : 1;
            const keywords = matchInfo ? matchInfo.keywords || [] : [];
            const count = matchInfo ? matchInfo.count : 0;
            
            return (
              <li key={index} className="category-item">
                <div className="category-header">
                  <span className="category-name">{category.replace(/_/g, ' ')}</span>
                  <span className={`category-severity ${getSeverityClass(severity)}`}>
                    Severity: {severity}
                  </span>
                </div>
                <div className="keywords-list">
                  {keywords.map((keyword, kidx) => (
                    <span key={kidx} className="keyword">{keyword}</span>
                  ))}
                </div>
                <div className="count">
                  Found {count} {count === 1 ? 'instance' : 'instances'}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};

export default AnalysisView;