// Main JavaScript file for Discord Wordle Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Word count for the words textarea
    const wordsTextarea = document.getElementById('words');
    if (wordsTextarea) {
        wordsTextarea.addEventListener('input', function() {
            const words = this.value.split('\n').filter(word => word.trim().length === 5);
            const wordCountElement = document.querySelector('.badge.bg-primary');
            if (wordCountElement) {
                wordCountElement.textContent = words.length;
            }
        });
    }

    // Confirm before submitting forms
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (form.classList.contains('confirm-submit')) {
                if (!confirm('Are you sure you want to save these changes?')) {
                    event.preventDefault();
                }
            }
        });
    });

    // Add active class to current nav item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 