document.addEventListener('DOMContentLoaded', function () {
    initializeTooltips();
    focusFirstField();
    applyBootstrapValidation();
    setupSignupForm(); // main handler
    autoHideAlerts();
    smoothAnchorScroll();
    handleCourseEnrollment();
    videoLoadLogger();
    simulateProgressBar();
    enableSearchFiltering();
    initializeProgressTracking();
    initHomepageAnimations();
    initCounterAnimations();
});

// ✅ Enable Bootstrap tooltips
function initializeTooltips() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
}

// ✅ Auto-focus first input
function focusFirstField() {
    const form = document.getElementById('signupForm');
    if (!form) return;
    const firstInput = form.querySelector('input:not([type="hidden"]):not([disabled]):not([readonly])');
    if (firstInput) firstInput.focus();
}

// ✅ Bootstrap validation handler
function applyBootstrapValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                console.log("🛑 Bootstrap validation failed.");
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// ✅ Signup form handling (merged all logic)
function setupSignupForm() {
    const form = document.getElementById('signupForm');
    if (!form) return;

    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const submitBtn = document.getElementById('submitBtn');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnText = document.getElementById('btnText');
    const debugMessage = document.getElementById('debugMessage');

    let isSubmitting = false;

    confirmPassword.addEventListener('input', () => {
        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add("is-invalid");
            confirmPassword.setCustomValidity("Passwords do not match");
        } else {
            confirmPassword.classList.remove("is-invalid");
            confirmPassword.setCustomValidity('');
        }
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        debugMessage.classList.remove("d-none");
        debugMessage.textContent = "🔵 Submit triggered...";

        if (isSubmitting) return;

        // Validate form
        if (!form.checkValidity()) {
            form.classList.add("was-validated");
            debugMessage.textContent = "❌ Please correct the form.";
            return;
        }

        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add("is-invalid");
            debugMessage.textContent = "❌ Passwords do not match.";
            return;
        }

        // All checks passed
        isSubmitting = true;
        submitBtn.disabled = true;
        btnSpinner.classList.remove('d-none');
        btnText.textContent = "Creating...";

        debugMessage.textContent = "✅ All good. Submitting to backend...";

        // Submit the form
        form.submit();

        // Optional timeout warning
        setTimeout(() => {
            if (!document.hidden) {
                showNotification("⏳ Signup taking longer than usual. Please wait...", "warning");
            }
        }, 10000);
    });
}

// ✅ Hide alerts automatically
function autoHideAlerts() {
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ✅ Smooth scroll to anchor
function smoothAnchorScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// ✅ Confirm on course enrollment
function handleCourseEnrollment() {
    document.querySelectorAll('form[action*="process_payment"]').forEach(form => {
        form.addEventListener('submit', function (e) {
            const title = this.closest('.card')?.querySelector('.card-title')?.textContent;
            if (title && !confirm(`Are you sure you want to enroll in "${title}"?`)) {
                e.preventDefault();
            }
        });
    });
}

// ✅ Log video iframe loads
function videoLoadLogger() {
    document.querySelectorAll('.video-container iframe').forEach(iframe => {
        iframe.addEventListener('load', function () {
            console.log("🎥 Video loaded:", this.title);
        });
    });
}

// ✅ Simulate progress bar
function simulateProgressBar() {
    const bar = document.querySelector('.progress-bar');
    if (!bar || !document.querySelector('.dashboard-header')) return;

    setTimeout(function update() {
        let current = parseInt(bar.style.width) || 25;
        const next = Math.min(current + 10, 100);
        bar.style.width = `${next}%`;
        bar.textContent = `${next}%`;

        if (next < 100) setTimeout(update, 5000);
    }, 2000);
}

// ✅ Debounced search
function enableSearchFiltering() {
    const searchInput = document.querySelector('input[type="search"]');
    if (!searchInput) return;
    searchInput.addEventListener("input", debounce(handleSearch, 300));
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.card').forEach(card => {
        const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const desc = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
        card.style.display = (title.includes(query) || desc.includes(query)) ? 'block' : 'none';
    });
}

function debounce(func, delay) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

// ✅ Toast-style alert
window.showNotification = function (message, type = 'info') {
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    const container = document.querySelector(".container") || document.body;
    container.insertBefore(alert, container.firstChild);
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 4000);
};

// ✅ Confirmation dialog
window.confirmAction = function (msg, callback) {
    if (confirm(msg)) callback();
};

// ✅ Initialize progress tracking for video modules
function initializeProgressTracking() {
    // This function will be implemented in module_video.html
    // It's included here to avoid errors if called from main.js
}

// ✅ Update progress bar
function updateProgressBar(courseProgress) {
    // This function will be implemented in module_video.html
    // It's included here to avoid errors if called from main.js
}

// ✅ Homepage Animations
function initHomepageAnimations() {
    // Add scroll-triggered animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated--fade-in');
            }
        });
    }, observerOptions);

    // Observe elements that should animate on scroll
    document.querySelectorAll('.feature-card, .course-preview-card, .testimonial-card, .hiw-card, .stat-item').forEach(el => {
        observer.observe(el);
    });

    // Add delay classes for staggered animations
    document.querySelectorAll('.feature-card').forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });

    document.querySelectorAll('.course-preview-card').forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });
}

// ✅ Counter Animations for Stats
function initCounterAnimations() {
    const counters = document.querySelectorAll('.counter');
    
    if (counters.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = +counter.getAttribute('data-target');
                const duration = 2000; // ms
                const step = target / (duration / 16); // 60fps
                
                let current = 0;
                const timer = setInterval(() => {
                    current += step;
                    if (current >= target) {
                        counter.textContent = target.toLocaleString();
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current).toLocaleString();
                    }
                }, 16);
                
                observer.unobserve(counter);
            }
        });
    }, {
        root: null,
        rootMargin: '0px',
        threshold: 0.5
    });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

// ✅ Enhanced button hover effects
document.addEventListener('DOMContentLoaded', function() {
    // Add ripple effect to buttons
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = (e.offsetX - 10) + 'px';
            ripple.style.top = (e.offsetY - 10) + 'px';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Rebuild FAISS Vector Index
document.getElementById("rebuildFaissBtn").addEventListener("click", function () {
    const status = document.getElementById("faissStatus");
    status.style.display = "inline";
    status.textContent = "Rebuilding AI index...";

    fetch("/admin/rebuild-faiss", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    })
    .catch(() => {
        alert("Error rebuilding FAISS index.");
    })
    .finally(() => {
        status.textContent = "Completed!";
        setTimeout(() => { status.style.display = "none"; }, 3000);
    });
});


document.getElementById("uploadDocumentForm")?.addEventListener("submit", async function(e) {
    e.preventDefault();

    // Show uploading status
    const status = document.getElementById("uploadStatus");
    if (status) {
        status.style.display = "block";
        status.textContent = "Uploading & rebuilding AI index...";
    }

    const formData = new FormData(this);
    const response = await fetch("/admin/document/upload", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    alert(result.message);

    if (result.success) location.reload();
});

document.getElementById("uploadDocumentForm")?.addEventListener("submit", async function(e) {
    e.preventDefault();

    // Show uploading status
    const status = document.getElementById("uploadStatus");
    if (status) {
        status.style.display = "block";
        status.textContent = "Uploading & rebuilding AI index...";
    }

    const formData = new FormData(this);
    const response = await fetch("/admin/document/upload", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    alert(result.message);

    if (result.success) location.reload();
});
