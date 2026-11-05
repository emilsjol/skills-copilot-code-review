# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View database-backed school announcements
- Manage announcements from the header after signing in

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   python -m uvicorn src.app:app --reload
   ```

3. Open your browser and go to:
   - Application: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/auth/login` | Sign in with a JSON body containing `username` and `password`; sets a session cookie |
| GET    | `/auth/check-session` | Return the user identified by the session cookie; otherwise 401 |
| POST   | `/auth/logout` | Revoke the current session and clear its cookie (204) |
| GET    | `/announcements` | Public list of announcements active today, sorted by expiration |
| GET    | `/announcements/manage` | List every announcement, including scheduled and expired; sign-in required |
| POST   | `/announcements` | Create an announcement; sign-in required (201) |
| PUT    | `/announcements/{id}` | Replace an announcement's message and dates; sign-in required |
| DELETE | `/announcements/{id}` | Delete an announcement; sign-in required (204) |

## Announcements

The header's **Announcements** button is available to signed-in teachers. Its dialog
lists all announcements with Active, Scheduled, or Expired status and provides
create, edit, and delete controls. Unsaved changes and deletion require confirmation.
The public noticeboard refreshes after edits, on window focus, and every minute.

Create and update requests use the following JSON structure:

```json
{
   "message": "Registration closes on Friday.",
   "start_date": null,
   "expiration_date": "2026-12-18"
}
```

Messages must contain 1-1000 characters after trimming. `expiration_date` is required;
`start_date` can be omitted or null to publish immediately. Dates use `YYYY-MM-DD`
and UTC calendar days. Both dates are inclusive, and start cannot follow expiration.
Past expiration dates are allowed for archived notices. The public endpoint excludes
future and expired announcements; the management endpoint includes them all.
Announcement text is rendered as plain text, never as HTML.

Invalid payloads return 422, missing or malformed announcement IDs return 404, and
unauthenticated management requests return 401. Database failures are logged on the
server and return a generic 503 response without internal details.

Authentication uses an eight-hour HttpOnly, SameSite=Strict cookie, marked Secure
when served over HTTPS. Only a hash of the session token is stored in MongoDB.
Expired sessions are rejected immediately and removed by a MongoDB TTL index.
Use HTTPS in deployment. Login credentials are sent in the request body, not the URL.

**Authentication API change:** login now requires JSON instead of query parameters,
and checking a session requires its cookie instead of a username. The included
frontend is updated accordingly; existing users must sign in again after upgrading.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

3. **Announcements** - MongoDB-generated identifiers, message, optional start date,
   and required expiration date.

All data is stored in MongoDB at `mongodb://localhost:27017/`, in the
`mergington_high` database. Start MongoDB before launching the application. Run
the installation and server commands above from the repository root.
Initialization seeds empty collections with sample activities, teacher accounts,
and an example announcement expiring 30 days after initialization. Data persists
across server restarts. Session records are stored separately and expire automatically.
