# Assignment 2 Reflection

**Name:** Nazia Fazili
**Option:** [A - Calendar]
**Date:** [10/11/2026]

---

## Tool Design Decisions

### Tools Implemented
1. **[list_upcoming_events]**: Retrieves upcoming events from the user's primary Google Calendar. The user can specify how many events they want to see.
2. **[find_available_slots]**: Checks a specific day in Google Calendar and identifies available time slots between 8 AM and 5 PM. It uses the Google Calendar FreeBusy API to identify busy periods and calculate free time.
3. **[create_event]**: Creates a new appointment in Google Calendar. It first checks for available time and then schedules the appointment during working hours. It accepts the date, title, duration, description, and location.

I also integrated GitHub MCP tools so the agent can interact with GitHub repositories, including retrieving repository information, issues etc.

### Why These Tools?
I chose these three Calendar tools because they support common scheduling tasks. I wanted the tools to work together. For example, when a user asks to schedule an appointment, the create_event tool first checks availability using find_available_slots before creating the event. I also added a restriction to schedule appointments only between 8 AM and 5 PM


### Description Strategy
I wrote clear tool descriptions explaining when each tool should be used, what parameters it expects, and what it returns.
I also included examples of natural-language questions users might ask. I also added instructions telling the agent not to invent results and to report errors when a tool fails.

---

## Challenges Encountered

### Challenge 1: Google OAuth Authentication
- **Problem:** Understanding how Google OAuth works and how the application obtains permission to access a user's Google Calendar was challenging.
- **Solution:** The credentials.json file identifies my application to Google. When the user signs in, Google asks for permission to access their Calendar. Once approved, Google provides an access token that the app uses to make Calendar API requests. When the token expires, the app can use a refresh token to get a new one without asking the user to sign in again.

### Challenge 2:  GitHub MCP Integration
- **Problem:** Understanding how to connect an MCP server to Google ADK and make the GitHub tools available to the agent was challenging. I also tried to implement the defer_loading pattern to avoid loading all GitHub tools into the agent's context.
- **Solution:** Learnt how to configure GitHub MCP server using McpToolset. I tried implementing the defer_loading pattern but faced error as Google ADK doesnt have a defer_loading flag. 

---

## Error Handling Approach

[Describe your approach to error handling. What types of errors did you anticipate? How do you communicate errors to users?]
I added error handling using try/except blocks and input validation in my Calendar tools.
For example:
- Invalid dates return a message asking for the correct YYYY-MM-DD format.
- Invalid appointment durations are not accepted.
I also instructed the agent to report actual tool results and never invent calendar events, availability, or GitHub information.
---

## Ideas for Improvement

If you had more time, what would you add or change?

1. Improve appointment scheduling: Allow users to select a specific appointment time instead of automatically choosing an available slot.
2. Improve GitHub tool search: Complete the deferred tool-loading implementation so the agent can discover and execute the required GitHub tools without loading all tool definitions upfront.
3. Improve calendar management: Add tools to update or cancel existing appointments.

---

## Key Learnings

What did you learn from this assignment about building AI agents?

This assignment helped me understand how to build AI agents using Google ADK and connect them to Google Calendar and GitHub. 
I learned how agents use tools to complete tasks, how OAuth provides secure access to Google Calendar, and how MCP connects agents to external tools.
I also learned the importance of clear instructions and tool descriptions make agents work reliably.
