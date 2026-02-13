# JobPulse — Smart Job Application Tracker

<div align="center">

![JobPulse Logo](https://img.shields.io/badge/JobPulse-Smart%20Job%20Tracker-brightgreen)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-blue.svg)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Your Job Search, Organized & Automated**

[Features](#-features) • [Quick Start](#-quick-start) • [Deployment](#-deployment) • [API](#-api-documentation) • [Contributing](#-contributing)

</div>

## 📋 Overview

**JobPulse** is a comprehensive job application tracking system that automatically imports applications from Gmail, tracks status changes, and provides powerful insights into your job search journey. Stop losing track of applications in spreadsheets and start using a purpose-built tracker that works with 30+ job platforms.

### 🎯 Key Highlights

- **🔄 Auto Gmail Import**: Automatically detects and imports job applications from LinkedIn, Naukri, Indeed, Glassdoor, and 25+ platforms
- **📊 Visual Dashboard**: Beautiful charts showing application pipeline, response rates, and weekly trends
- **🔍 Smart Filtering**: Advanced search and filter capabilities by company, role, status, platform, and date
- **☁️ Cloud Synced**: Secure data storage with MongoDB Atlas, accessible from anywhere
- **📱 Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **🔒 Enterprise Security**: JWT authentication, bcrypt password hashing, and user data isolation
- **📤 Data Export/Import**: JSON and CSV export/import functionality for data portability
- **⚡ Real-time Updates**: Live status tracking and automatic email notifications

## 🚀 Features

### Core Functionality
- **Application Management**: Track applications across multiple platforms
- **Status Pipeline**: Applied → Interview → Assessment → Offer → Rejected
- **Company Intelligence**: Automatic company detection and duplicate management
- **Email Integration**: Gmail OAuth with App Password support
- **Visual Analytics**: Charts, graphs, and statistical insights
- **Advanced Search**: Multi-parameter filtering and sorting

### Authentication & Security
- **Dual Sign-in**: Email/password and Google OAuth 2.0
- **Email Verification**: Secure email verification with code generation
- **JWT Tokens**: Stateless authentication with configurable expiry
- **Password Security**: bcrypt hashing with salt rounds
- **User Isolation**: Complete data separation between users

### Supported Platforms
- **Job Boards**: LinkedIn, Naukri, Indeed, Glassdoor, Monster, ZipRecruiter
- **Startup Platforms**: Wellfound, Instahyre, Internshala
- **ATS Systems**: Workday, Greenhouse, Lever, iCIMS, SmartRecruiters
- **Direct Applications**: Company career pages and custom portals

### Mobile Experience
- **Responsive Design**: Optimized for all screen sizes (360px - 1920px)
- **Touch Interactions**: Native mobile gestures and touch feedback
- **Progressive Enhancements**: Offline capabilities and fast loading
- **Safe Area Support**: Full compatibility with notched devices (iPhone X+)

## 🛠 Technology Stack

### Frontend
- **HTML5/CSS3**: Semantic markup with modern CSS Grid and Flexbox
- **Vanilla JavaScript**: No framework dependencies, pure ES6+
- **Google OAuth**: Official Google Sign-In integration
- **Progressive Enhancement**: Mobile-first responsive design

### Backend
- **Flask 3.0.0**: Lightweight Python web framework
- **MongoDB Atlas**: Cloud-native NoSQL database
- **JWT Authentication**: Secure token-based auth
- **Gmail API**: Official Google Gmail integration
- **CORS Support**: Cross-origin resource sharing

### Security & Infrastructure
- **bcrypt**: Industry-standard password hashing
- **python-dotenv**: Environment configuration management
- **Google Auth Libraries**: Official OAuth 2.0 implementation
- **Secure Headers**: CSRF protection and security headers

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8 or higher
- MongoDB Atlas account (free tier available)
- Gmail account for email integration
- Google Cloud Console project for OAuth

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/job-application-tracker.git
cd job-application-tracker
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r ../requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials (see Configuration section)
nano .env
```

### 3. Configuration
Create a `.env` file in the `backend/` directory:

```env
# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/jobpulse?retryWrites=true&w=majority

# Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-characters
JWT_EXPIRY_HOURS=24

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_CLIENT_SECRET=your-oauth-secret

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### 4. Google Cloud Setup
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API and Google+ API
3. Create OAuth 2.0 credentials (Web application)
4. Add your domain to authorized origins
5. Download client configuration

### 5. Start Development Server
```bash
# Start backend (from backend directory)
python app.py

# Serve frontend (from frontend directory)
python -m http.server 3000
```

### 6. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5050

## 🚢 Deployment

### Render.com (Recommended)
JobPulse is optimized for Render.com deployment:

1. **Connect Repository**: Link your GitHub repository to Render
2. **Configure Build**: Use the included `render.yaml` configuration
3. **Environment Variables**: Add all `.env` variables to Render dashboard
4. **Domain Setup**: Configure custom domain and SSL
5. **Auto Deploy**: Automatic deployments on git push to main branch

### Manual Deployment
```bash
# Build and deploy to production
gunicorn --bind 0.0.0.0:$PORT backend.app:app
```

### Environment Variables for Production
Ensure all environment variables from `.env` are configured in your hosting platform:
- Database connection strings
- Google OAuth credentials
- SMTP configuration
- JWT secrets

## 📚 API Documentation

### Authentication Endpoints
```
POST   /api/auth/signup          # User registration
POST   /api/auth/signin          # Email/password login
POST   /api/auth/google          # Google OAuth login
POST   /api/auth/verify-email    # Email verification
GET    /api/auth/profile         # Get user profile
PUT    /api/auth/profile         # Update user profile
```

### Application Management
```
GET    /api/applications         # Get user's applications
POST   /api/applications         # Create new application
PUT    /api/applications/:id     # Update application
DELETE /api/applications/:id     # Delete application
GET    /api/applications/stats   # Get dashboard statistics
```

### Gmail Integration
```
POST   /api/gmail/configure      # Setup Gmail connection
POST   /api/gmail/scan           # Trigger email scan
GET    /api/gmail/scan-status    # Check scan progress
DELETE /api/gmail/disconnect     # Remove Gmail connection
```

### Data Management
```
GET    /api/export              # Export data (JSON/CSV)
POST   /api/import              # Import data
GET    /api/companies           # Get tracked companies
```

### Request/Response Examples

**User Registration**
```json
POST /api/auth/signup
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Application Creation**
```json
POST /api/applications
{
  "company": "Google",
  "role": "Software Engineer",
  "platform": "LinkedIn",
  "status": "Applied",
  "salary": "120000",
  "location": "Mountain View, CA",
  "job_url": "https://...",
  "notes": "Referral from Sarah"
}
```

## 🔒 Security Features

### Data Protection
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Encryption at Rest**: MongoDB Atlas automatic encryption
- **Password Hashing**: bcrypt with configurable rounds
- **Session Management**: Stateless JWT tokens with expiry

### Access Control
- **User Isolation**: Complete data separation between users
- **Authentication Required**: All API endpoints require valid JWT
- **Email Verification**: Account activation through email
- **OAuth Integration**: Secure Google Sign-In implementation

### Privacy Compliance
- **Data Minimization**: Only collect necessary application data
- **User Consent**: Clear privacy policy and terms of service
- **Data Portability**: Full export functionality
- **Account Deletion**: Complete data removal on request

## 🤝 Contributing

We welcome contributions! Please follow these steps:

### Development Setup
```bash
# Fork the repository
git fork https://github.com/yourusername/job-application-tracker.git

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test thoroughly
python -m pytest backend/tests/

# Commit with conventional commit messages
git commit -m "feat: add new dashboard widget"

# Push and create pull request
git push origin feature/your-feature-name
```

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **JavaScript**: Use ES6+ features, no framework dependencies
- **CSS**: Mobile-first responsive design
- **Documentation**: Update README for new features

### Testing
```bash
# Run backend tests
cd backend
python -m pytest tests/

# Test frontend functionality
# Manual testing across different browsers and devices
```

## 📱 Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+
- **Mobile Safari**: iOS 14+
- **Chrome Mobile**: Android 90+

## 👥 Support & Community

- **Issues**: [GitHub Issues](https://github.com/yourusername/job-application-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/job-application-tracker/discussions)
- **Email**: support@jobpulse.dev

## 📊 Project Stats

- **30+ Job Platforms** supported for auto-import
- **100% Mobile Responsive** across all screen sizes
- **MongoDB Atlas** cloud database integration
- **JWT + OAuth** dual authentication system
- **Email Verification** with SMTP integration
- **Real-time Dashboard** with visual analytics

## 🎉 Acknowledgments

- **Google APIs**: Gmail and OAuth integration
- **MongoDB Atlas**: Cloud database hosting
- **Font Awesome**: Icon library
- **Inter Font**: Typography
- **Render.com**: Application hosting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for job seekers everywhere**

[⭐ Star this repo](https://github.com/yourusername/job-application-tracker) if you find it helpful!

</div>

<!-- Deploy trigger Fri Feb 13 17:16:00 IST 2026 -->
