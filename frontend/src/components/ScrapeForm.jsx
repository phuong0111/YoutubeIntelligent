import React, { useState } from 'react';
import { addChannel, addVideo } from '../api/api';
import { FaYoutube, FaLink, FaComments, FaVideo, FaUser } from 'react-icons/fa';
import './ScrapeForm.css';

const ScrapeForm = () => {
  const [input, setInput] = useState('');
  const [type, setType] = useState('channel');
  const [maxVideos, setMaxVideos] = useState(5);
  const [scrapeComments, setScrapeComments] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    setMessageType('');
    
    try {
      let response;
      if (type === 'channel') {
        response = await addChannel(input, maxVideos, scrapeComments);
      } else {
        response = await addVideo(input, scrapeComments);
      }
      setMessage(`Analysis task started successfully. Task ID: ${response.task_id}`);
      setMessageType('success');
      setInput('');
    } catch (error) {
      setMessage(`Error: ${error.message}`);
      setMessageType('error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="scrape-form card">
      <h2>
        <FaYoutube className="card-icon" />
        Add Content for Analysis
      </h2>
      <form onSubmit={handleSubmit}>
        <div className="radio-group">
          <label className="radio-option">
            <input
              type="radio"
              value="channel"
              checked={type === 'channel'}
              onChange={() => setType('channel')}
            />
            <FaUser className="option-icon" />
            Channel
          </label>
          <label className="radio-option">
            <input
              type="radio"
              value="video"
              checked={type === 'video'}
              onChange={() => setType('video')}
            />
            <FaVideo className="option-icon" />
            Video
          </label>
        </div>
        
        <div className="input-field">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={type === 'channel' ? "Channel URL or @username" : "Video URL"}
            required
          />
          <FaLink className="input-icon" />
        </div>
        
        {type === 'channel' && (
          <div className="number-field">
            <label>
              Maximum Videos:
              <input
                type="number"
                min="1"
                max="50"
                value={maxVideos}
                onChange={(e) => setMaxVideos(Number(e.target.value))}
              />
            </label>
          </div>
        )}
        
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={scrapeComments}
            onChange={(e) => setScrapeComments(e.target.checked)}
          />
          <FaComments className="checkbox-icon" />
          Scrape Comments
        </label>
        
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Start Analysis'}
        </button>
      </form>
      
      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default ScrapeForm;