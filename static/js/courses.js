// Coursera-style course interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize course cards
    initializeCourseCards();
    
    // Add hover effects
    addHoverEffects();
    
    // Add sorting functionality
    addSortingFunctionality();
    
    // Add view toggle functionality
    addViewToggle();
});

function initializeCourseCards() {
    const courseCards = document.querySelectorAll('.course-card');
    
    courseCards.forEach(card => {
        // Add animation class
        card.classList.add('animated-card');
        
        // Add data attributes for filtering
        const title = card.querySelector('.card-title').textContent.toLowerCase();
        const instructor = card.querySelector('.instructor').textContent.toLowerCase();
        const category = card.dataset.category || 'programming';
        const level = card.dataset.level || 'beginner';
        
        card.dataset.title = title;
        card.dataset.instructor = instructor;
        card.dataset.category = category;
        card.dataset.level = level;
    });
}

function addHoverEffects() {
    const courseCards = document.querySelectorAll('.course-card');
    
    courseCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 15px 30px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)';
        });
    });
}

function addSortingFunctionality() {
    // Sorting dropdown functionality
    const sortDropdown = document.querySelector('.dropdown-menu');
    if (sortDropdown) {
        sortDropdown.addEventListener('click', function(e) {
            if (e.target.classList.contains('dropdown-item')) {
                e.preventDefault();
                const sortBy = e.target.getAttribute('data-sort');
                sortCourses(sortBy);
            }
        });
    }
}

function sortCourses(sortBy) {
    const courseGrid = document.getElementById('coursesGrid');
    const courseCards = Array.from(courseGrid.querySelectorAll('.course-card'));
    
    courseCards.sort((a, b) => {
        switch(sortBy) {
            case 'newest':
                return parseInt(b.dataset.id) - parseInt(a.dataset.id);
            case 'oldest':
                return parseInt(a.dataset.id) - parseInt(b.dataset.id);
            case 'price-low':
                return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
            case 'price-high':
                return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
            case 'title-asc':
                return a.dataset.title.localeCompare(b.dataset.title);
            case 'title-desc':
                return b.dataset.title.localeCompare(a.dataset.title);
            default:
                return 0;
        }
    });
    
    // Re-append sorted cards
    courseCards.forEach(card => courseGrid.appendChild(card));
    
    // Show visual feedback
    showSortFeedback(sortBy);
}

function showSortFeedback(sortBy) {
    // Create temporary feedback element
    const feedback = document.createElement('div');
    feedback.className = 'alert alert-info position-fixed top-0 start-50 translate-middle-x mt-3';
    feedback.style.zIndex = '1000';
    feedback.textContent = `Sorted by: ${sortBy.replace('-', ' ').toUpperCase()}`;
    feedback.style.transition = 'opacity 0.3s';
    
    document.body.appendChild(feedback);
    
    // Remove after 2 seconds
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(feedback);
        }, 300);
    }, 2000);
}

function addViewToggle() {
    const gridViewBtn = document.querySelector('[onclick="toggleView(\'grid\')"]');
    const listViewBtn = document.querySelector('[onclick="toggleView(\'list\')"]');
    
    if (gridViewBtn && listViewBtn) {
        gridViewBtn.addEventListener('click', function() {
            toggleCourseView('grid');
        });
        
        listViewBtn.addEventListener('click', function() {
            toggleCourseView('list');
        });
    }
}

function toggleCourseView(view) {
    const courseCards = document.querySelectorAll('.course-card');
    
    courseCards.forEach(card => {
        const cardElement = card.querySelector('.card');
        
        if (view === 'list') {
            // Convert to list view
            card.classList.remove('col-lg-4', 'col-md-6');
            card.classList.add('col-12');
            cardElement.classList.add('flex-row');
            
            // Adjust image size for list view
            const img = cardElement.querySelector('.card-img-top');
            if (img) {
                img.style.width = '200px';
                img.style.height = '120px';
                img.style.objectFit = 'cover';
            }
        } else {
            // Convert to grid view
            card.classList.remove('col-12');
            card.classList.add('col-lg-4', 'col-md-6');
            cardElement.classList.remove('flex-row');
            
            // Reset image size for grid view
            const img = cardElement.querySelector('.card-img-top');
            if (img) {
                img.style.width = '';
                img.style.height = '160px';
                img.style.objectFit = '';
            }
        }
    });
    
    // Update active button state
    updateViewButtonState(view);
}

function updateViewButtonState(activeView) {
    const gridViewBtn = document.querySelector('[onclick="toggleView(\'grid\')"]');
    const listViewBtn = document.querySelector('[onclick="toggleView(\'list\')"]');
    
    if (activeView === 'grid') {
        gridViewBtn.classList.add('btn-primary');
        gridViewBtn.classList.remove('btn-outline-secondary');
        listViewBtn.classList.add('btn-outline-secondary');
        listViewBtn.classList.remove('btn-primary');
    } else {
        listViewBtn.classList.add('btn-primary');
        listViewBtn.classList.remove('btn-outline-secondary');
        gridViewBtn.classList.add('btn-outline-secondary');
        gridViewBtn.classList.remove('btn-primary');
    }
}

// Enhanced filtering functionality
function filterCourses() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const priceFilter = document.getElementById('priceFilter').value;
    const levelFilter = document.getElementById('levelFilter') ? document.getElementById('levelFilter').value : '';
    
    const courseCards = document.querySelectorAll('.course-card');
    let visibleCount = 0;
    
    courseCards.forEach(card => {
        const title = card.dataset.title || '';
        const instructor = card.dataset.instructor || '';
        const category = card.dataset.category || '';
        const level = card.dataset.level || '';
        const price = parseFloat(card.dataset.price) || 0;
        
        let show = true;
        
        // Search filter
        if (searchTerm && !title.includes(searchTerm) && !instructor.includes(searchTerm)) {
            show = false;
        }
        
        // Category filter
        if (categoryFilter && category !== categoryFilter) {
            show = false;
        }
        
        // Level filter
        if (levelFilter && level !== levelFilter) {
            show = false;
        }
        
        // Price filter
        if (priceFilter) {
            switch(priceFilter) {
                case 'free':
                    if (price > 0) show = false;
                    break;
                case '0-50':
                    if (price < 0 || price > 50) show = false;
                    break;
                case '50-100':
                    if (price < 50 || price > 100) show = false;
                    break;
                case '100-200':
                    if (price < 100 || price > 200) show = false;
                    break;
                case '200+':
                    if (price < 200) show = false;
                    break;
            }
        }
        
        if (show) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Update results count
    const resultsCount = document.getElementById('resultsCount');
    if (resultsCount) {
        resultsCount.textContent = visibleCount;
    }
    
    // Show/hide no results message
    const noResults = document.getElementById('noResults');
    if (noResults) {
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
    
    // Update active filters display
    updateActiveFilters();
}

function updateActiveFilters() {
    const activeFilters = document.getElementById('activeFilters');
    if (!activeFilters) return;
    
    const filters = [];
    
    const searchTerm = document.getElementById('searchInput').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    const priceFilter = document.getElementById('priceFilter').value;
    
    if (searchTerm) filters.push(`Search: "${searchTerm}"`);
    if (categoryFilter) filters.push(`Category: ${categoryFilter}`);
    if (priceFilter) filters.push(`Price: ${priceFilter}`);
    
    if (filters.length > 0) {
        activeFilters.style.display = 'block';
        activeFilters.innerHTML = `
            <div class="d-flex flex-wrap gap-2">
                ${filters.map(filter => `<span class="badge bg-primary">${filter}</span>`).join('')}
                <button class="btn btn-sm btn-outline-danger" onclick="clearFilters()">
                    <i class="fas fa-times me-1"></i>Clear All
                </button>
            </div>
        `;
    } else {
        activeFilters.style.display = 'none';
    }
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('priceFilter').value = '';
    
    if (document.getElementById('levelFilter')) {
        document.getElementById('levelFilter').value = '';
    }
    
    filterCourses();
}

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading animation for buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function() {
        if (this.classList.contains('btn-enroll') || this.classList.contains('btn-continue')) {
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
            this.disabled = true;
        }
    });
});