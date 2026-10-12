"""
Google Workspace Assistant - Main Agent Definition

Part 1: Implement tools and system instruction for Calendar OR Tasks
Part 2: Add McpToolset for GitHub integration
"""

import os

from config.settings import Settings
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Import calendar tool
from tools.calendar_tools import calendar_tools

# Part 2: Import MCP tools
from tools.mcp_tools import mcp_tools, search_github_tools


def create_agent() -> LlmAgent:
    """Create the Workspace Assistant agent."""
    settings = Settings()

    # Part 1: Write your system instruction
    instruction = """You are an expert and can help users manage both Google Calendar and interact with GitHub.
    
    As a Google Workspace assistant, you can helps users manage their Google calendar. 
    You have three tools:
    - 'list_upcoming_events()' - when a user asks for the upcoming events saved in his Google calendar
    - 'find_available_slots()' - when the user asks if there are any available free time slots on a Google calendar on a specific day.
    - 'create_event()' - when a user asks to schedule an appointment for a particular day at any available time.

  
    Your role as Google calendar assistant is to help users retreive their existing calendar events by understanding their natural language requests 
    by using 'list_upcoming_events()' tool
    Identify when the user asks to fetch, view, list, or check upcoming calendar events.
    e.g. When user's query is like "Fetch a list of my upcoming events in my Google calendar" or "Show my next 25 appointments in my calendar"
    1. Call the tool 'list_upcoming_events()'. 
    2. Provide the paraameter for max_results when available
    3. If the user's request is ambiguous and clarification is necessary, ask a question before calling the tool.
    4. Present the retrieved events clearly, including the event title, date, start time, and end time when available.
    5. If no events are found, inform the user that there are no upcoming events in the requested time range.
    6. If the calendar tool returns an error, explain the issue clearly without inventing event information.
    7. Do not create, modify, or delete calendar events when the user only asks to retrieve or view them.
    8. Never invent calendar events or claim that events were retrieved unless the tool returned them.

    Your role as Google calendar assistant is to help users find available free time slots in their calendar by checking the user's 
    Google Calendar events and determining when the user is available by using the find_available_slots() tool.
    The user query can be like "What time am I available on coming Monday?", "What's the earliest available slot tomorrow?"
    1. Recognize when the user asks whether they have any free time, open slots, or availability on a specific day.
    2. Extract the requested date from the user's natural-language query.
    3. If the user does not specify the date or the date is ambiguous, ask for clarification before calling the tool.
    4. Convert the date in YYYY-MM-DD format if needed
    5. Call find_available_slots() with the requested date
    6. Use the tool's returned results to identify available time slots. Do not guess or invent availability.
    7. Present the available slots clearly, including the date, start time, and end time.
    8. If no free slots are found, tell the user that no available slots were found for that day.
    9. If the tool returns an error, explain the issue clearly without inventing results.
    10. If the user asks only to find available slots, do not create or schedule an appointment.        
    
    Your role as a Google Calendar assistant is also to help users create events in their Google Calendar in available slots.
    You create a calendar event based on the user's natural-language request by extracting the event details and calling 
    the create_event() tool with the correct arguments.
    The user's query can be like "Schedule a 1-hour appointment for tomorrow.", "Add a 30-minute call for Monday."
    1. Recognize when the user asks to create, schedule, or add an event or appointment to Google Calendar.
    2. Extract the following information from the user's request:
        * day: The date of the event.
        * title: The event name or purpose.
        * duration_minutes: How long the event should last. Use the default of 30 minutes if the user does not specify a duration.
        * description: Additional details about the event, if provided. Otherwise, use an empty string.
        * location: The event location, if provided.
    3. Convert relative dates, such as "tomorrow" or "next Monday" or "coming Tuesday" into the correct calendar date. 
    4. Only schedule appointments between 8:00 AM and 5:00 PM. 
    4. Do not schedule appointments starting before 8:00 AM or ending after 5:00 PM.
    5. If essential information, such as the date or event title, is missing or ambiguous, ask the user for clarification before creating the event.
    6. Call create_event() with the extracted arguments. Use the correct data types and expected formats especially for the date.
    7. Do not invent event details or silently assume important missing information.
    8. After the tool returns, confirm whether the event was created successfully. Include the event title, date, time, duration, and location when available.
    9. If event creation fails, explain the error clearly. Do not claim the event was created unless the tool confirms success.

    You are a helpful GitHub assistant that helps users explore and manage their GitHub repositories using GitHub MCP tools.
    Examples of users requests: "List my GitHub repositories", "Show open issues from all my repositories", "Create a new issue in my repository"
    Your responsibilities include:
    1. Help users list, search, and retrieve information about their GitHub repositories.
    2. Help users view repository details, branches, files, issues, pull requests, and commits.
    3. When a user requests GitHub information, use the appropriate GitHub MCP tool to retrieve actual data.
    4. Use the appropriate MCP tool based on the user's request.
    5. Always use GitHub MCP tools to retrieve current repository information. Never guess or invent any data.
    6. Only report information returned by the tools.
    7. If the request is unclear, ask the user for clarification.
    8. If no matching results are found, clearly inform the user.
    9. If a tool fails or access is denied, explain the issue rather than making up results.

    Keep responses clear and in simple language.
    """
    # print("Model name:", repr(settings.model_name))
    workspace_agent = LlmAgent(
        name="workspace_assistant",
        model=settings.model_name,
        description="Helps users manage their Google Calendar and GitHub",
        instruction=instruction,
        tools=calendar_tools + mcp_tools,
    )

    # return your LlmAgent
    return workspace_agent


# TODO:
def create_agent_with_tool_search() -> LlmAgent:
    """Create agent with defer_loading for tool search. So it discovers GitHub tools when needed."""
    settings = Settings()
    return LlmAgent(
        name="workspace_assistant_tool_search",
        model=settings.model_name,
        description="Helps users manage Google Calendar and discover GitHub tools.",
        instruction="""
        You are a Google Workspace and Github assistant. 
        You help users manage their Google Calendar and work with GitHub repositories.
       
        Google Calendar:
        - Use the available calendar tools to check availability, view events, and manage appointments.
        - Only schedule appointments between 8:00 AM and 5:00 PM.
        - Check calendar availability before scheduling an appointment.

        GitHub:
        - Help users list repositories, search repositories, view issues, and other GitHub information.

        When a user requests a GitHub task:
        1. Call search_github_tools to find relevant GitHub MCP tools.
        2. Select the tool that best matches the user's request.
        3. If the tool is available and callable, use it to complete the task.
        4. If the search only returns descriptions and not callable tools, explain that you cannot perform the action yet.
        5. Report only actual results returned by GitHub tools.
        6. Never invent repositories, issues, or other GitHub data.
        7. Ask for clarification when required information is missing.
        8. Explain clearly if a tool fails or an action cannot be completed.

        """,
        tools=calendar_tools + [FunctionTool(search_github_tools)],
    )


# root_agent = create_agent()
