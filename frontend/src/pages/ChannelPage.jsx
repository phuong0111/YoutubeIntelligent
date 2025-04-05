import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChannel } from '../api/api';
import Loading from '../components/common/Loading';
import { FaUserAlt, FaExternalLinkAlt, FaInfoCircle, FaVideo, FaExclamationCircle } from 'react-icons/fa';
import './ChannelPage.css'

const ChannelPage = () => {
  const { id } = useParams();
  const [channel, setChannel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChannel = async () => {
      try {
        const response = await getChannel(id);
        setChannel(response.channel);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchChannel();
  }, [id]);

  if (loading) return <Loading />;
  if (error) return <p className="error">Error: {error}</p>;
  if (!channel) return <p>Channel not found</p>;

  // Get first letter of channel name for avatar fallback
  const firstLetter = channel.name ? channel.name.charAt(0).toUpperCase() : 'C';

  return (
    <div className="channel-page">
      <div className="channel-header">
        <div className="channel-header-bg"></div>
        <div className="channel-header-content">
          <div className="channel-profile">
            <div className="channel-avatar large">
              {channel.thumbnail ? (
                <img src={channel.thumbnail} alt={`${channel.name} avatar`} />
              ) : (
                firstLetter
              )}
            </div>
            <div className="channel-title">
              <h1>{channel.name}</h1>
              <div className="channel-meta">
                <div className="meta-item">
                  <FaUserAlt className="meta-icon" />
                  <span className="subscribers">{channel.subscribers}</span>
                </div>
                <div className="meta-item">
                  <span className="channel-id">{channel.channel_id}</span>
                </div>
                <a 
                  href={channel.url} 
                  className="channel-link" 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <FaExternalLinkAlt className="link-icon" />
                  View on YouTube
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {channel.description && (
        <div className="channel-description">
          <h2>
            <FaInfoCircle className="description-icon" />
            Description
          </h2>
          <p>{channel.description}</p>
        </div>
      )}

      <div className="channel-videos">
        <h2>
          <div className="section-title">
            <FaVideo />
            Videos
          </div>
          <div className="videos-count">{channel.videos ? channel.videos.length : 0} videos</div>
        </h2>
        {channel.videos && channel.videos.length > 0 ? (
          <div className="videos-grid">
            {channel.videos.map((video) => (
              <div key={video.id} className="video-card">
                <div className="video-thumbnail">
                  <img src={video.thumbnail} alt={video.title} />
                  {/* Example danger badge, you can add logic to show this based on analysis */}
                  {/* <div className="video-danger-badge">
                    <FaExclamationCircle />
                  </div> */}
                </div>
                <div className="video-content">
                  <h3 className="video-title">{video.title}</h3>
                  <div className="video-meta">
                    <span className="views">{video.views}</span>
                    <span className="upload-date">{video.upload_date}</span>
                  </div>
                  <Link to={`/videos/${video.id}`} className="view-btn">
                    View Analysis
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No videos found for this channel.</p>
        )}
      </div>
    </div>
  );
};

export default ChannelPage;