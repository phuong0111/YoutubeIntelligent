import React, { useEffect, useState } from 'react';
import ScrapeForm from '../components/ScrapeForm';
import TasksList from '../components/TasksList';
import { getStats } from '../api/api';
import { FaChartLine, FaYoutube, FaVideo, FaExclamationTriangle, FaTasks } from 'react-icons/fa';
import './HomePage.css';

const HomePage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getStats();
        setStats(response.stats);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    
    // Refresh stats every minute
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="home-page">
      <h1>YouTube Content Analysis Dashboard</h1>
      
      <div className="dashboard-grid">
        <div className="scrape-section">
          <ScrapeForm />
        </div>
        
        <div className="stats-section">
          <h2>
            <FaChartLine className="stats-icon" />
            System Statistics
          </h2>
          {loading ? (
            <p>Loading statistics...</p>
          ) : error ? (
            <p className="error">Error loading statistics: {error}</p>
          ) : stats ? (
            <div className="stats-grid">
              <div className="stat-card channels-card">
                <h3>Channels</h3>
                <p className="stat-value">{stats.channels_count}</p>
              </div>
              <div className="stat-card videos-card">
                <h3>Videos</h3>
                <p className="stat-value">{stats.videos_count}</p>
              </div>
              <div className="stat-card dangerous-card">
                <h3>Dangerous Content</h3>
                <p className="stat-value">{stats.dangerous_content_count}</p>
              </div>
              <div className="stat-card tasks-card">
                <h3>Active Tasks</h3>
                <p className="stat-value">{stats.active_tasks}</p>
              </div>
            </div>
          ) : (
            <p>Unable to load statistics</p>
          )}
        </div>
        
        <div className="tasks-section">
          <TasksList limit={5} showViewAll={true} />
        </div>
      </div>
    </div>
  );
};

export default HomePage;