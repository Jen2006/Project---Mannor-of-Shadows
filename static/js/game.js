// Enhanced Game Timer
class GameTimer {
    constructor() {
        this.startTime = null;
        this.timerElement = document.getElementById('timer');
        this.intervalId = null;
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) return;
        
        this.startTime = Date.now();
        this.isRunning = true;
        this.intervalId = setInterval(() => this.update(), 1000);
        this.update();
        
        console.log('Game timer started');
    }

    update() {
        if (!this.startTime || !this.isRunning) return;
        
        const elapsed = Date.now() - this.startTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        if (this.timerElement) {
            this.timerElement.textContent = 
                `Time: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            this.isRunning = false;
        }
    }

    getElapsedTime() {
        return this.startTime ? Date.now() - this.startTime : 0;
    }

    formatTime(milliseconds) {
        const hours = Math.floor(milliseconds / 3600000);
        const minutes = Math.floor((milliseconds % 3600000) / 60000);
        const seconds = Math.floor((milliseconds % 60000) / 1000);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Interactive Puzzle Manager
class PuzzleManager {
    constructor() {
        this.currentRoom = this.getCurrentRoom();
        this.initializeRoomSpecificInteractions();
    }

    getCurrentRoom() {
        const path = window.location.pathname;
        if (path.includes('room1')) return 'workshop';
        if (path.includes('room2')) return 'observatory';
        if (path.includes('room3')) return 'laboratory';
        if (path.includes('final')) return 'control';
        return 'entrance';
    }

    initializeRoomSpecificInteractions() {
        console.log(`Initializing interactions for: ${this.currentRoom}`);
        
        switch(this.currentRoom) {
            case 'workshop':
                this.initializeWorkshopInteractions();
                break;
            case 'observatory':
                this.initializeObservatoryInteractions();
                break;
            case 'laboratory':
                this.initializeLaboratoryInteractions();
                break;
            case 'control':
                this.initializeControlInteractions();
                break;
        }
        
        this.initializeCommonInteractions();
    }

    initializeWorkshopInteractions() {
        const selects = document.querySelectorAll('select[name="part_seq"]');
        const partItems = document.querySelectorAll('.part-item');
        
        // Enhanced select interactions
        selects.forEach((select, index) => {
            select.addEventListener('change', function() {
                const selectedValue = this.value;
                
                // Clear duplicate selections
                selects.forEach((otherSelect, otherIndex) => {
                    if (otherIndex !== index && otherSelect.value === selectedValue) {
                        otherSelect.value = '';
                        otherSelect.style.borderColor = '#666';
                        otherSelect.style.background = '';
                    }
                });
                
                // Visual feedback
                if (selectedValue) {
                    this.style.borderColor = '#4caf50';
                    this.style.background = 'rgba(76, 175, 80, 0.1)';
                } else {
                    this.style.borderColor = '#666';
                    this.style.background = '';
                }
                
                updateAssemblyPreview();
            });
        });

        // Clickable part items
        partItems.forEach(item => {
            item.style.cursor = 'pointer';
            item.addEventListener('click', function() {
                const code = this.dataset.code;
                const emptySelect = Array.from(selects).find(select => !select.value);
                if (emptySelect) {
                    emptySelect.value = code;
                    emptySelect.dispatchEvent(new Event('change'));
                    item.classList.add('correct-answer');
                    setTimeout(() => item.classList.remove('correct-answer'), 1000);
                }
            });
        });

        const updateAssemblyPreview = () => {
            const sequence = Array.from(selects).map(select => select.value).filter(val => val);
            const preview = document.getElementById('assembly-preview');
            if (preview) {
                if (sequence.length > 0) {
                    preview.textContent = `Current sequence: ${sequence.join(' → ')}`;
                    preview.style.background = 'rgba(76, 175, 80, 0.1)';
                    preview.style.borderLeft = '3px solid #4caf50';
                } else {
                    preview.textContent = 'Select parts to build sequence';
                    preview.style.background = 'rgba(255, 255, 255, 0.1)';
                    preview.style.borderLeft = '3px solid #666';
                }
            }
        };

        // Initialize preview
        updateAssemblyPreview();
    }

    initializeObservatoryInteractions() {
        const answerInput = document.getElementById('riddle_answer');
        const clueItems = document.querySelectorAll('.clue-item');
        
        if (answerInput) {
            answerInput.addEventListener('input', function() {
                const answer = this.value.toLowerCase().trim();
                if (answer.includes('echo')) {
                    this.style.borderColor = '#4caf50';
                    this.style.background = 'rgba(76, 175, 80, 0.1)';
                } else {
                    this.style.borderColor = '#666';
                    this.style.background = '';
                }
            });
        }

        // Interactive clues
        clueItems.forEach(clue => {
            clue.style.cursor = 'pointer';
            clue.addEventListener('click', function() {
                // Reset all clues
                clueItems.forEach(c => {
                    c.style.background = '';
                    c.style.borderColor = '#444';
                });
                
                // Highlight clicked clue
                this.style.background = 'rgba(76, 175, 80, 0.2)';
                this.style.borderColor = '#4caf50';
                this.style.transform = 'scale(1.02)';
            });
        });
    }

    initializeLaboratoryInteractions() {
        const numberElements = document.querySelectorAll('.number');
        const answerInput = document.getElementById('pattern_answer');
        
        // Animate numbers on hover
        numberElements.forEach(number => {
            number.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1) rotate(5deg)';
                this.style.transition = 'all 0.3s ease';
            });
            
            number.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) rotate(0deg)';
            });
        });

        if (answerInput) {
            answerInput.addEventListener('input', function() {
                const currentPattern = document.querySelector('.sequence-display');
                if (currentPattern) {
                    const numbers = Array.from(currentPattern.querySelectorAll('.number:not(.missing)'))
                        .map(el => parseInt(el.textContent));
                    
                    if (numbers.length >= 2) {
                        const lastNum = numbers[numbers.length - 1];
                        const secondLast = numbers[numbers.length - 2];
                        
                        // Check for common patterns
                        let expectedAnswer = this.detectPattern(numbers);
                        
                        if (expectedAnswer && this.value == expectedAnswer) {
                            this.style.borderColor = '#4caf50';
                            this.style.background = 'rgba(76, 175, 80, 0.1)';
                        } else {
                            this.style.borderColor = '#666';
                            this.style.background = '';
                        }
                    }
                }
            }.bind(this));
        }
    }

    detectPattern(numbers) {
        if (numbers.length < 3) return null;
        
        // Check arithmetic sequence
        const arithmetic = numbers[1] - numbers[0];
        if (numbers.every((num, i, arr) => i === 0 || num - arr[i-1] === arithmetic)) {
            return numbers[numbers.length - 1] + arithmetic;
        }
        
        // Check geometric sequence
        const geometric = numbers[1] / numbers[0];
        if (numbers.every((num, i, arr) => i === 0 || num / arr[i-1] === geometric)) {
            return numbers[numbers.length - 1] * geometric;
        }
        
        // Check Fibonacci-like
        if (numbers.length >= 4) {
            let isFibonacci = true;
            for (let i = 2; i < numbers.length; i++) {
                if (numbers[i] !== numbers[i-2] + numbers[i-1]) {
                    isFibonacci = false;
                    break;
                }
            }
            if (isFibonacci) {
                return numbers[numbers.length - 2] + numbers[numbers.length - 1];
            }
        }
        
        return null;
    }

    initializeControlInteractions() {
        const selects = document.querySelectorAll('.logic-form select');
        
        // Add visual feedback for logic puzzle
        selects.forEach(select => {
            select.addEventListener('change', function() {
                this.validateLogicSelection();
            }.bind(this));
        });

        // Initial validation
        this.validateLogicSelection();
    }

    validateLogicSelection() {
        const selects = document.querySelectorAll('.logic-form select');
        const allSelects = Array.from(selects);
        const values = allSelects.map(s => s.value).filter(v => v);
        const duplicates = values.filter((value, index) => values.indexOf(value) !== index);
        
        allSelects.forEach(select => {
            if (duplicates.includes(select.value) && select.value) {
                select.style.borderColor = '#ff6b6b';
                select.style.background = 'rgba(255, 107, 107, 0.1)';
            } else if (select.value) {
                select.style.borderColor = '#4caf50';
                select.style.background = 'rgba(76, 175, 80, 0.1)';
            } else {
                select.style.borderColor = '#666';
                select.style.background = '';
            }
        });
        
        // Check for completion
        const allFilled = allSelects.every(select => select.value);
        const noDuplicates = new Set(values).size === values.length;
        const submitButton = document.querySelector('.btn-primary');
        
        if (submitButton) {
            if (allFilled && noDuplicates) {
                submitButton.style.background = 'linear-gradient(45deg, #4caf50, #45a049)';
                submitButton.style.cursor = 'pointer';
            } else {
                submitButton.style.background = 'linear-gradient(45deg, rgba(165, 42, 42, 0.9), rgba(205, 92, 92, 0.9))';
            }
        }
    }

    initializeCommonInteractions() {
        // Add loading states to forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitButton = this.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.classList.add('loading');
                    submitButton.disabled = true;
                    submitButton.innerHTML = 'Processing' + submitButton.innerHTML;
                }
            });
        });

        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+S or Cmd+S for quick save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                quickSave();
            }
            
            // Escape key to go back
            if (e.key === 'Escape') {
                if (this.currentRoom !== 'entrance') {
                    if (confirm('Return to main menu? Your progress will be saved.')) {
                        quickSave().then(() => {
                            window.location.href = '/';
                        });
                    }
                }
            }
        });
    }
}

// User Authentication Manager
class AuthManager {
    constructor() {
        this.isLoggedIn = !!localStorage.getItem('userToken');
        this.userData = JSON.parse(localStorage.getItem('userData') || '{}');
        this.updateUI();
    }

    updateUI() {
        const userInfoElement = document.getElementById('user-info');
        const authButtons = document.getElementById('auth-buttons');
        
        if (this.isLoggedIn && userInfoElement) {
            userInfoElement.innerHTML = `
                Welcome, ${this.userData.username}!
                <a href="{{ url_for('logout') }}" class="btn-secondary" style="margin-left: 10px; padding: 5px 10px; font-size: 0.9rem;">
                    Logout
                </a>
            `;
        }
        
        if (authButtons) {
            authButtons.style.display = this.isLoggedIn ? 'none' : 'block';
        }
    }

    login(username, password) {
        // In a real app, this would make an API call
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                if (username && password) {
                    const userToken = 'mock_token_' + Math.random().toString(36).substr(2, 9);
                    const userData = {
                        username: username,
                        loginTime: new Date().toISOString()
                    };
                    
                    localStorage.setItem('userToken', userToken);
                    localStorage.setItem('userData', JSON.stringify(userData));
                    
                    this.isLoggedIn = true;
                    this.userData = userData;
                    this.updateUI();
                    
                    resolve(true);
                } else {
                    reject(new Error('Invalid credentials'));
                }
            }, 1000);
        });
    }

    logout() {
        localStorage.removeItem('userToken');
        localStorage.removeItem('userData');
        this.isLoggedIn = false;
        this.userData = {};
        this.updateUI();
        window.location.href = '/';
    }

    isAuthenticated() {
        return this.isLoggedIn;
    }
}

// Save/Load Manager
class SaveManager {
    static async quickSave() {
        try {
            const response = await fetch('/quick_save');
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Game saved successfully!', 'success');
                return true;
            } else {
                this.showNotification('Save failed: ' + data.message, 'error');
                return false;
            }
        } catch (error) {
            this.showNotification('Save error: ' + error.message, 'error');
            return false;
        }
    }

    static showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotification = document.querySelector('.save-notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `save-notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 5px;
            color: white;
            z-index: 10000;
            font-weight: bold;
            animation: fadeOut 3s forwards;
            background: ${type === 'success' ? 'rgba(76, 175, 80, 0.9)' : 
                         type === 'error' ? 'rgba(244, 67, 54, 0.9)' : 
                         'rgba(33, 150, 243, 0.9)'};
        `;

        document.body.appendChild(notification);

        // Remove after animation
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Global functions for template use
function quickSave() {
    return SaveManager.quickSave();
}

function deleteSave(saveId) {
    if (confirm('Are you sure you want to delete this saved game?')) {
        fetch(`/delete_save/${saveId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                SaveManager.showNotification('Save deleted successfully!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                SaveManager.showNotification('Failed to delete save: ' + data.message, 'error');
            }
        })
        .catch(error => {
            SaveManager.showNotification('Error: ' + error.message, 'error');
        });
    }
}

// Initialize everything when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Manor of Shadow game...');
    
    const timer = new GameTimer();
    const puzzleManager = new PuzzleManager();
    const authManager = new AuthManager();
    
    // Make managers globally available
    window.gameTimer = timer;
    window.puzzleManager = puzzleManager;
    window.authManager = authManager;
    window.SaveManager = SaveManager;
    
    // Start timer if in game room and authenticated
    if (puzzleManager.currentRoom !== 'entrance' && 
        !window.location.pathname.includes('auth') &&
        !sessionStorage.getItem('timerStarted') &&
        authManager.isAuthenticated()) {
        
        timer.start();
        sessionStorage.setItem('timerStarted', 'true');
        console.log('Game timer started for room:', puzzleManager.currentRoom);
    }
    
    // Stop timer on success page
    if (window.location.pathname.includes('success')) {
        timer.stop();
        sessionStorage.removeItem('timerStarted');
    }
    
    // Add auto-save on page unload
    window.addEventListener('beforeunload', function() {
        if (puzzleManager.currentRoom !== 'entrance' && authManager.isAuthenticated()) {
            // Quick save without waiting for response
            fetch('/quick_save').catch(() => {}); // Silent fail
        }
    });
    
    console.log('Game initialization complete');
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('Game error:', e.error);
});

// Export for module use (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GameTimer, PuzzleManager, AuthManager, SaveManager };
}