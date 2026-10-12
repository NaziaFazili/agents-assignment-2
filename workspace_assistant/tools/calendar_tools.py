"""
Option A: Calendar Assistant Tools

Implement at least 3 tools for Google Calendar operations.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from google.adk.tools import FunctionTool

from .auth import get_calendar_service

# Implement your calendar tools
# Define each tool as a plain Python function with a clear docstring and type
# hints (ADK reads these to build the tool schema and auto-wraps the function),
# then add it to the list below. Each tool should return a dict with 'status'
# and relevant data. Wrapping with FunctionTool(func=my_function) is optional
# and only needed when you want explicit control over the tool.

timezone_name: str = "UTC"
# calendar_tools = []


def list_upcoming_events(max_results: int = 20) -> dict:
    """List upcoming calendar events from primary calendar

    Use this when user asks to retreive upcoming calendar events from his primary google calendar.
    (e.g., "Fetch a list of my upcoming events in my Google calendar", "Can you show me my schedule for the next few days?", "What meetings do I have coming up?").

    Args:
        max_results: Maximum number of events to return. It has to be an integer value greater than 0

    Returns:
        A dict containing:
        - status (str): "success" or  "error"
        - events (list[dict]): A list of calendar event dictionaries.
            Each event contains id, title, start, end, and location.
            This list is empty if no events are found.
        - message (str): Error details, present only if status is "error".
    """
    try:
        service = get_calendar_service()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                maxResults=max_results,
                orderBy="startTime",
                timeMin=datetime.now(timezone.utc).isoformat(),
                singleEvents=True,
            )
            .execute()
        )
        items = events_result.get("items", [])
        events = []

        for event in items:
            start = event.get("start", {})
            end = event.get("end", {})

            events.append(
                {
                    "id": event.get("id"),
                    "title": event.get("summary", "(No title)"),
                    "start": start.get("dateTime") or start.get("date"),
                    "end": end.get("dateTime") or end.get("date"),
                    "location": event.get("location"),
                    # "link": event.get("htmlLink"),
                }
            )

        return {"status": "success", "events": events}
        # return {"status": "success", "events": events_result.get("items", [])}
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred while fetching the calendar events: {str(e)}",
        }


def find_available_slots(
    day: str,
) -> dict:
    """
    Finds free slots within a working day (from 8 AM to 5 PM) in Google calendar

    Use this when a user asks if there are any available free time slots on a Google calendar on a specific day.
    (e.g. "Show me my available time slots for October 15", "Do I have any openings this Friday?", "Am I free tomorrow?" )
    Args:
        day: Date to check for free slots in YYYY-MM-DD format.

    Returns:
        A dictionary containing:
            - status: "success" or "error".
            - date: Date being checked.
            - free_slots (list[dict]): A list of open slots dictionaries.
                        Each open slot contains start_time and end_time.
                        This list is empty if no slots are found.
            - message: Error details if something goes wrong.
    """
    try:
        service = get_calendar_service()
    except Exception as e:
        return {
            "status": "error",
            "date": day,
            "free_slots": [],
            "message": f"Failed to initialize calendar service: {str(e)}",
        }

    calendar_id = "primary"
    start_hour: int = 8
    end_hour: int = 17
    settings = service.settings().get(setting="timezone").execute()

    timezone_name = settings.get("value", "UTC")
    tz = ZoneInfo(timezone_name)

    try:
        selected_date = date.fromisoformat(day)
    except (ValueError, TypeError):
        return {
            "status": "error",
            "message": "Provide the date in YYYY-MM-DD string format.",
        }
    try:
        # Define the time boundaries for the query day (in ISO format / RFC3339)
        time_min = datetime.combine(selected_date, time(start_hour, 0), tzinfo=tz)
        time_max = datetime.combine(selected_date, time(end_hour, 0), tzinfo=tz)
        # 1. Build the Freebusy query payload
        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "timeZone": timezone_name,
            "items": [{"id": calendar_id}],
        }

        # 2. Execute the Freebusy request
        busy_result = service.freebusy().query(body=body).execute()
        busy_intervals = busy_result["calendars"][calendar_id]["busy"]

        # Convert string timestamps to datetime objects for easy math
        # day_start = datetime.fromisoformat(time_min.isoformat())
        # day_end = datetime.fromisoformat(time_max.isoformat())

        busy_periods = []
        for block in busy_intervals:
            start = datetime.fromisoformat(block["start"]).astimezone(tz)
            end = datetime.fromisoformat(block["end"]).astimezone(tz)
            busy_periods.append((start, end))

        # Sort busy blocks just in case they aren't ordered
        busy_periods.sort(key=lambda x: x[0])

        # 3. Calculate the free slots (the gaps)
        free_slots = []
        current_time = time_min

        for busy_start, busy_end in busy_periods:
            # If there is a gap before the next busy block starts, it's a free slot
            if busy_start > current_time:
                free_slots.append(
                    {
                        "start_time": current_time.strftime("%I:%M %p").lstrip("0"),
                        "end_time": busy_start.strftime("%I:%M %p").lstrip("0"),
                    }
                )
            # Move our timeline forward to the end of the busy block
            if busy_end > current_time:
                current_time = busy_end

        # Check if there is any free time left at the end of the day
        if current_time < time_max:
            free_slots.append(
                {
                    "start_time": current_time.strftime("%I:%M %p").lstrip("0"),
                    "end_time": time_max.strftime("%I:%M %p").lstrip("0"),
                }
            )

        return {
            "status": "success",
            "date": day,
            "free_slots": free_slots,
            "message": "Free slots retrieved successfully.",
        }
    except Exception as e:
        return {
            "status": "error",
            "date": day,
            "free_slots": [],
            "message": f"An error occurred while fetching free slots: {str(e)}",
        }


def create_event(
    day: str,
    title: str,
    duration_minutes: int = 30,
    description: str = "",
    location: str = "",
) -> dict:
    """Create an appointment in Google Calendar during an available time slot on a working day (from 8 AM to 5 PM)

    Use this when a user asks to schedule an appointment for a particular day.
    It does not handle appointment time requests.
    (e.g., "Schedule a 1-hour appointment for tomorrow.", "Add a 30-minute call for Monday.", "Book an 45-minute meeting for October 15").

    Args:
        day: Date in YYYY-MM-DD format.
        title: Title of the appointment.
        duration_minutes: Appointment duration in minutes. Defaults to 30.
        description: Optional appointment details.
        location: Optional appointment location.

    Returns:
        A dictionary containing status and event details, or an error message.
    """

    # Validate the inputs

    try:
        selected_date = date.fromisoformat(day)
    except (ValueError, TypeError):
        return {
            "status": "error",
            "message": "Provide the date in YYYY-MM-DD string format.",
        }
    try:
        if not title.strip():
            raise ValueError("Appointment title cannot be empty.")

        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise ValueError("Duration must be a positive integer.")

    except (ValueError, TypeError) as e:
        return {
            "status": "error",
            "message": str(e),
        }

    try:
        # Call the existing tool to find available slots
        availability = find_available_slots(day)

        if availability.get("status") != "success":
            return {
                "status": "error",
                "message": availability.get("message"),
            }

        free_slots = availability.get("free_slots", [])

        if not free_slots:
            return {
                "status": "error",
                "message": f"No free time is available on {day}.",
            }

        # Convert the available times into datetime objects
        tz = ZoneInfo(timezone_name)
        duration = timedelta(minutes=duration_minutes)

        selected_start = None
        selected_end = None

        # Find a slot that can fit the appointment
        for slot in free_slots:
            slot_start = datetime.combine(
                selected_date,
                datetime.strptime(slot["start_time"], "%I:%M %p").time(),
                tzinfo=tz,
            )

            slot_end = datetime.combine(
                selected_date,
                datetime.strptime(slot["end_time"], "%I:%M %p").time(),
                tzinfo=tz,
            )

            appointment_end: datetime = slot_start + duration

            # The appointment must fit completely inside the free slot
            if appointment_end <= slot_end:
                selected_start = slot_start
                selected_end = appointment_end
            break

        if selected_start is None:
            return {
                "status": "error",
                "message": (
                    f"No available slot fits a {duration_minutes}-minute "
                    f"appointment on {day}"
                ),
            }

        # 5. Prepare the Google Calendar event
        event = {
            "summary": title,
            "start": {
                "dateTime": selected_start.isoformat(),
                "timeZone": timezone_name,
            },
            "end": {
                "dateTime": selected_end.isoformat(),
                "timeZone": timezone_name,
            },
        }

        if description.strip():
            event["description"] = description

        if location.strip():
            event["location"] = location

        # 6. Create the event in Google Calendar
        service = get_calendar_service()

        created_event = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
            )
            .execute()
        )

        # 7. Return a simple response
        return {
            "status": "success",
            "message": "Appointment created successfully.",
            "event": {
                "id": created_event.get("id"),
                "title": created_event.get("summary"),
                "start": created_event.get("start", {}).get("dateTime"),
                "end": created_event.get("end", {}).get("dateTime"),
                "link": created_event.get("htmlLink"),
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create appointment: {str(e)}",
        }


calendar_tools = [
    list_upcoming_events,
    find_available_slots,
    create_event,
    # FunctionTool(func=create_event, require_confirmation=True),
]

if __name__ == "__main__":
    print("Starting calendar tool test...", flush=True)
    # result = list_upcoming_events(max_results=2)
    result = find_available_slots("2026-10-13")
    # result = create_event(
    #     "2026-10-12", "Dentist", 30, "Root canal", "Dr. Stewart office"
    # )

    print(result)
