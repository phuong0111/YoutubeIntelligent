// api.js
import axios from 'axios';

const API_URL = 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_URL
});

// Channel functions
export const getChannels = async () => {
  const response = await api.get('/channels');
  return response.data;
};

export const getChannel = async (id) => {
  const response = await api.get(`/channels/${id}`);
  return response.data;
};

export const addChannel = async (channelInput, maxVideos = 5, scrapeComments = true) => {
  const response = await api.post('/process/channel', {
    channel_input: channelInput,
    max_videos: maxVideos,
    scrape_comments: scrapeComments
  });
  return response.data;
};

// Video functions
export const getVideos = async () => {
  // No direct endpoint for all videos, we have to get them from channels
  const channelsResponse = await getChannels();
  const videos = [];
  
  for (const channel of channelsResponse.channels) {
    const channelDetail = await getChannel(channel.id);
    videos.push(...channelDetail.channel.videos);
  }
  
  return { status: 'success', videos };
};

export const getVideo = async (id) => {
  const response = await api.get(`/videos/${id}`);
  return response.data;
};

export const addVideo = async (videoUrl, scrapeComments = true) => {
  const response = await api.post('/process/video', {
    video_url: videoUrl,
    scrape_comments: scrapeComments
  });
  return response.data;
};

// Task functions
export const getTasks = async () => {
  const response = await api.get('/tasks');
  return response.data;
};

export const getTask = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data;
};

// Stats functions
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// Dangerous content functions
export const getDangerousVideos = async (contentType = null) => {
  let url = '/analysis/dangerous-videos';
  if (contentType) {
    url += `?content_type=${contentType}`;
  }
  const response = await api.get(url);
  return response.data;
};

export default api;