# User Onboarding Guide Feature

## Overview
The JobPulse application now includes an interactive onboarding guide that helps new users get started with the application. The guide walks users through key features with the ability to skip any step or the entire tutorial.

## Features

### ✨ Key Capabilities
- **5-Step Guided Tour**: Welcome → Add Application → Gmail Import → Dashboard Tour → Completion
- **Fully Skippable**: Users can skip individual steps or dismiss the entire tutorial
- **Progress Tracking**: Visual progress bar and step indicators
- **Interactive Actions**: Quick action buttons to perform tasks directly from the guide
- **Persistent State**: Completion status saved in localStorage
- **Responsive Design**: Works beautifully on mobile and desktop
- **Restart Anytime**: Users can replay the tutorial from Profile Settings

## Usage

### For End Users

#### First-Time Experience
1. Sign up or sign in to JobPulse
2. The onboarding guide automatically appears after 800ms
3. Follow the steps or click "Skip tutorial" to dismiss

#### Restarting the Tutorial
1. Click your profile icon in the sidebar
2. Select "Profile Settings"
3. Scroll to "Tutorial & Help" section
4. Click "Restart Tutorial"

#### Navigation Controls
- **Next/Back**: Navigate between steps
- **Skip tutorial**: Dismiss the onboarding entirely
- **Quick Actions**: Perform actions directly from the guide
- **Close (X)**: Exit the tutorial

### For Developers

#### File Structure
```
frontend/
├── css/
│   └── onboarding.css          # Styles for onboarding overlay and components
├── js/
│   ├── onboarding.js           # OnboardingGuide class and logic
│   └── app.js                  # Integration with main app
└── index.html                  # Onboarding HTML structure
```

#### Integration Points

**1. Initialization (app.js)**
```javascript
async function initApp() {
    // ... other initialization
    
    // Show onboarding for first-time users
    setTimeout(() => {
        if (typeof showOnboarding === 'function') {
            showOnboarding(handleOnboardingAction);
        }
    }, 800);
}
```

**2. Action Handlers (app.js)**
```javascript
function handleOnboardingAction(action) {
    switch (action) {
        case 'add-application':
            // Open add application form
            hideOnboarding();
            resetForm();
            setView("add");
            break;
        case 'connect-gmail':
            // Open Gmail connection view
            hideOnboarding();
            setView("gmail");
            break;
    }
}
```

**3. Manual Trigger (app.js)**
```javascript
function restartOnboardingTutorial() {
    hideProfileSettings();
    resetOnboarding();
    showOnboarding(handleOnboardingAction);
}
```

#### Key Classes and Methods

**OnboardingGuide Class**
- `show(callback)` - Display the onboarding guide
- `hide()` - Hide the onboarding overlay
- `next()` - Move to next step
- `previous()` - Move to previous step
- `skip()` - Skip and mark as completed
- `complete()` - Mark as completed and hide
- `triggerAction(action)` - Execute action callback
- `resetOnboarding()` - Clear completion status

**Global Functions**
- `initOnboarding()` - Initialize the guide
- `showOnboarding(callback)` - Show guide with action handler
- `hideOnboarding()` - Hide the guide
- `resetOnboarding()` - Reset completion state

## Onboarding Steps

### Step 1: Welcome (0)
- **Purpose**: Introduce JobPulse and its benefits
- **Features Highlighted**: Auto-import, multi-platform tracking, analytics, follow-ups
- **Actions**: Get Started, Skip tutorial

### Step 2: Add Application (1)
- **Purpose**: Guide user to add their first job application
- **Interactive**: Quick action button to open add form
- **Tips**: What fields to fill, how to add notes and deadlines
- **Actions**: Add Application (quick action), Back, Next, Skip

### Step 3: Gmail Import (2)
- **Purpose**: Explain auto-import from Gmail
- **Interactive**: Quick action button to connect Gmail
- **Benefits**: Privacy, automatic detection, time-saving
- **Actions**: Connect Gmail (quick action), Back, Next, Skip

### Step 4: Dashboard Tour (3)
- **Purpose**: Explain dashboard features
- **Covered**: Analytics, Filters, Search, Quick Edit
- **Actions**: Back, Next, Skip

### Step 5: Completion (4)
- **Purpose**: Congratulate and provide pro tips
- **Tips**: Update statuses, set reminders, run weekly scans
- **Actions**: Start Tracking (completes onboarding), Go Back

## Customization

### Adding New Steps

1. **Update totalSteps in onboarding.js**:
```javascript
this.totalSteps = 6; // Increase count
```

2. **Add header info**:
```javascript
const headers = [
    // ... existing steps
    { title: 'New Step Title', subtitle: 'New step description' }
];
```

3. **Add HTML step in index.html**:
```html
<div class="onboarding-step" id="onboarding-step-5">
    <div class="onboarding-icon">🎨</div>
    <h3>New Step Title</h3>
    <p class="onboarding-step-description">Description...</p>
    <!-- Content and actions -->
</div>
```

### Styling Customization

Edit `frontend/css/onboarding.css`:
- `.onboarding-overlay` - Background overlay
- `.onboarding-card` - Main card container
- `.onboarding-header` - Header with gradient
- `.onboarding-icon` - Step icons
- `.btn-onboarding-primary` - Primary buttons

### Changing Auto-Show Delay

In `app.js`, modify the timeout:
```javascript
setTimeout(() => {
    showOnboarding(handleOnboardingAction);
}, 800); // Change delay in milliseconds
```

### Disabling Auto-Show

Comment out or remove the onboarding call in `initApp()`:
```javascript
async function initApp() {
    // ... other initialization
    
    // setTimeout(() => {
    //     showOnboarding(handleOnboardingAction);
    // }, 800);
}
```

## Storage

### LocalStorage Keys
- `jobpulse_onboarding_completed` - Stores `"true"` when user completes or skips onboarding

### Clearing Onboarding State
```javascript
// Via code
resetOnboarding();

// Via console
localStorage.removeItem('jobpulse_onboarding_completed');
```

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- IE11+ (with polyfills for backdrop-filter)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Responsive Breakpoints
- **Desktop**: Full width (max 600px)
- **Mobile** (<640px): Responsive adjustments, stacked buttons

## Future Enhancements
- [ ] Analytics tracking for step completion rates
- [ ] A/B testing different onboarding flows
- [ ] Video tutorials embedded in steps
- [ ] Contextual help tooltips
- [ ] Multi-language support
- [ ] Keyboard navigation (arrow keys)
- [ ] Accessibility improvements (ARIA labels)

## Support
For issues or questions, please create a GitHub issue or contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: February 13, 2026  
**Branch**: user-onboarding-guide
