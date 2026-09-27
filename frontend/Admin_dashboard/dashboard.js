// ================================================================
// DASHBOARD JAVASCRIPT - PRODUCTION READY
// ================================================================

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    initializeNavigation();
    initializeTopbar();
    initializeCharts();
    updateDateTime();
    initializeInteractions();
});

// ================================================================
// SIDEBAR FUNCTIONALITY (Desktop & Mobile)
// ================================================================

function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const overlay = document.getElementById('sidebarOverlay');
    
    // Desktop: Toggle collapse/expand
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (window.innerWidth > 768) {
                // Desktop: toggle collapse
                sidebar.classList.toggle('collapsed');
                updateSidebarState();
            } else {
                // Mobile: toggle open/close
                sidebar.classList.toggle('active');
                overlay.classList.toggle('active');
                document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : 'auto';
            }
        });
    }

    // Mobile: Close sidebar button
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            closeSidebar();
        });
    }

    // Mobile: Close sidebar on overlay click
    if (overlay) {
        overlay.addEventListener('click', function() {
            closeSidebar();
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = 'auto';
            sidebar.classList.remove('collapsed');
        }
    });

    // Restore sidebar state from localStorage (desktop only)
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    if (sidebarState === 'true' && window.innerWidth > 768) {
        sidebar.classList.add('collapsed');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}

function updateSidebarState() {
    const sidebar = document.getElementById('sidebar');
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed);
}

// ================================================================
// NAVIGATION - WITH MOBILE SIDEBAR FIX
// ================================================================

function initializeNavigation() {
    const routes = {
        dashboard: "dashboard.html",
        "academic-integrity": "academic-integrity.html",
        academic_integrity: "academic-integrity.html",
        "clerk-watchdog": "clerk-watchdog.html",
        clerk_watchdog: "clerk-watchdog.html",
        "exam-monitoring": "exam-monitoring.html",
        exam_monitoring: "exam-monitoring.html",
        "student-management": "student-management.html",
        student_management: "student-management.html",
        "faculty-management": "faculty-management.html",
        Faculty_management: "faculty-management.html",
        "finance-agent": "finance-agent.html",
        finance_agent: "finance-agent.html",
        "hr-administration": "hr-administration.html",
        hr_administration: "hr-administration.html",
        "hostel-agent": "hostel-agent.html",
        hostel_agent: "hostel-agent.html",
        "ai-timetable-creator": "ai-timetable-creator.html",
        ai_timetable_creator: "ai-timetable-creator.html",
        "library-agent": "library-agent.html",
        library_agent: "library-agent.html",
        "security-agent": "security-agent.html",
        security_agent: "security-agent.html",
        "communication-agent": "coming-soon.html?feature=Communication%20Agent",
        "student-services": "coming-soon.html?feature=Student%20Services",
        "admission-agent": "coming-soon.html?feature=Admission%20Agent",
        "it-helpdesk": "coming-soon.html?feature=IT%20Helpdesk",
        "audit-logs": "coming-soon.html?feature=Audit%20Logs",
        "hostel-management": "coming-soon.html?feature=Hostel%20Management",
        "security-operations": "coming-soon.html?feature=Security%20Operations",
        reports: "coming-soon.html?feature=Reports",
        analytics: "coming-soon.html?feature=Analytics",
        settings: "coming-soon.html?feature=Settings",
        support: "coming-soon.html?feature=Support"
    };

    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();

            const page = this.dataset.page;
            const sidebar = document.getElementById('sidebar');
            const isMobile = window.innerWidth <= 768;

            // Handle Logout
            if (page === "logout") {
                if (isMobile) closeSidebar();
                if (confirm("Are you sure you want to logout?")) {
                    window.location.href = "../login_page/admin-login.html";
                }
                return;
            }

            // Set active state
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // On mobile: Close sidebar BEFORE navigating
            if (isMobile && sidebar.classList.contains('active')) {
                closeSidebar();
                // Wait for sidebar animation to complete before navigation
                setTimeout(() => {
                    navigateToPage(page, routes);
                }, 300);
            } else {
                // Desktop: Navigate immediately
                navigateToPage(page, routes);
            }
        });
    });
}

function navigateToPage(page, routes) {
    if (page === "dashboard") {
        window.location.href = "dashboard.html";
    } else if (routes[page]) {
        window.location.href = routes[page];
    }
}

// ================================================================
// TOPBAR FUNCTIONALITY
// ================================================================

function initializeTopbar() {
    // Profile Dropdown
    const profileDropdownBtn = document.getElementById('profileDropdownBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    
    if (profileDropdownBtn && profileDropdown) {
        profileDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.profile-section')) {
                profileDropdown.classList.remove('active');
            }
        });

        // Close dropdown when clicking on dropdown items
        profileDropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                profileDropdown.classList.remove('active');
                console.log('Navigating to:', this.textContent.trim());
            });
        });
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            this.placeholder = 'Type to search...';
        });

        searchInput.addEventListener('blur', function() {
            this.placeholder = 'Search students, staff, courses, documents...';
        });

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });

        // Keyboard shortcut Ctrl+K
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // Notification button
    const notificationBtn = document.querySelector('.notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            showNotification('You have 3 new notifications');
        });
    }

    // Message button
    const messageBtn = document.querySelector('.message-btn');
    if (messageBtn) {
        messageBtn.addEventListener('click', function() {
            showNotification('You have 2 new messages');
        });
    }

    // Theme toggle
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            toggleTheme();
        });

        // Set initial theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            updateThemeIcon();
        }
    }

    // Fullscreen button
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.log('Fullscreen error:', err);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }
}

function performSearch(query) {
    console.log('Searching for:', query);
    // Implement search logic here
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        background-color: #2563EB;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 2000;
        font-size: 14px;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon();
    console.log('Theme switched to:', newTheme);
}

function updateThemeIcon() {
    const sunIcon = document.querySelector('.theme-icon-sun');
    const moonIcon = document.querySelector('.theme-icon-moon');
    const theme = document.documentElement.getAttribute('data-theme') || 'light';
    
    if (theme === 'dark') {
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
    } else {
        sunIcon.style.display = 'block';
        moonIcon.style.display = 'none';
    }
}

// ================================================================
// DATE & TIME UPDATES
// ================================================================

function updateDateTime() {
    const currentDateEl = document.getElementById('currentDate');
    const currentTimeEl = document.getElementById('currentTime');
    const lastUpdateEl = document.getElementById('lastUpdate');

    function updateTime() {
        const now = new Date();
        
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        };
        const dateString = now.toLocaleDateString('en-US', options);
        if (currentDateEl) currentDateEl.textContent = dateString;

        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        if (currentTimeEl) currentTimeEl.textContent = timeString;

        if (lastUpdateEl) {
            lastUpdateEl.textContent = 'Just now';
        }
    }

    updateTime();
    setInterval(updateTime, 30000); // Update every 30 seconds
}

// ================================================================
// CHARTS INITIALIZATION (Chart.js)
// ================================================================

function initializeCharts() {
    // Chart.js default options
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = '#64748B';
    Chart.defaults.borderColor = '#E2E8F0';
    Chart.defaults.plugins.legend.display = true;
    Chart.defaults.plugins.legend.position = 'top';

    // Student Enrollment Trend Chart
    const enrollmentCtx = document.getElementById('enrollmentChart');
    if (enrollmentCtx) {
        new Chart(enrollmentCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Enrollment',
                    data: [1000, 1200, 1400, 1600, 1800, 2100],
                    borderColor: '#2563EB',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#2563EB',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)',
                            drawBorder: false
                        },
                        ticks: {
                            maxTicksLimit: 5
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    // Fee Collection Chart (Bar)
    const feeCtx = document.getElementById('feeChart');
    if (feeCtx) {
        new Chart(feeCtx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Fee Collection (%)',
                    data: [65, 72, 68, 85, 92, 87],
                    backgroundColor: '#10B981',
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)',
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    // AI Agent Activity Chart (Line)
    const activityCtx = document.getElementById('activityChart');
    if (activityCtx) {
        new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'AI Activities',
                    data: [450, 520, 480, 650, 780, 520, 380],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: '#3B82F6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)',
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    // Security Alerts Chart (Bar)
    const securityCtx = document.getElementById('securityChart');
    if (securityCtx) {
        new Chart(securityCtx, {
            type: 'bar',
            data: {
                labels: ['W1', 'W2', 'W3', 'W4'],
                datasets: [{
                    label: 'Security Alerts',
                    data: [28, 18, 15, 12],
                    backgroundColor: '#EF4444',
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)',
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    // Department Distribution (Doughnut)
    const departmentCtx = document.getElementById('departmentChart');
    if (departmentCtx) {
        new Chart(departmentCtx, {
            type: 'doughnut',
            data: {
                labels: ['Engineering', 'Business', 'Arts', 'Science', 'Medicine'],
                datasets: [{
                    data: [420, 380, 280, 220, 150],
                    backgroundColor: [
                        '#2563EB',
                        '#10B981',
                        '#F59E0B',
                        '#8B5CF6',
                        '#EC4899'
                    ],
                    borderColor: '#FFFFFF',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    // Research Publications Chart (Bar)
    const researchCtx = document.getElementById('researchChart');
    if (researchCtx) {
        new Chart(researchCtx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Publications',
                    data: [38, 45, 52, 48, 65, 72],
                    backgroundColor: '#8B5CF6',
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)',
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }
}

// ================================================================
// INTERACTIONS & EFFECTS
// ================================================================

function initializeInteractions() {
    // Add smooth scroll behavior for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Add keyboard navigation for menu items
    document.querySelectorAll('.nav-link').forEach((link, index) => {
        link.addEventListener('keydown', function(e) {
            const allLinks = document.querySelectorAll('.nav-link');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (index < allLinks.length - 1) {
                    allLinks[index + 1].focus();
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (index > 0) {
                    allLinks[index - 1].focus();
                }
            }
        });
    });

    // Add ripple effect to buttons
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: ripple 0.6s ease-out;
            `;

            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// ================================================================
// UTILITY FUNCTIONS
// ================================================================

function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function formatCurrency(num) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(num);
}

// ================================================================
// DARK MODE INITIALIZATION
// ================================================================

if (document.documentElement.getAttribute('data-theme') === 'dark') {
    updateThemeIcon();
}

console.log('✅ Dashboard initialized successfully! (Production Ready)');
