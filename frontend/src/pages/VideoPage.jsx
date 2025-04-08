import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getVideo } from '../api/api';
import Loading from '../components/common/Loading';
import AnalysisView from '../components/AnalysisView';
import { 
  FaYoutube, 
  FaUser, 
  FaEye, 
  FaCalendarAlt, 
  FaThumbsUp, 
  FaExternalLinkAlt,
  FaInfoCircle,
  FaComments,
  FaClosedCaptioning,
  FaExclamationTriangle,
  FaShieldAlt
} from 'react-icons/fa';
import './VideoPage.css';

const VideoPage = () => {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('title'); // 'title', 'comments', 'transcription'

  useEffect(() => {
    const fetchVideo = async () => {
      try {
        const response = await getVideo(id);
        setVideo(response.video);
        
        // Auto-select the tab with dangerous content, if any
        if (response.video.comment_analysis && response.video.comment_analysis.results.is_dangerous) {
          setActiveTab('comments');
        } else if (
          response.video.transcriptions && 
          response.video.transcriptions.some(t => t.analysis && t.analysis.is_dangerous)
        ) {
          setActiveTab('transcription');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVideo();
  }, [id]);

  if (loading) return <Loading />;
  if (error) return <div className="error-container"><p className="error">Error: {error}</p></div>;
  if (!video) return <div className="error-container"><p>Video not found</p></div>;

  // Check if we have any dangerous content
  const hasDangerousTitle = video.title_analysis && video.title_analysis.results.is_dangerous;
  const hasDangerousComments = video.comment_analysis && video.comment_analysis.results.is_dangerous;
  const hasDangerousTranscription = video.transcriptions && video.transcriptions.some(
    t => t.analysis && t.analysis.is_dangerous
  );
  
  const hasDangerousContent = hasDangerousTitle || hasDangerousComments || hasDangerousTranscription;
  
  // Get highest severity across all analyses
  let highestSeverity = 0;
  if (hasDangerousTitle) {
    highestSeverity = Math.max(highestSeverity, video.title_analysis.highest_severity);
  }
  if (hasDangerousComments) {
    highestSeverity = Math.max(highestSeverity, video.comment_analysis.highest_severity);
  }
  if (hasDangerousTranscription) {
    video.transcriptions.forEach(t => {
      if (t.analysis && t.analysis.is_dangerous) {
        highestSeverity = Math.max(highestSeverity, t.analysis.highest_severity);
      }
    });
  }

  // Helper function to safely get categories from analysis results
  const getCategoriesFromAnalysis = (analysis) => {
    if (!analysis || !analysis.results || !analysis.results.matches) {
      return [];
    }
    
    // With transformer model approach, we get categories from matches object keys
    return Object.keys(analysis.results.matches);
  };

  return (
    <div className="video-page">
      <div className="video-content-wrapper">
        <div className="video-main-content">
          <div className="video-header">
            <div className="video-header-content">
              <h1>{video.title}</h1>
              
              <div className="video-meta">
                <span className="meta-item channel">
                  <FaUser className="meta-icon" />
                  <Link to={`/channels/${video.channel.id}`}>
                    {video.channel.name}
                  </Link>
                </span>
                
                <span className="meta-item views">
                  <FaEye className="meta-icon" />
                  {video.views}
                </span>
                
                <span className="meta-item upload-date">
                  <FaCalendarAlt className="meta-icon" />
                  {video.upload_date}
                </span>
                
                {video.likes && (
                  <span className="meta-item likes">
                    <FaThumbsUp className="meta-icon" />
                    {video.likes}
                  </span>
                )}
                
                <a 
                  href={video.url} 
                  className="meta-item youtube-link" 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <FaYoutube className="meta-icon" />
                  View on YouTube
                  <FaExternalLinkAlt className="external-icon" />
                </a>
              </div>
            </div>
            
            {hasDangerousContent && (
              <div className={`content-warning severity-${highestSeverity}`}>
                <FaExclamationTriangle className="warning-icon" />
                <div className="warning-content">
                  <h3>Potentially Concerning Content Detected</h3>
                  <p>This video contains content that may be flagged as problematic with severity level {highestSeverity}/4.</p>
                </div>
              </div>
            )}
          </div>

          <div className="video-content-grid">
            <div className="video-primary">
              <div className="video-thumbnail-container">
                <div className="video-thumbnail">
                  <img src={video.thumbnail} alt={video.title} />
                  <a 
                    href={video.url} 
                    className="youtube-play-button" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    title="Watch on YouTube"
                  >
                    <FaYoutube className="youtube-icon" />
                  </a>
                </div>
              </div>
              
              {video.description && (
                <div className="video-description">
                  <h3>
                    <FaInfoCircle className="section-icon" />
                    Description
                  </h3>
                  <p>{video.description}</p>
                </div>
              )}
            </div>
            
            <div className="video-analysis-summary">
              <h3 className="analysis-summary-title">
                <FaShieldAlt className="section-icon" />
                Analysis Summary
              </h3>
              
              <div className="analysis-summary-content">
                <div className="analysis-summary-item">
                  <div className="summary-label">Title Analysis</div>
                  <div className={`summary-status ${hasDangerousTitle ? 'danger' : 'safe'}`}>
                    {hasDangerousTitle ? (
                      <>
                        <FaExclamationTriangle className="status-icon" />
                        <span>Issues Detected</span>
                      </>
                    ) : (
                      <>
                        <span className="check-icon">✓</span>
                        <span>No Issues</span>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="analysis-summary-item">
                  <div className="summary-label">Comments Analysis</div>
                  <div className={`summary-status ${hasDangerousComments ? 'danger' : 'safe'}`}>
                    {hasDangerousComments ? (
                      <>
                        <FaExclamationTriangle className="status-icon" />
                        <span>Issues Detected</span>
                      </>
                    ) : (
                      <>
                        <span className="check-icon">✓</span>
                        <span>No Issues</span>
                      </>
                    )}
                  </div>
                </div>
                
                {video.transcriptions && video.transcriptions.length > 0 && (
                  <div className="analysis-summary-item">
                    <div className="summary-label">Transcription Analysis</div>
                    <div className={`summary-status ${hasDangerousTranscription ? 'danger' : 'safe'}`}>
                      {hasDangerousTranscription ? (
                        <>
                          <FaExclamationTriangle className="status-icon" />
                          <span>Issues Detected</span>
                        </>
                      ) : (
                        <>
                          <span className="check-icon">✓</span>
                          <span>No Issues</span>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {hasDangerousContent && (
                <div className="category-summary">
                  <h4>Detected Categories:</h4>
                  <div className="category-tags">
                    {/* Collect all unique categories from matches in all analyses */}
                    {[
                      ...(hasDangerousTitle ? getCategoriesFromAnalysis(video.title_analysis) : []),
                      ...(hasDangerousComments ? getCategoriesFromAnalysis(video.comment_analysis) : []),
                      ...(hasDangerousTranscription 
                          ? video.transcriptions
                              .filter(t => t.analysis && t.analysis.is_dangerous)
                              .flatMap(t => getCategoriesFromAnalysis(t.analysis))
                          : []
                      )
                    ]
                      .filter((value, index, self) => self.indexOf(value) === index) // Remove duplicates
                      .map((category, index) => (
                        <span key={index} className="category-tag">
                          {category.replace(/_/g, ' ')}
                        </span>
                      ))
                    }
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="analysis-detailed">
        <div className="analysis-tabs">
          <div className="tab-buttons">
            <button 
              className={activeTab === 'title' ? 'tab-button active' : 'tab-button'}
              onClick={() => setActiveTab('title')}
            >
              <FaInfoCircle className="tab-icon" />
              Title Analysis
              {hasDangerousTitle && <span className="alert-badge">!</span>}
            </button>
            
            <button 
              className={activeTab === 'comments' ? 'tab-button active' : 'tab-button'}
              onClick={() => setActiveTab('comments')}
            >
              <FaComments className="tab-icon" />
              Comments Analysis
              {hasDangerousComments && <span className="alert-badge">!</span>}
            </button>
            
            {video.transcriptions && video.transcriptions.length > 0 && (
              <button 
                className={activeTab === 'transcription' ? 'tab-button active' : 'tab-button'}
                onClick={() => setActiveTab('transcription')}
              >
                <FaClosedCaptioning className="tab-icon" />
                Transcription Analysis
                {hasDangerousTranscription && <span className="alert-badge">!</span>}
              </button>
            )}
          </div>
          
          <div className="tab-content">
            {activeTab === 'title' && (
              <div className="title-analysis tab-panel">
                <h2>
                  <FaInfoCircle className="panel-icon" />
                  Title Analysis
                </h2>
                {hasDangerousTitle ? (
                  <AnalysisView analysis={video.title_analysis.results} />
                ) : (
                  <div className="safe-content">
                    <span className="safe-icon">✓</span>
                    <span>No issues detected in the title.</span>
                  </div>
                )}
                
                <div className="analysis-context">
                  <h3>Title:</h3>
                  <p className="highlighted-content">"{video.title}"</p>
                </div>
              </div>
            )}
            
            {activeTab === 'comments' && (
              <div className="comments-analysis tab-panel">
                <h2>
                  <FaComments className="panel-icon" />
                  Comments Analysis
                </h2>
                
                {hasDangerousComments ? (
                  <>
                    <AnalysisView analysis={video.comment_analysis.results} />
                    
                    {video.comment_analysis.results.dangerous_comments && (
                      <div className="dangerous-comments">
                        <h3>
                          <FaExclamationTriangle className="section-icon" />
                          Flagged Comments ({video.comment_analysis.results.dangerous_comments.length})
                        </h3>
                        <ul className="comments-list">
                          {video.comment_analysis.results.dangerous_comments.slice(0, 5).map((item, index) => (
                            <li key={index} className="dangerous-comment">
                              <div className="comment-header">
                                <strong className="comment-author">{item.comment_data.author}</strong>
                                {item.comment_data.date && (
                                  <span className="comment-date">{item.comment_data.date}</span>
                                )}
                              </div>
                              <p className="comment-text">{item.comment_data.text}</p>
                              <div className="comment-categories">
                                {/* Updated to get categories from matches in analysis */}
                                {item.analysis && item.analysis.matches ? 
                                  Object.keys(item.analysis.matches).map((category, catIndex) => (
                                    <span key={catIndex} className="comment-category">
                                      {category.replace(/_/g, ' ')}
                                    </span>
                                  )) : null
                                }
                              </div>
                            </li>
                          ))}
                        </ul>
                        
                        {video.comment_analysis.results.dangerous_comments.length > 5 && (
                          <p className="more-comments">
                            And {video.comment_analysis.results.dangerous_comments.length - 5} more flagged comments...
                          </p>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="safe-content">
                    <span className="safe-icon">✓</span>
                    <span>No issues detected in the comments.</span>
                  </div>
                )}
                
                {video.comments && video.comments.length > 0 && (
                  <div className="all-comments">
                    <h3>
                      <FaComments className="section-icon" />
                      Recent Comments ({video.comments.length})
                    </h3>
                    <ul className="comments-list">
                      {video.comments.slice(0, 10).map((comment) => (
                        <li key={comment.id} className="comment">
                          <div className="comment-header">
                            <strong className="comment-author">{comment.author}</strong>
                            {comment.date && (
                              <span className="comment-date">{comment.date}</span>
                            )}
                          </div>
                          <p className="comment-text">{comment.text}</p>
                        </li>
                      ))}
                    </ul>
                    
                    {video.comments.length > 10 && (
                      <p className="more-comments">
                        Showing 10 of {video.comments.length} comments
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'transcription' && video.transcriptions && (
              <div className="transcription-analysis tab-panel">
                <h2>
                  <FaClosedCaptioning className="panel-icon" />
                  Transcription Analysis
                </h2>
                
                {video.transcriptions.length > 0 ? (
                  video.transcriptions.map((transcript, index) => (
                    <div key={index} className="transcription-item">
                      <h3>Transcription #{index + 1}</h3>
                      
                      {transcript.analysis && transcript.analysis.is_dangerous ? (
                        <AnalysisView analysis={transcript.analysis.results} />
                      ) : (
                        <div className="safe-content">
                          <span className="safe-icon">✓</span>
                          <span>No issues detected in this transcription.</span>
                        </div>
                      )}
                      
                      <div className="transcription-text">
                        <h4>Content:</h4>
                        <p>{transcript.text}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No transcriptions available for this video.</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPage;