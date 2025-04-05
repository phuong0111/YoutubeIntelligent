import React, { useEffect, useState } from 'react';
import { getTasks, getTask } from '../api/api';
import Loading from '../components/common/Loading';
import './TasksPage.css'

const TasksPage = () => {
  const [tasks, setTasks] = useState({});
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDetails, setTaskDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
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

  useEffect(() => {
    // Fetch task details when a task is selected
    if (selectedTask) {
      const fetchTaskDetails = async () => {
        setDetailsLoading(true);
        try {
          const response = await getTask(selectedTask);
          setTaskDetails(response);
        } catch (err) {
          console.error('Error fetching task details:', err);
        } finally {
          setDetailsLoading(false);
        }
      };

      fetchTaskDetails();
    } else {
      setTaskDetails(null);
    }
  }, [selectedTask]);

  if (loading) return <Loading />;
  if (error) return <p className="error">Error: {error}</p>;

  const taskIds = Object.keys(tasks);
  if (taskIds.length === 0) return <p>No tasks found.</p>;

  // Get completion status counts
  const statusCounts = {
    pending: 0,
    in_progress: 0,
    completed: 0,
    failed: 0
  };

  taskIds.forEach(id => {
    const status = tasks[id].status;
    if (statusCounts.hasOwnProperty(status)) {
      statusCounts[status]++;
    }
  });

  // Sort tasks by newest first
  const sortedTaskIds = taskIds.sort((a, b) => {
    const timeA = new Date(tasks[a].start_time).getTime();
    const timeB = new Date(tasks[b].start_time).getTime();
    return timeB - timeA;
  });

  return (
    <div className="tasks-page">
      <h1>Analysis Tasks</h1>
      
      <div className="task-stats">
        <div className="stat-card">
          <h3>Active</h3>
          <p className="stat-value">{statusCounts.pending + statusCounts.in_progress}</p>
        </div>
        <div className="stat-card">
          <h3>Completed</h3>
          <p className="stat-value">{statusCounts.completed}</p>
        </div>
        <div className="stat-card">
          <h3>Failed</h3>
          <p className="stat-value">{statusCounts.failed}</p>
        </div>
        <div className="stat-card">
          <h3>Total</h3>
          <p className="stat-value">{taskIds.length}</p>
        </div>
      </div>
      
      <div className="tasks-container">
        <div className="tasks-list-container">
          <h2>Task History</h2>
          <table className="tasks-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Started</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedTaskIds.map(taskId => {
                const task = tasks[taskId];
                return (
                  <tr 
                    key={taskId} 
                    className={`task-row status-${task.status} ${selectedTask === taskId ? 'selected' : ''}`}
                  >
                    <td>{taskId.substring(0, 8)}...</td>
                    <td>{task.type}</td>
                    <td>
                      <span className={`status-badge ${task.status}`}>
                        {task.status}
                      </span>
                    </td>
                    <td>{new Date(task.start_time).toLocaleString()}</td>
                    <td>
                      <button 
                        className="details-btn"
                        onClick={() => setSelectedTask(taskId === selectedTask ? null : taskId)}
                      >
                        {taskId === selectedTask ? 'Hide Details' : 'View Details'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {selectedTask && (
          <div className="task-details-panel">
            <h2>Task Details</h2>
            {detailsLoading ? (
              <Loading />
            ) : taskDetails ? (
              <div className="task-details">
                <h3>Task ID: {selectedTask.substring(0, 8)}...</h3>
                <div className="detail-item">
                  <strong>Type:</strong> {taskDetails.task.type}
                </div>
                <div className="detail-item">
                  <strong>Status:</strong> {taskDetails.task.status}
                </div>
                <div className="detail-item">
                  <strong>Started:</strong> {new Date(taskDetails.task.start_time).toLocaleString()}
                </div>
                {taskDetails.task.end_time && (
                  <div className="detail-item">
                    <strong>Completed:</strong> {new Date(taskDetails.task.end_time).toLocaleString()}
                  </div>
                )}
                
                <div className="detail-item">
                  <strong>Parameters:</strong>
                  <pre className="params-json">
                    {JSON.stringify(taskDetails.task.params, null, 2)}
                  </pre>
                </div>
                
                {taskDetails.task.error && (
                  <div className="detail-item error">
                    <strong>Error:</strong>
                    <p>{taskDetails.task.error}</p>
                  </div>
                )}
                
                {taskDetails.results && (
                  <div className="detail-item">
                    <strong>Results:</strong>
                    <pre className="results-json">
                      {JSON.stringify(taskDetails.results, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p>Unable to load task details</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TasksPage;