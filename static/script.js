console.log("Script.js has loaded successfully!");
// EmpowerHub Frontend JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Global state
    let currentUser = null;
    let authToken = localStorage.getItem('authToken');
    
    // Initialize the app
    initApp();
    
    // Navigation event listeners
    // Navigation event listeners - FIXED VERSION
    document.querySelectorAll('.nav-tabs a, a[data-target]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target');
            if (target) {
                showSection(target);
            }
        });
    });
    
    // Authentication event listeners
    document.getElementById('login-form')?.addEventListener('submit', handleLogin);
    document.getElementById('register-form')?.addEventListener('submit', handleRegister);
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
    
    // Feature form event listeners
    document.getElementById('learning-path-form')?.addEventListener('submit', generateLearningPath);
    document.getElementById('qa-form')?.addEventListener('submit', answerQuestion);
    document.getElementById('mental-health-form')?.addEventListener('submit', analyzeMentalHealth);
    document.getElementById('wellness-form')?.addEventListener('submit', trackWellness);
    document.getElementById('health-qa-form')?.addEventListener('submit', answerHealthQuestion);
    document.getElementById('meal-plan-form')?.addEventListener('submit', generateMealPlan);
    document.getElementById('food-waste-form')?.addEventListener('submit', reduceFoodWaste);
    document.getElementById('nutrition-advice-form')?.addEventListener('submit', getNutritionAdvice);
    
    // Initialize the app
    function initApp() {
        if (authToken) {
            // Verify token and load user data
            verifyToken().then(isValid => {
                if (isValid) {
                    showSection('dashboard');
                    loadDashboard();
                } else {
                    showSection('login');
                }
            });
        } else {
            showSection('login');
        }
    }
    
    // Show/hide sections
    function showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Remove active class from all tabs
        document.querySelectorAll('.nav-tabs a').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show the requested section
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            section.classList.add('fade-in');
            
            // Add active class to the corresponding tab
            const tab = document.querySelector(`.nav-tabs a[data-target="${sectionId}"]`);
            if (tab) tab.classList.add('active');
            
            // Load section-specific data
            if (sectionId === 'dashboard') {
                loadDashboard();
            } else if (sectionId === 'education') {
                loadEducationHistory();
            } else if (sectionId === 'health') {
                loadHealthHistory();
            } else if (sectionId === 'nutrition') {
                loadNutritionHistory();
            }
        }
    }
    
    // Add this code RIGHT AFTER your existing showSection function

    // Fix for login/register navigation links
    document.addEventListener('DOMContentLoaded', function() {
        // Handle register link
        const registerLink = document.querySelector('a[data-target="register"]');
        if (registerLink) {
            registerLink.addEventListener('click', function(e) {
                e.preventDefault();
                showSection('register');
            });
        }
        
        // Handle login link  
        const loginLink = document.querySelector('a[data-target="login"]');
        if (loginLink) {
            loginLink.addEventListener('click', function(e) {
                e.preventDefault();
                showSection('login');
            });
        }
    });

    // API call function
    async function apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (authToken) {
            defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const finalOptions = { ...defaultOptions, ...options };
        
        if (finalOptions.body && typeof finalOptions.body !== 'string') {
            finalOptions.body = JSON.stringify(finalOptions.body);
        }
        
        try {
            const response = await fetch(`/api${endpoint}`, finalOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API call error:', error);
            showAlert('error', error.message || 'An error occurred');
            throw error;
        }
    }
    
    // Show alert message
    function showAlert(type, message) {
        // Remove any existing alerts
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        // Add to page
        const container = document.querySelector('.app-container');
        container.insertBefore(alert, container.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    // Verify authentication token
    async function verifyToken() {
        try {
            const response = await apiCall('/user-dashboard', { method: 'GET' });
            currentUser = response.dashboard.user_info;
            updateUIForAuthState(true);
            return true;
        } catch (error) {
            localStorage.removeItem('authToken');
            authToken = null;
            updateUIForAuthState(false);
            return false;
        }
    }
    
    // Update UI based on authentication state
    function updateUIForAuthState(isAuthenticated) {
        const authSections = document.getElementById('auth-sections');
        const unauthSections = document.getElementById('unauth-sections');
        const userInfo = document.getElementById('user-info');
        
        if (isAuthenticated) {
            if (authSections) authSections.style.display = 'flex';
            if (unauthSections) unauthSections.style.display = 'none';
            if (userInfo && currentUser) {
                userInfo.textContent = currentUser.email;
                if (currentUser.is_premium) {
                    userInfo.innerHTML += ' <span class="premium-badge">PREMIUM</span>';
                }
            }
        } else {
            if (authSections) authSections.style.display = 'none';
            if (unauthSections) unauthSections.style.display = 'flex';
            if (userInfo) userInfo.textContent = '';
        }
    }
    
    // Handle login
    async function handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const credentials = {
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        try {
            const response = await apiCall('/login', {
                method: 'POST',
                body: credentials
            });
            
            authToken = response.token;
            localStorage.setItem('authToken', authToken);
            currentUser = { email: credentials.email, is_premium: response.is_premium };
            
            showAlert('success', 'Login successful!');
            showSection('dashboard');
            loadDashboard();
            updateUIForAuthState(true);
        } catch (error) {
            showAlert('error', error.message);
        }
    }
    
    // Handle registration
    async function handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const userData = {
            email: formData.get('email'),
            password: formData.get('password'),
            phone: formData.get('phone')
        };
        
        try {
            const response = await apiCall('/register', {
                method: 'POST',
                body: userData
            });
            
            showAlert('success', 'Registration successful! Please login.');
            showSection('login');
        } catch (error) {
            showAlert('error', error.message);
        }
    }
    
    // Handle logout
    function handleLogout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('authToken');
        updateUIForAuthState(false);
        showSection('login');
        showAlert('info', 'You have been logged out.');
    }
    
    // Load dashboard data
    async function loadDashboard() {
        try {
            const response = await apiCall('/user-dashboard');
            const dashboard = response.dashboard;
            
            // Update stats
            document.getElementById('learning-count').textContent = dashboard.activity_counts.learning_activities;
            document.getElementById('health-count').textContent = dashboard.activity_counts.health_tracking;
            document.getElementById('nutrition-count').textContent = dashboard.activity_counts.meal_plans;
            document.getElementById('waste-count').textContent = dashboard.activity_counts.waste_reduction;
            
            // Update wellness score
            document.getElementById('wellness-score').textContent = `${dashboard.wellness_score}%`;
            document.getElementById('wellness-progress').style.width = `${dashboard.wellness_score}%`;
            
            // Update SDG progress
            updateProgressBar('education-progress', dashboard.sdg_progress.education.average_progress);
            updateProgressBar('health-progress', dashboard.sdg_progress.health.average_score);
            updateProgressBar('nutrition-progress', dashboard.sdg_progress.nutrition.average_nutrition_score);
            
            // Populate recent activities
            populateRecentActivities(dashboard.recent_activities, 'recent-learning');
            populateRecentActivities(dashboard.recent_health, 'recent-health');
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }
    
    // Update progress bar
    function updateProgressBar(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = `${value}%`;
            element.textContent = `${Math.round(value)}%`;
        }
    }
    
    // Populate recent activities
    function populateRecentActivities(activities, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent activities</p>';
            return;
        }
        
        activities.forEach(activity => {
            const activityEl = document.createElement('div');
            activityEl.className = 'activity-item';
            activityEl.innerHTML = `
                <strong>${activity.topic || activity.type}</strong>
                <span class="float-right">${activity.score || activity.progress}%</span>
                <br>
                <small class="text-muted">${new Date(activity.date).toLocaleDateString()}</small>
            `;
            container.appendChild(activityEl);
        });
    }
    
    // Generate learning path
    async function generateLearningPath(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            topic: formData.get('topic'),
            level: formData.get('level')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Generating...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/generate-learning-path', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('learning-path-result').innerHTML = `
                <h4>Your Learning Path for "${data.topic}"</h4>
                <div class="learning-path-content">${formatLearningPath(response.learning_path)}</div>
            `;
            
            showAlert('success', 'Learning path generated successfully!');
            e.target.reset();
            loadEducationHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Format learning path text
    function formatLearningPath(text) {
        // Convert line breaks to HTML
        return text.replace(/\n/g, '<br>');
    }
    
    // Answer question
    async function answerQuestion(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            question: formData.get('question'),
            context: formData.get('context') || 'General knowledge and educational content.'
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Thinking...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/answer-question', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('qa-result').innerHTML = `
                <div class="question">${data.question}</div>
                <div class="answer">${response.answer}</div>
                <div class="confidence">Confidence: ${response.confidence}%</div>
            `;
            
            showAlert('success', 'Answer generated successfully!');
            e.target.reset();
            loadEducationHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Analyze mental health
    async function analyzeMentalHealth(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            mood_text: formData.get('mood_text')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Analyzing...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/analyze-mental-health', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('mental-health-result').innerHTML = `
                <h4>Analysis Results</h4>
                <div class="sentiment">Sentiment: ${response.sentiment}</div>
                <div class="confidence">Confidence: ${response.confidence}%</div>
                <div class="mood-score">Mood Score: ${response.mood_score}/100</div>
                <h5>Recommendations:</h5>
                <ul>
                    ${response.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            `;
            
            showAlert('success', 'Mental health analysis completed!');
            e.target.reset();
            loadHealthHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Track wellness
    async function trackWellness(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            sleep_hours: parseFloat(formData.get('sleep_hours')),
            exercise_minutes: parseFloat(formData.get('exercise_minutes')),
            water_glasses: parseFloat(formData.get('water_glasses'))
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Tracking...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/track-wellness', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('wellness-result').innerHTML = `
                <h4>Wellness Tracking Results</h4>
                <div class="wellness-score">Overall Score: ${response.wellness_score}/100</div>
                <div class="breakdown">
                    <div>Sleep: ${response.breakdown.sleep_score}%</div>
                    <div>Exercise: ${response.breakdown.exercise_score}%</div>
                    <div>Hydration: ${response.breakdown.water_score}%</div>
                </div>
                <h5>Recommendations:</h5>
                <ul>
                    ${response.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            `;
            
            showAlert('success', 'Wellness tracked successfully!');
            e.target.reset();
            loadHealthHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Answer health question
    async function answerHealthQuestion(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            question: formData.get('question')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Researching...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/health-question', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('health-qa-result').innerHTML = `
                <div class="question">${data.question}</div>
                <div class="answer">${response.answer}</div>
                <div class="disclaimer">${response.disclaimer}</div>
            `;
            
            showAlert('success', 'Health information retrieved!');
            e.target.reset();
            loadHealthHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Generate meal plan
    async function generateMealPlan(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            ingredients: formData.get('ingredients'),
            dietary_restrictions: formData.get('dietary_restrictions')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Planning meals...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/generate-meal-plan', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('meal-plan-result').innerHTML = `
                <h4>Your Meal Plan</h4>
                <div class="nutrition-score">Nutrition Score: ${response.nutrition_score}/100</div>
                <div class="meal-plan-content">${formatMealPlan(response.meal_plan)}</div>
            `;
            
            showAlert('success', 'Meal plan generated successfully!');
            e.target.reset();
            loadNutritionHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Format meal plan text
    function formatMealPlan(text) {
        // Convert line breaks to HTML
        return text.replace(/\n/g, '<br>');
    }
    
    // Reduce food waste
    async function reduceFoodWaste(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            expiring_items: formData.get('expiring_items')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Finding solutions...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/reduce-food-waste', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('food-waste-result').innerHTML = `
                <h4>Food Waste Reduction Ideas</h4>
                <div class="impact-score">Impact Score: ${response.impact_score}/100</div>
                <div class="items-saved">Items Saved: ${response.items_saved}</div>
                <div class="environmental-impact">${response.environmental_impact}</div>
                <div class="suggestions">${formatFoodWasteSuggestions(response.suggestions)}</div>
            `;
            
            showAlert('success', 'Food waste reduction ideas generated!');
            e.target.reset();
            loadNutritionHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Format food waste suggestions
    function formatFoodWasteSuggestions(text) {
        // Convert line breaks to HTML
        return text.replace(/\n/g, '<br>');
    }
    
    // Get nutrition advice
    async function getNutritionAdvice(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            question: formData.get('question')
        };
        
        const button = e.target.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        button.textContent = 'Researching...';
        button.disabled = true;
        
        try {
            const response = await apiCall('/nutrition-advice', {
                method: 'POST',
                body: data
            });
            
            document.getElementById('nutrition-advice-result').innerHTML = `
                <div class="question">${data.question}</div>
                <div class="advice">${response.advice}</div>
                <div class="disclaimer">${response.disclaimer}</div>
            `;
            
            showAlert('success', 'Nutrition advice retrieved!');
            e.target.reset();
            loadNutritionHistory();
        } catch (error) {
            showAlert('error', error.message);
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Load education history
    async function loadEducationHistory() {
        try {
            const response = await apiCall('/user-history/education');
            const container = document.getElementById('education-history');
            
            if (response.history.length === 0) {
                container.innerHTML = '<p class="text-muted">No education history yet</p>';
                return;
            }
            
            container.innerHTML = '';
            response.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <div class="question">${item.question}</div>
                    <div class="answer">${item.answer}</div>
                    <div class="meta">
                        <span class="confidence">${item.confidence}% confidence</span>
                        <span class="date">${new Date(item.date).toLocaleDateString()}</span>
                    </div>
                `;
                container.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Failed to load education history:', error);
        }
    }
    
    // Load health history
    async function loadHealthHistory() {
        try {
            const response = await apiCall('/user-history/health');
            const container = document.getElementById('health-history');
            
            if (response.history.length === 0) {
                container.innerHTML = '<p class="text-muted">No health history yet</p>';
                return;
            }
            
            container.innerHTML = '';
            response.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <div class="type">${item.type}</div>
                    <div class="score">Score: ${item.score}%</div>
                    <div class="date">${new Date(item.date).toLocaleDateString()}</div>
                `;
                container.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Failed to load health history:', error);
        }
    }
    
    // Load nutrition history
    async function loadNutritionHistory() {
        try {
            const response = await apiCall('/user-history/nutrition');
            const container = document.getElementById('nutrition-history');
            
            if (response.history.length === 0) {
                container.innerHTML = '<p class="text-muted">No nutrition history yet</p>';
                return;
            }
            
            container.innerHTML = '';
            response.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <div class="ingredients">${item.ingredients}</div>
                    <div class="score">Nutrition Score: ${item.nutrition_score}%</div>
                    <div class="date">${new Date(item.date).toLocaleDateString()}</div>
                `;
                container.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Failed to load nutrition history:', error);
        }
    }
});