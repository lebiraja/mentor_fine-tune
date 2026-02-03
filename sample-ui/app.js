/**
 * ClarityMentor Voice UI
 * WebSocket client for voice-to-voice chat with emotion detection
 */

class ClarityMentorUI {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isProcessing = false;
        this.currentTheme = 'dark';

        this.initElements();
        this.setupEventListeners();
        this.connect();
        this.loadTheme();
    }

    initElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.themeToggle = document.getElementById('themeToggle');
        this.newSessionBtn = document.getElementById('newSessionBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.statusText = document.getElementById('statusText');
        this.emotionBadge = document.getElementById('emotionBadge');
        this.spinnerContainer = document.getElementById('spinnerContainer');
        this.processingText = document.getElementById('processingText');
        this.waveform = document.getElementById('waveform');
        this.audioContainer = document.getElementById('audioContainer');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.audioSource = document.getElementById('audioSource');
        this.fileInput = document.getElementById('fileInput');
        this.sessionIdDisplay = document.getElementById('sessionId');
        this.uploadLabel = document.querySelector('.upload-label');
    }

    setupEventListeners() {
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        this.newSessionBtn.addEventListener('click', () => this.createNewSession());
        this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.uploadLabel.addEventListener('click', () => this.fileInput.click());
    }

    // ============ WebSocket ============

    connect() {
        const wsUrl = 'ws://localhost:2323/ws/voice';

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.binaryType = 'arraybuffer';

            this.ws.onopen = () => {
                console.log('Connected to backend');
                this.setStatus('Connected', 'success');
                this.createNewSession();
            };

            this.ws.onmessage = (event) => this.handleMessage(event);

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.setStatus('Connection error', 'error');
            };

            this.ws.onclose = () => {
                console.log('Disconnected from backend');
                this.setStatus('Disconnected', 'error');
                setTimeout(() => this.connect(), 3000);
            };
        } catch (error) {
            console.error('Failed to connect:', error);
            this.setStatus('Connection failed', 'error');
        }
    }

    handleMessage(event) {
        try {
            // Check if it's binary data (audio)
            if (event.data instanceof ArrayBuffer) {
                this.handleAudioResponse(event.data);
                return;
            }

            // Handle JSON messages
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'status':
                    this.processingText.textContent = message.message;
                    break;

                case 'transcript':
                    this.addMessage('user', message.text);
                    this.setStatus('Transcribed', 'success');
                    break;

                case 'emotion':
                    this.handleEmotion(message.data);
                    break;

                case 'response':
                    this.addMessage('assistant', message.text);
                    this.setStatus('Responding', 'success');
                    break;

                case 'error':
                    this.showError(message.message);
                    this.setStatus('Error', 'error');
                    break;

                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    }

    handleAudioResponse(audioData) {
        try {
            // Convert ArrayBuffer to Blob
            const blob = new Blob([audioData], { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);

            // Update audio player
            this.audioSource.src = url;
            this.audioContainer.style.display = 'block';

            // Auto-play
            this.audioPlayer.play().catch(error => {
                console.warn('Audio auto-play failed:', error);
                this.audioPlayer.controls = true;
            });

            this.stopSpinner();
            this.setStatus('Ready', 'success');
        } catch (error) {
            console.error('Error handling audio:', error);
            this.showError('Failed to process audio response');
        }
    }

    handleEmotion(emotionData) {
        const emotion = emotionData.primary_emotion;
        const confidence = (emotionData.confidence * 100).toFixed(0);

        this.emotionBadge.textContent = `${emotion} (${confidence}%)`;
        this.emotionBadge.className = `emotion-badge ${emotion}`;

        // Update background color based on emotion
        this.updateEmotionTheme(emotion);
    }

    updateEmotionTheme(emotion) {
        const emotionColors = {
            neutral: '#64748b',
            joy: '#fbbf24',
            sadness: '#3b82f6',
            anger: '#ef4444',
            fear: '#8b5cf6',
            surprise: '#ec4899',
            confused: '#06b6d4'
        };

        const color = emotionColors[emotion] || emotionColors.neutral;
        document.documentElement.style.setProperty('--emotion-accent', color);
    }

    // ============ Recording ============

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                this.processAudio();
            };

            this.mediaRecorder.start();
            this.isRecording = true;

            this.recordBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.waveform.classList.add('active');

            this.setStatus('Recording...', 'recording');
            console.log('Recording started');
        } catch (error) {
            console.error('Microphone access denied:', error);
            this.showError('Microphone access denied. Please check your browser permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            this.recordBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.waveform.classList.remove('active');

            this.setStatus('Processing...', 'processing');
        }
    }

    processAudio() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        // Convert to WAV for better compatibility
        const reader = new FileReader();
        reader.onload = () => {
            const audioData = reader.result;
            this.sendAudioToBackend(audioData);
        };
        reader.readAsArrayBuffer(audioBlob);
    }

    // ============ File Upload ============

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
            const audioData = reader.result;
            this.sendAudioToBackend(audioData);
        };
        reader.readAsArrayBuffer(file);

        // Reset input
        this.fileInput.value = '';
    }

    // ============ Send Audio ============

    sendAudioToBackend(audioData) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showError('Not connected to backend');
            return;
        }

        try {
            this.showSpinner();
            this.setStatus('Sending audio...', 'processing');

            // Send as binary
            this.ws.send(audioData);

            console.log('Audio sent to backend');
        } catch (error) {
            console.error('Error sending audio:', error);
            this.showError('Failed to send audio to backend');
            this.stopSpinner();
        }
    }

    // ============ UI Updates ============

    addMessage(role, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;

        let htmlContent = `<div class="message-content">${this.escapeHtml(content)}`;

        // Add emotion tag for user messages
        if (role === 'user') {
            const emotionText = this.emotionBadge.textContent;
            if (emotionText && emotionText !== '—') {
                const emotion = emotionText.split('(')[0].trim().toLowerCase();
                htmlContent += `<div class="emotion-tag ${emotion}">${emotionText}</div>`;
            }
        }

        htmlContent += '</div>';
        messageEl.innerHTML = htmlContent;

        this.chatMessages.appendChild(messageEl);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setStatus(text, type = 'info') {
        this.statusText.textContent = text;
        this.statusText.style.color = this.getStatusColor(type);
    }

    getStatusColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            processing: '#f59e0b',
            recording: '#ef4444',
            info: '#6b7280'
        };
        return colors[type] || colors.info;
    }

    showSpinner() {
        this.spinnerContainer.style.display = 'flex';
        this.recordBtn.disabled = true;
        this.stopBtn.disabled = true;
    }

    stopSpinner() {
        this.spinnerContainer.style.display = 'none';
        this.recordBtn.disabled = false;
    }

    showError(message) {
        console.error(message);
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant';
        messageEl.innerHTML = `<div class="message-content" style="color: #ef4444;">⚠️ ${this.escapeHtml(message)}</div>`;
        this.chatMessages.appendChild(messageEl);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============ Session Management ============

    createNewSession() {
        // Clear chat
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <h3>Welcome to ClarityMentor</h3>
                <p>Click the microphone button below to start a conversation</p>
            </div>
        `;

        this.emotionBadge.textContent = '—';
        this.emotionBadge.className = 'emotion-badge';

        // Reset audio
        this.audioContainer.style.display = 'none';
        this.audioPlayer.pause();

        this.setStatus('Ready', 'success');
        console.log('New session started');
    }

    // ============ Theme ============

    toggleTheme() {
        if (this.currentTheme === 'dark') {
            document.body.classList.add('light-theme');
            this.currentTheme = 'light';
            this.themeToggle.textContent = '🌞';
            localStorage.setItem('theme', 'light');
        } else {
            document.body.classList.remove('light-theme');
            this.currentTheme = 'dark';
            this.themeToggle.textContent = '🌙';
            localStorage.setItem('theme', 'dark');
        }
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.currentTheme = savedTheme;

        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
            this.themeToggle.textContent = '🌞';
        } else {
            this.themeToggle.textContent = '🌙';
        }
    }
}

// ============ Initialize ============

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing ClarityMentor UI...');
    window.ui = new ClarityMentorUI();
    console.log('UI initialized');
});
