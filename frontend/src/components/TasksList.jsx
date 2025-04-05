import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getTasks } from '../api/api';
import { FaTasks, FaSpinner, FaCheck, FaExclamationTriangle, FaClock, FaVideo, FaUser } from 'react-icons/fa';
import './TasksList.css';

const TasksList = ({ limit = null, showViewAll = false }) => {
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await getTasks();
        setTasks(response.tasks);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
    
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="tasks-list">
        <h2>
          <FaTasks className="task-icon" /> Analysis Tasks
        </h2>
        <div className="loading">
          <FaSpinner className="loading-icon spin" />
          <p>Loading tasks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tasks-list">
        <h2>
          <FaTasks className="task-icon" /> Analysis Tasks
        </h2>
        <div className="error">
          <FaExclamationTriangle className="error-icon" />
          <p>Error loading tasks: {error}</p>
        </div>
      </div>
    );
  }

  const taskIds = Object.keys(tasks);
  if (taskIds.length === 0) {
    return (
      <div className="tasks-list">
        <h2>
          <FaTasks className="task-icon" /> Analysis Tasks
        </h2>
        <div className="no-tasks">
          <div className="no-tasks-icon">🔍</div>
          <p>No tasks found. Add a channel or video to analyze.</p>
        </div>
      </div>
    );
  }

  // Sort tasks by time (newest first)
  const sortedTaskIds = taskIds.sort((a, b) => {
    const timeA = new Date(tasks[a].start_time).getTime();
    const timeB = new Date(tasks[b].start_time).getTime();
    return timeB - timeA;
  });

  // Apply limit if specified
  const displayTaskIds = limit ? sortedTaskIds.slice(0, limit) : sortedTaskIds;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <FaClock />;
      case 'in_progress':
        return <FaSpinner className="spin" />;
      case 'completed':
        return <FaCheck />;
      case 'failed':
        return <FaExclamationTriangle />;
      default:
        return null;
    }
  };

  const getTypeIcon = (type) => {
    return type === 'channel' ? <FaUser /> : <FaVideo />;
  };

  return (
    <div className="tasks-list">
      <h2>
        <FaTasks className="task-icon" /> Analysis Tasks
      </h2>
      <table>
        <thead>
          <tr>
            <th>Task ID</th>
            <th>Type</th>
            <th>Status</th>
            <th>Started</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {displayTaskIds.map(taskId => {
            const task = tasks[taskId];
            return (
              <tr key={taskId} className={`task-row status-${task.status}`}>
                <td className="task-id">{taskId.substring(0, 8)}...</td>
                <td className="task-type">
                  {getTypeIcon(task.type)} {task.type}
                </td>
                <td>
                  <span className={`status-badge ${task.status}`}>
                    {getStatusIcon(task.status)} {task.status}
                  </span>
                </td>
                <td className="task-time">
                  {new Date(task.start_time).toLocaleString()}
                </td>
                <td className="task-details">
                  {task.type === 'channel' && (
                    <span title={task.params.channel_input}>
                      Channel: {task.params.channel_input.length > 25 
                        ? `${task.params.channel_input.substring(0, 25)}...`
                        : task.params.channel_input}
                    </span>
                  )}
                  {task.type === 'video' && (
                    <span title={task.params.video_url}>
                      Video: {task.params.video_url.length > 25 
                        ? `${task.params.video_url.substring(0, 25)}...` 
                        : task.params.video_url}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {showViewAll && limit && taskIds.length > limit && (
        <div className="view-all-tasks">
          <Link to="/tasks" className="view-all-link">
            View all {taskIds.length} tasks
          </Link>
        </div>
      )}
    </div>
  );
};

export default TasksList;