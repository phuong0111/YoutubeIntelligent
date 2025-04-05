-- Database schema for YouTube content analysis pipeline

-- Channels table to store YouTube channel information
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL UNIQUE,  -- YouTube channel ID or handle (@username)
    channel_name TEXT NOT NULL,
    subscribers TEXT,
    description TEXT,
    thumbnail TEXT,
    url TEXT NOT NULL,
    scrape_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Videos table to store information about YouTube videos
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,  -- YouTube video ID
    channel_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    views TEXT,
    upload_date TEXT,
    likes INTEGER,
    description TEXT,
    thumbnail TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

-- Audio files table to store information about downloaded audio
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    format_type TEXT NOT NULL,
    file_size INTEGER,
    duration REAL,
    download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Transcriptions table to store speech-to-text results
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL,
    transcription_text TEXT NOT NULL,
    language TEXT DEFAULT 'vi',
    success BOOLEAN NOT NULL,
    error_message TEXT,
    transcription_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_id) REFERENCES audio_files(id) ON DELETE CASCADE
);

-- Content analysis table to store dangerous content detection results
CREATE TABLE IF NOT EXISTS content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcription_id INTEGER,  -- Can be NULL for title or comment analysis
    video_id INTEGER,  -- Direct link to video for title or comment analysis
    content_type TEXT DEFAULT 'transcription',  -- 'transcription', 'title', or 'comments'
    is_dangerous BOOLEAN NOT NULL,
    highest_severity INTEGER,
    analysis_results TEXT NOT NULL,  -- JSON with detailed analysis
    analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Analysis categories table to store which dangerous categories were detected
CREATE TABLE IF NOT EXISTS analysis_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    severity INTEGER NOT NULL,
    keywords TEXT NOT NULL,  -- JSON array of matched keywords
    count INTEGER NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES content_analysis(id) ON DELETE CASCADE
);

-- Comments table to store video comments
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    likes TEXT,
    comment_date TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Analysis tasks table to track pipeline processing status
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,  -- 'scrape', 'download', 'transcribe', 'analyze'
    entity_id INTEGER,  -- ID of the related entity (channel, video, audio, etc.)
    entity_type TEXT,  -- Type of the related entity ('channel', 'video', 'audio', etc.)
    status TEXT NOT NULL,  -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for improved query performance
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_video_id ON audio_files(video_id);
CREATE INDEX IF NOT EXISTS idx_transcriptions_audio_id ON transcriptions(audio_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_transcription_id ON content_analysis(transcription_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_video_id ON content_analysis(video_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_content_type ON content_analysis(content_type);
CREATE INDEX IF NOT EXISTS idx_analysis_categories_analysis_id ON analysis_categories(analysis_id);
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_tasks_entity ON tasks(entity_id, entity_type);