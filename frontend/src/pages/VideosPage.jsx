import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getVideos, getDangerousVideos } from '../api/api';
import Loading from '../components/common/Loading';
import './VideosPage.css'

const VideosPage = () => {
  const [videos, setVideos] = useState([]);
  const [dangerousVideos, setDangerousVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'dangerous'

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch all videos
        const videosResponse = await getVideos();
        setVideos(videosResponse.videos);

        // Fetch videos with dangerous content
        const dangerousResponse = await getDangerousVideos();
        setDangerousVideos(dangerousResponse.videos);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <Loading />;
  if (error) return <p className="error">Error: {error}</p>;

  // Get the filtered videos
  const filteredVideos = filter === 'all' 
    ? videos 
    : dangerousVideos;

  // Function to show a badge if a video has dangerous content
  const isDangerous = (videoId) => {
    return dangerousVideos.some(v => v.id === videoId);
  };

  if (!filteredVideos.length) return (
    <div className="videos-page">
      <h1>Videos</h1>
      <div className="filter-controls">
        <button 
          className={filter === 'all' ? 'active' : ''} 
          onClick={() => setFilter('all')}
        >
          All Videos
        </button>
        <button 
          className={filter === 'dangerous' ? 'active' : ''} 
          onClick={() => setFilter('dangerous')}
        >
          Dangerous Content
        </button>
      </div>
      <p>No videos found with the current filter.</p>
    </div>
  );

  return (
    <div className="videos-page">
      <h1>Videos</h1>
      
      <div className="filter-controls">
        <button 
          className={filter === 'all' ? 'active' : ''} 
          onClick={() => setFilter('all')}
        >
          All Videos ({videos.length})
        </button>
        <button 
          className={filter === 'dangerous' ? 'active' : ''} 
          onClick={() => setFilter('dangerous')}
        >
          Dangerous Content ({dangerousVideos.length})
        </button>
      </div>
      
      <div className="videos-grid">
        {filteredVideos.map((video) => (
          <div key={video.id} className="video-card">
            <div className="video-thumbnail">
              <img src={video.thumbnail} alt={video.title} />
              {isDangerous(video.id) && (
                <span className="danger-badge">⚠️</span>
              )}
            </div>
            <h3 className="video-title">{video.title}</h3>
            
            {video.channel_name && (
              <p className="video-channel">{video.channel_name}</p>
            )}
            
            {video.highest_severity && (
              <div 
                className="severity-indicator" 
                data-level={video.highest_severity}
              >
                Severity: {video.highest_severity}/4
              </div>
            )}
            
            <Link to={`/videos/${video.id}`} className="view-btn">
              View Analysis
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VideosPage;