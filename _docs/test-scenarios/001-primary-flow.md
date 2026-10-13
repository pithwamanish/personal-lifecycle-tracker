# Test Scenario 001 — Primary Lifecycle Workflow

## User Validation Journey

1. **User Registration & Login**: User registers with email and password, receives JWT token.
2. **Item Creation**: User creates a Renewal ("Passport Renewal", due in 60 days), a Maintenance item ("Car Oil Change", due in 15 days), and a Warranty ("MacBook Pro Warranty", due in 365 days).
3. **Dashboard Filtering**: User switches views between All, Renewals, Maintenance, and Warranties; list updates instantly.
4. **Group Collaboration**: User creates group "Home Life", invites a collaborator by email.
5. **Shared Item Creation**: Collaborator creates an item assigned to "Home Life".
6. **Action Summary**: Reminders engine categorizes items into Overdue, Due Soon (<= 30 days), and Normal.
7. **Completion & Deletion**: User marks an item completed; verifies status changes and item persists in completed view.
