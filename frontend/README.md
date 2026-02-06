# Fuzzy Friend Frontend

A Next.js 14 application providing the user interface for the Fuzzy Friend pet health triage system.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context API

## Project Structure

```
frontend/
├── app/                        # Next.js App Router pages
│   ├── page.tsx                # Home page
│   ├── layout.tsx              # Root layout
│   ├── auth/page.tsx           # Login/Register page
│   ├── chat/page.tsx           # Chat interface
│   ├── onboarding/page.tsx     # Pet profile setup
│   ├── profile/page.tsx        # User profile
│   ├── settings/page.tsx       # App settings
│   └── community-forum/        # Community features
├── components/                 # Reusable UI components
│   ├── AuthContext.tsx         # Authentication state
│   ├── PetContext.tsx          # Pet profile state
│   ├── TopNav.tsx              # Top navigation bar
│   ├── BottomNav.tsx           # Bottom navigation bar
│   └── chatbot/                # Chat UI components
│       ├── ChatbotModal.tsx    # Main chat modal
│       ├── useCameraCapture.ts # Camera hook
│       └── useSymptomResultsNavigation.ts
├── lib/                        # Utility functions
│   └── api.ts                  # Backend API client
├── public/                     # Static assets
└── .env.local                  # Environment variables
```

## Features

### Pages

| Route | Description |
|-------|-------------|
| `/` | Home page with symptom checker |
| `/auth` | User login and registration |
| `/onboarding` | Pet profile setup wizard |
| `/chat` | AI chat interface |
| `/profile` | User and pet profile management |
| `/settings` | App settings |
| `/community-forum` | Community features |

### Components

- **AuthContext**: Manages user authentication state and JWT tokens
- **PetContext**: Manages pet profile data across the app
- **ChatbotModal**: Full-featured chat interface with:
  - Symptom Checker mode (triage)
  - General Question mode (chat)
  - Image upload support
  - Risk level display

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

Create `.env.local` in the frontend directory:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Integration

The frontend communicates with the backend through `lib/api.ts`:

| Function | Endpoint | Description |
|----------|----------|-------------|
| `healthCheck` | GET /api/health | Check backend status |
| `getCategories` | GET /api/categories | Get symptom categories |
| `sendTriageRequest` | POST /api/triage | Submit triage request |
| `sendChatMessage` | POST /api/chat | Send chat message |
| `register` | POST /api/auth/register | User registration |
| `login` | POST /api/auth/login | User login |
| `savePetProfile` | POST /api/pet-profile | Save pet profile |

## State Management

### Authentication Flow

1. User registers/logs in via `/auth`
2. JWT token stored in localStorage
3. AuthContext provides auth state to all components
4. Protected routes redirect to `/auth` if not authenticated

### Onboarding Flow

1. New users redirected to `/onboarding`
2. User fills pet profile (name, species, breed, age)
3. Profile saved to backend and localStorage
4. User redirected to home page

## Build and Deploy

```bash
# Type check
npx tsc --noEmit

# Build production bundle
npm run build

# Start production server
npm start
```
