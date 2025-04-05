import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getChannels } from '../api/api';
import Loading from '../components/common/Loading';
import { FaYoutube } from 'react-icons/fa';
import './ChannelsPage.css'

const ChannelsPage = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const response = await getChannels();
        setChannels(response.channels);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchChannels();
  }, []);

  if (loading) return <Loading />;
  if (error) return <p className="error">Error: {error}</p>;
  if (!channels.length) return <p>No channels found. Add a channel from the dashboard.</p>;

  return (
    <div className="channels-page">
      <div className="channels-header">
        <h1><FaYoutube className="channels-icon" /> YouTube Channels</h1>
        <div className="channels-count">{channels.length} Channels</div>
      </div>
      <div className="channels-grid">
        {channels.map((channel) => {
          // Get first letter of channel name for avatar fallback
          const firstLetter = channel.name ? channel.name.charAt(0).toUpperCase() : 'C';
          
          return (
            <div key={channel.id} className="channel-card">
              <div className="channel-banner"></div>
              <div className="channel-content">
                <div className="channel-avatar">
                  {channel.thumbnail ? (
                    <img src={channel.thumbnail} alt={`${channel.name} avatar`} />
                  ) : (
                    firstLetter
                  )}
                </div>
                <h2>{channel.name}</h2>
                <div className="channel-meta">
                  <span className="subscribers">{channel.subscribers}</span>
                </div>
                <div className="channel-id">{channel.channel_id}</div>
                <div className="channel-actions">
                  <Link to={`/channels/${channel.id}`} className="view-btn">
                    View Details
                  </Link>
                  <a 
                    href={channel.url} 
                    className="external-link" 
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    Open in YouTube
                  </a>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChannelsPage;