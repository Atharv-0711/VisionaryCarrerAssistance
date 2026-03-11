# System Architecture for Visionary Career Assistance

## Overview
Visionary Career Assistance employs a layered, microservices-inspired architecture to support prioritized features including user authentication, assessment management, mobile optimization, PDF reporting, sentiment analysis refinement, and basic mentor matching. The system is built on a client-server model with React/TypeScript frontend and Flask/Python backend, ensuring scalability, security, and performance.

## Architectural Diagram Description (PlantUML Compatible)

```
@startuml System Architecture Diagram
!define RECTANGLE class

skinparam backgroundColor #FEFEFE
skinparam componentStyle uml2

title Visionary Career Assistance - System Architecture

package "Frontend Layer" as Frontend {
  component [React App] as ReactApp
  component [Authentication UI] as AuthUI
  component [Assessment Dashboard] as Dashboard
  component [Mentor Profiles] as MentorUI
  component [Mobile Responsive UI] as MobileUI
  component [PDF Generator] as PDFGen
}

package "Backend Layer" as Backend {
  component [Flask API Gateway] as APIGateway
  component [Authentication Service] as AuthService
  component [Assessment Service] as AssessmentService
  component [Mentor Matching Service] as MentorService
  component [Vector Similarity Service] as VectorService
  component [Feedback Service] as FeedbackService
  component [Reporting Service] as ReportService
  component [Sentiment Analysis Engine] as SentimentEngine
}

package "Data Layer" as Data {
  database "PostgreSQL" as DB
  component [Redis Cache] as Cache
  component [Vector Store (pgvector)] as VectorStore
}

package "External Services" as External {
  component [OAuth Providers] as OAuth
  component [Email/SMS Service] as Notifications
  component [Analytics Service] as Analytics
}

ReactApp --> APIGateway : HTTPS Requests
AuthUI --> AuthService : Login/Register
Dashboard --> AssessmentService : Save/View Assessments
MentorUI --> MentorService : Match Requests
MobileUI --> ReactApp : Responsive Rendering
PDFGen --> ReportService : Generate Reports
SentimentEngine --> AssessmentService : Analyze Data

APIGateway --> AuthService : Route Auth
APIGateway --> AssessmentService : Route Assessments
APIGateway --> MentorService : Route Matching
APIGateway --> ReportService : Route Reports
APIGateway --> FeedbackService : Route Feedback

AuthService --> DB : User Data CRUD
AssessmentService --> DB : Assessment Data CRUD
MentorService --> DB : Mentor Data CRUD
ReportService --> DB : Report Data CRUD
FeedbackService --> DB : Ratings + Weights

AuthService --> Cache : Session Tokens
AssessmentService --> Cache : Cached Results
MentorService --> Cache : Match Cache
VectorService --> VectorStore : Store/Query Embeddings

APIGateway --> OAuth : Social Login
MentorService --> Notifications : Match Alerts
ReactApp --> Analytics : User Engagement
MentorUI --> FeedbackService : Ratings

MentorService --> VectorService : Profile + Need Embeddings
VectorService --> MentorService : Cosine Similarity Scores
FeedbackService --> MentorService : Weight Adjustments
FeedbackService --> VectorService : Embedding Re-weighting

note right of ReactApp : Mobile-first design\n70% user base
note right of SentimentEngine : Rule-based weighting\nNo AI yet
note right of Cache : Sub-3s load times
@enduml
```

## Component Descriptions

### Frontend Layer (React/TypeScript)
- **React App**: Main application container managing routing and state.
- **Authentication UI**: Handles login, signup, and profile management.
- **Assessment Dashboard**: Displays analysis results, history, and progress tracking.
- **Mentor Profiles**: Interface for browsing and connecting with mentors.
- **Mobile Responsive UI**: Ensures optimal experience on mobile devices (70% priority).
- **PDF Generator**: Client-side PDF creation for downloadable reports.

### Backend Layer (Flask/Python)
- **Flask API Gateway**: Central entry point for all API requests.
- **Authentication Service**: Manages user accounts, JWT tokens, and security.
- **Assessment Service**: Processes survey data, sentiment analysis, and storage.
- **Mentor Matching Service**: Hybrid rule + similarity engine; orchestrates matching.
- **Vector Similarity Service**: Builds embeddings for mentor profiles and user needs; computes cosine similarity; uses pgvector store.
- **Feedback Service**: Collects ratings, updates matching weights, and feeds adjustments back to Mentor/Vector services.
- **Reporting Service**: Generates PDF reports from assessment data.
- **Sentiment Analysis Engine**: Applies refined rules and weighting for insights.

### Data Layer
- **PostgreSQL Database**: Stores users, assessments, mentors, and reports.
- **Vector Store (pgvector)**: Persists embeddings for mentors and user needs.
- **Redis Cache**: Improves performance for sessions and frequent queries.

### External Services
- **OAuth Providers**: Social login integration.
- **Email/SMS Service**: Notifications for mentor matches.
- **Analytics Service**: Tracks user engagement (70% target).

## Data Flows for Prioritized Features
1. **User Authentication + Profiles**: User → AuthUI → AuthService → DB/Cache → JWT Response.
2. **Save + View Past Assessments**: Dashboard → AssessmentService → DB → Cached Results.
3. **Refine UI for Mobile**: MobileUI → ReactApp → Responsive Rendering.
4. **Generate PDF Reports**: PDFGen → ReportService → DB → Download.
5. **Clean Up Sentiment Rules + Weighting**: AssessmentService → SentimentEngine → Analysis.
6. **Smarter Mentor Matching (Hybrid)**:
   - Inference: MentorUI → MentorService → VectorService (embeddings + cosine) → DB (profiles) → Recommendations.
   - Feedback: User Rating → FeedbackService → MentorService/VectorService (auto-adjust weights) → Better future rankings.

## Security and Performance
- **Security**: HTTPS, encryption, input validation, role-based access.
- **Performance**: Caching, optimized queries, mobile optimizations for <3s loads.
- **Scalability**: Local server deployment on Windows/Linux environments for development and production, with traditional web hosting for scalability.

This description can be directly used in PlantUML or similar tools to generate the architecture diagram.
