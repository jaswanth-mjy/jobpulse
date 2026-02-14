/* ==========================================
   Onboarding Guide Module
   User Guide with Skippable Steps
   ========================================== */

class OnboardingGuide {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 5;
        this.isCompleted = this.checkOnboardingStatus();
        this.onActionCallback = null;
        
        // Check if user has already completed onboarding
        if (this.isCompleted) {
            console.log("✓ User has already completed onboarding");
        }
    }

    checkOnboardingStatus() {
        const status = localStorage.getItem('jobpulse_onboarding_completed');
        return status === 'true';
    }

    markCompleted() {
        localStorage.setItem('jobpulse_onboarding_completed', 'true');
        this.isCompleted = true;
    }

    resetOnboarding() {
        localStorage.removeItem('jobpulse_onboarding_completed');
        this.isCompleted = false;
        this.currentStep = 0;
    }

    show(onActionCallback) {
        if (this.isCompleted) {
            return; // Don't show if already completed
        }

        this.onActionCallback = onActionCallback;
        this.currentStep = 0;
        this.render();
        this.updateProgress();
        
        const overlay = document.getElementById('onboardingOverlay');
        if (overlay) {
            overlay.classList.add('active');
        }
    }

    hide() {
        const overlay = document.getElementById('onboardingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
    
    dismiss() {
        // Called when user closes without explicitly skipping/completing
        // Mark as completed to prevent showing again
        this.markCompleted();
        this.hide();
    }

    next() {
        if (this.currentStep < this.totalSteps - 1) {
            this.currentStep++;
            this.render();
            this.updateProgress();
        } else {
            this.complete();
        }
    }

    previous() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.render();
            this.updateProgress();
        }
    }

    skip() {
        this.markCompleted();
        this.hide();
        
        // Notify user that tutorial is permanently dismissed
        if (typeof showToast === 'function') {
            showToast('Tutorial skipped. You can restart it anytime from Profile Settings.', 'info');
        }
    }

    complete() {
        this.markCompleted();
        this.hide();
        
        // Show completion notification
        if (typeof showToast === 'function') {
            showToast('🎉 Welcome to JobPulse! You\'re all set to start tracking.', 'success');
        }
    }

    goToStep(stepNumber) {
        if (stepNumber >= 0 && stepNumber < this.totalSteps) {
            this.currentStep = stepNumber;
            this.render();
            this.updateProgress();
        }
    }

    updateProgress() {
        const progressBar = document.querySelector('.onboarding-progress-bar');
        if (progressBar) {
            const progress = ((this.currentStep + 1) / this.totalSteps) * 100;
            progressBar.style.width = `${progress}%`;
        }

        const stepIndicator = document.querySelector('.onboarding-step-indicator');
        if (stepIndicator) {
            stepIndicator.textContent = `Step ${this.currentStep + 1} of ${this.totalSteps}`;
        }
    }

    render() {
        // Hide all steps
        const steps = document.querySelectorAll('.onboarding-step');
        steps.forEach(step => step.classList.remove('active'));

        // Show current step
        const currentStepEl = document.getElementById(`onboarding-step-${this.currentStep}`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
        }

        // Update header
        this.updateStepHeader();
    }

    updateStepHeader() {
        const headers = [
            { title: 'Welcome to JobPulse! 👋', subtitle: 'Your smart job application tracker' },
            { title: 'Add Your First Application 📝', subtitle: 'Get started by tracking your first job' },
            { title: 'Auto-Import from Gmail 📧', subtitle: 'Save time with automatic tracking' },
            { title: 'Explore Your Dashboard 📊', subtitle: 'Understand your job search analytics' },
            { title: 'You\'re All Set! 🚀', subtitle: 'Start tracking smarter today' }
        ];

        const header = headers[this.currentStep];
        const titleEl = document.querySelector('#onboardingOverlay .onboarding-header h2');
        const subtitleEl = document.querySelector('#onboardingOverlay .onboarding-header > p');

        if (titleEl) titleEl.textContent = header.title;
        if (subtitleEl) subtitleEl.textContent = header.subtitle;
    }

    // Action handlers for interactive steps
    triggerAction(action) {
        if (this.onActionCallback) {
            this.onActionCallback(action);
        }
        // Note: Removed auto-proceed to keep tutorial visible
        // Users can manually click 'Next' to continue
    }
}

// Initialize onboarding guide
let onboardingGuide = null;

function initOnboarding() {
    onboardingGuide = new OnboardingGuide();
    return onboardingGuide;
}

function showOnboarding(onActionCallback) {
    if (!onboardingGuide) {
        onboardingGuide = initOnboarding();
    }
    onboardingGuide.show(onActionCallback);
}

function hideOnboarding() {
    if (onboardingGuide) {
        onboardingGuide.dismiss(); // Use dismiss instead of hide to mark as completed
    }
}

function resetOnboarding() {
    // Always clear localStorage first
    localStorage.removeItem('jobpulse_onboarding_completed');
    
    // Reset the instance if it exists
    if (onboardingGuide) {
        onboardingGuide.isCompleted = false;
        onboardingGuide.currentStep = 0;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OnboardingGuide, initOnboarding, showOnboarding, hideOnboarding, resetOnboarding };
}
