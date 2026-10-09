# Personal Lifecycle Tracker --- MVP Scope Brainstorm

**Status:** Working scope draft\
**Purpose:** Consolidate decisions made during brainstorming. This is
not yet a final technical specification.\
**MVP lifecycle types:** Renewals, Maintenance, Warranties

## 1. Product Goal

Build a Personal Lifecycle Tracker for multiple independent users and
groups. It helps people track important lifecycle items, see upcoming
and overdue actions, and receive reminders.

The MVP is limited to three lifecycle types:

1.  **Renewals** --- e.g., insurance, passport, licence, membership
2.  **Maintenance** --- e.g., car, AC, appliance, home
3.  **Warranties** --- e.g., electronics and appliances

## 2. Consolidated MVP Scope

### Accounts and users

-   Support multiple independent users.
-   Users sign up and log in using **email and password**.
-   Each user can create and belong to groups.
-   No Google sign-in is included in the chosen scope.

### Groups and shared access

-   Any user can create a group and invite members by email.
-   Group access model: **owner and members with shared access**.
-   All group members can create, edit, and complete shared lifecycle
    items.
-   Group membership and item permissions are otherwise intentionally
    simple.
-   Shared group items remain with the group when a member leaves or is
    removed.
-   No external sharing of individual items is supported.

### Lifecycle items

-   Only three lifecycle types are in scope: **Renewals, Maintenance,
    and Warranties**.
-   Use **common fields only**; no type-specific or user-customizable
    fields in the MVP.
-   The selected common fields are:
    -   **Name**
    -   **Lifecycle type**
    -   **Due date** (optional)
    -   **Status**
-   Dates are entered manually.
-   Missing due dates are allowed.
-   Items are created through a guided form where the user first selects
    a lifecycle type.
-   Items are organized into basic lists by lifecycle type.
-   No item assignment or responsible-person field.
-   No attachments or document uploads.
-   No external sharing.

### Status, completion, and deletion

-   Completed items are retained and remain visible in the main list
    alongside other items.
-   Overdue items remain overdue until manually completed.
-   No recurring schedules are included in the MVP, despite the earlier
    selection of manual date entry with recurring schedules. The later
    explicit decision was **no recurring schedules in MVP**.
-   Item deletion is permanent.
-   No activity history is included.
-   Account deletion removes everything associated with the account,
    including its group items.
-   Deleting a group deletes the group and all its shared items.

### Dashboard and navigation

-   The dashboard prioritizes **upcoming actions and overdue items**.
-   Basic lists are separated by lifecycle type.
-   No advanced search, filters, custom tags, folders, calendar, or
    analytics were selected for the MVP.

### Reminders and email

-   Support both in-app and email reminders.
-   Reminder schedule is fixed and identical for everyone.
-   Both reminder channels are always enabled; users cannot disable
    either channel.
-   No snooze functionality.
-   Email delivery uses a **daily scheduled digest**, rather than a
    separate email for each reminder event.
-   The digest contains **upcoming and overdue items**.
-   A single application time zone is used.
-   The digest delivery time is still pending (see Section 4).

### Excluded capabilities

-   No attachments or document vault
-   No data export
-   No activity history
-   No external item sharing
-   No recurring schedules in the MVP
-   No reminder snooze
-   No user-configurable reminder timing or notification preferences
-   No item assignment
-   No custom fields or type-specific fields
-   No CSV/PDF export

## 3. Decisions Made --- Question-by-Question Record

  ------------------------------------------------------------------------
                            \# Topic                 Selected decision
  ---------------------------- --------------------- ---------------------
                             1 Target audience       Multiple people ---
                                                     support independent
                                                     users and groups

                             2 Ownership model       Independent users and
                                                     groups

                             3 Account access        Email-based accounts
                                                     using email and
                                                     password

                             4 Group permissions     Owner and members
                                                     with shared access

                             5 Item data model       Common fields only

                             6 Reminder channels     In-app and email
                                                     reminders

                             7 Date handling         Manual date entry
                                                     with recurring
                                                     schedules was
                                                     initially selected;
                                                     later superseded by
                                                     Question 27: no
                                                     recurring schedules
                                                     in MVP

                             8 Completion behavior   Mark complete and
                                                     retain history

                             9 Documents             No attachments

                            10 Dashboard             Upcoming actions and
                                                     overdue items

                            11 Item creation         Guided form with
                                                     lifecycle type
                                                     selection

                            12 Item organization     Basic lists by
                                                     lifecycle type

                            13 Group creation        Users can create
                                                     groups and invite
                                                     members by email

                            14 Shared item           All group members can
                               permissions           manage shared items

                            15 Reminder timing       Fixed reminder
                                                     schedule for everyone

                            16 Overdue behavior      Keep overdue until
                                                     manually completed

                            17 Item responsibility   No assignment

                            18 Member departure      Items remain with the
                                                     group

                            19 Item deletion         Permanent deletion

                            20 Activity history      No activity history

                            21 Data export           No export

                            22 Notification          Both channels always
                               preferences           enabled

                            23 Account deletion      Delete everything,
                                                     including group items

                            24 External item sharing No external sharing

                            25 Common item fields    Name, type, due date,
                                                     status

                            26 Reminder snooze       No snooze

                            27 Recurring schedules   No recurring
                                                     schedules in MVP

                            28 Completed item        Keep completed items
                               visibility            in the main list

                            29 Missing dates         Allow missing dates

                            30 Group deletion        Delete group and all
                                                     its shared items

                            31 Time zones            Single application
                                                     time zone

                            32 Email delivery        Daily scheduled
                                                     digest

                            33 Digest contents       Upcoming and overdue
                                                     items
  ------------------------------------------------------------------------

## 4. Pending Decision

### Question 34 --- Daily digest delivery time

Choose the time for the daily email digest in the single application
time zone:

-   [ ] **A. 6:00 AM** --- early morning
-   [ ] **B. 8:00 AM** --- morning planning
-   [ ] **C. 9:00 AM** --- start-of-workday summary
-   [ ] **D. 12:00 PM** --- midday check-in

No option has been selected yet.

## 5. Important Clarifications for the Next Pass

These are unresolved specification details, not additional decisions:

1.  **Fixed reminder schedule:** The exact lead times before a due date
    have not been selected. Do not assume intervals such as 30, 7, or 1
    day without confirming them.
2.  **In-app reminder behavior:** The channel is selected, but the exact
    UI location and whether reminders are persistent notifications or
    dashboard indicators are not defined.
3.  **Status values:** The common `Status` field is selected, but the
    complete list of statuses and transition rules has not been defined.
    At minimum, the conversation establishes active/upcoming, overdue,
    and completed concepts; final status labels should be confirmed.
4.  **Missing due dates:** Items without dates are allowed. They cannot
    be classified as upcoming or overdue until a due date exists.
5.  **Completed items and "history":** Completed records should remain
    visible, but a separate activity/change log is excluded.
6.  **Account deletion and group ownership:** The selected rule says
    account deletion deletes everything, including group items. The
    handling of groups with other members when their owner deletes their
    account may need an explicit implementation rule; do not silently
    preserve or transfer the group.
7.  **Group deletion permissions:** The deletion consequence is
    selected, but whether only the group owner can delete a group has
    not been explicitly decided.
8.  **Group invitations:** Invitations are sent by email, but
    acceptance, expiry, cancellation, duplicate invitations, and
    behavior for unregistered invitees remain unspecified.
9.  **Due-date semantics:** The application time zone is global, but
    date-only versus date-and-time input and the exact boundary for
    becoming overdue need to be defined.
10. **Renewals and maintenance completion:** Items are retained when
    completed. Since recurring schedules are excluded, the MVP should
    not automatically create a next-cycle item.

## 6. MVP Acceptance Outline

The MVP should allow a user to:

-   Register and log in with email and password.
-   Create a group and invite members by email.
-   Create renewal, maintenance, and warranty items using a guided form.
-   Save items with name, type, optional due date, and status.
-   View items in lists separated by lifecycle type.
-   See upcoming actions and overdue items on the dashboard.
-   Mark an item complete while retaining it in the main list.
-   Receive in-app reminders and a daily email digest containing
    upcoming and overdue items, using the fixed schedule and application
    time zone once configured.
-   Permanently delete items, groups, and accounts according to the
    selected deletion rules.

## 7. Scope Principle

Keep the first version deliberately small: lifecycle records, simple
groups, a focused action dashboard, and fixed reminders. Do not add
excluded capabilities unless the scope is explicitly revised.
