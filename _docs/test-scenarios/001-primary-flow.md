# Test Scenario 001 — Primary Lifecycle Workflow

## Target Environments & Live Public URLs (Criterion 8 — 2 Points)

The verification journey can be validated either on the live cloud deployment or locally:
- **Live Public Web Application (Production)**: [https://d1ca9upoitnq9b.cloudfront.net/](https://d1ca9upoitnq9b.cloudfront.net/) *(AWS CloudFront CDN)*
- **Live Public Backend API Health**: [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health) *(AWS Lambda + Neon DB)*
- **Interactive Swagger UI**: [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs)
- **Local Development Environment**: `http://localhost:3003` (via `make up`)

### Pre-Seeded Test Credentials
- **Primary User**: `alex@example.com` (password: `password123`)
- **Collaborator 1**: `sarah@example.com` (password: `password123`)
- **Collaborator 2**: `jordan@example.com` (password: `password123`)
- **Zero-State**: Click "Sign Up" to register any new account.

---

## User Validation Journey

1. **User Registration & Login**: User registers with email and password or logs in with `alex@example.com` / `password123`, receives JWT bearer token.
2. **Item Creation**: User creates a Renewal ("Passport Renewal", due in 60 days), a Maintenance item ("Car Oil Change", due in 15 days), and a Warranty ("MacBook Pro Warranty", due in 365 days).
3. **Dashboard Filtering**: User switches views between All, Renewals, Maintenance, and Warranties; list updates reactively.
4. **Group Collaboration**: User opens group selector, creates group "Home Life" (or selects pre-seeded group), and inspects shared member items.
5. **Shared Item Creation**: Group member creates an item assigned to "Home Life"; item is visible to all members of the group.
6. **Action Summary**: Reminders engine categorizes items into Overdue, Due Soon (<= 30 days), and Normal, rendering clear visual badges.
7. **Completion & Deletion**: User marks an item completed; verifies status changes and item persists in completed view. User triggers morning digest simulator to preview scheduled notification email.
