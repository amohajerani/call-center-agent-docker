import psycopg2
from langchain.tools import tool
from dotenv import load_dotenv
import os
from openai import OpenAI

from datetime import datetime
from shared import member_info_cache

# Ensure environment variables are loaded
load_dotenv()

# Get the connection string from environment variables
connection_string = os.getenv("DATABASE_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")


def connect_to_db():
    # Check if the connection string is not None before creating the database
    if connection_string is not None:
        conn = psycopg2.connect(connection_string)
    else:
        raise ValueError("DATABASE_URL environment variable is not set")
    return conn


# Check if the OpenAI API key is not None before creating the client
if openai_api_key is not None:
    client = OpenAI(api_key=openai_api_key)
else:
    raise ValueError("OPENAI_API_KEY environment variable is not set")



def get_member_information(phone_number: str) -> dict:
    """
    This function retrieves all the member's information, including their name, contact information, age, gender, medical conditions, past and future appointments.
    Args:
        phone_number (str): member's phone number, formatted as XXX-XXX-XXXX

    Returns:
        str: information about the member's name, contact information, age, gender, medical conditions, past and future appointments.
    """
    # Check if the member information is already in the cache and it is up to date
    print(f"member_info_cache: {member_info_cache}")
    if (
        phone_number in member_info_cache
        and member_info_cache[phone_number]["up_to_date"]
    ):
        member_information = member_info_cache[phone_number]["info"]
        return member_information
    conn = connect_to_db()
    cur = conn.cursor()

    query = f"""
    SELECT 
        id, first_name, last_name, phone_number, 
        date_of_birth, gender, street_address, city, 
        state, zip_code, email
    FROM members
    WHERE phone_number = '{phone_number}'
    """

    cur.execute(query)
    result = cur.fetchone()

    if not result:
        return f"No Member information was found for the phone number {phone_number}"

    member_id = result[0]
    first_name = result[1]
    last_name = result[2]
    date_of_birth = str(result[4])
    gender = result[5]
    street_address = result[6]
    city = result[7]
    state = result[8]
    zip_code = result[9]
    email = result[10]

    # find all the member's appointments
    query = f"""
    SELECT 
        a.id, a.date, a.time, a.street_address, a.city, 
        a.state, a.zip_code,  a.status,
        p.first_name AS provider_first_name, p.last_name AS provider_last_name
    FROM appointments a
    JOIN providers p ON a.provider_id = p.id
    WHERE a.member_phone = '{phone_number}'
    ORDER BY a.date DESC, a.time DESC
    """
    cur.execute(query)
    appointments = cur.fetchall()
    conn.close()

    appointment_descriptions = []
    for appointment in appointments:
        print(f'appointment: {appointment}')
        appointment_id = appointment[0]
        appointment_date = appointment[1].strftime("%B %d, %Y")
        appointment_time = appointment[2].strftime("%I:%M %p")
        appointment_status = appointment[7].capitalize()
        provider_name = f"{appointment[8]} {appointment[9]}"

        description = f"Appointment ID {appointment_id}: Appointment on {appointment_date} at {appointment_time} with Dr. {provider_name}. "
        description += f"Location: {appointment[3]}, {appointment[4]}, {appointment[5]} {appointment[6]}. "
        description += f"Status: {appointment_status}."

        appointment_descriptions.append(description)
        if len(appointment_descriptions) == 0:
            appointment_descriptions.append("No past or future appointments.")

    member_info = f"""
    Member ID: {member_id}
    First Name: {first_name}
    Last Name: {last_name}
    Phone Number: {phone_number}
    Date of Birth: {date_of_birth}
    Gender: {gender}
    Address: {street_address}, {city}, {state} {zip_code}
    Email: {email}
    Appointments:
    {chr(10).join(f"- {appointment}" for appointment in appointment_descriptions)}
    """
    # Update the cache with the member information
    member_info_cache[phone_number] = {"info": member_info, "up_to_date": True}
    return member_info


@tool
def get_provider_information(provider_id: str) -> dict:
    """Get provider information based on their provider ID
    Args:
        provider_id: the id number of the provider
    """

    conn = connect_to_db()
    cur = conn.cursor()
    query = f"""
    SELECT 
        id, first_name, last_name, phone_number, 
        email, street_address, city, state, zip_code, degree, procedures
    FROM providers
    WHERE id = {provider_id}
    """

    cur.execute(query)
    result = cur.fetchone()
    conn.close()

    if not result:
        return {"error": "Provider not found"}

    provider_info = f"""
    Provider Information:
    ID: {result[0]}
    Name: Dr. {result[1]} {result[2]} ({result[9]})
    Contact:
        Phone: {result[3]}
        Email: {result[4]}
    Address: {result[5]}, {result[6]}, {result[7]} {result[8]}
    Procedures: {result[10]}
    """
    return provider_info


@tool
def schedule_appointment(
    member_phone: str, appointment_date: str, appointment_time: str
) -> str:
    """
    Schedule an appointment for a member with an available provider.
    Args:
        member_phone (str): The phone number of the member.
        appointment_date (str): The date of the appointment (format: YYYY-MM-DD).
        appointment_time (str): The time of the appointment (format: HH:MM).

    Returns:
        str: A confirmation message for the scheduled appointment.
    """
    # update the member_info_cache
    if member_phone in member_info_cache:
        member_info_cache[member_phone]["up_to_date"] = False
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        # Get member information
        member_query = """
        SELECT id, street_address, city, state, zip_code
        FROM members
        WHERE phone_number = %s
        """
        cur.execute(member_query, (member_phone,))
        member_result = cur.fetchone()

        if not member_result:
            return "Error: Member not found with the given phone number."

        member_id, street_address, city, state, zip_code = member_result

        # Find an available provider
        availability_query = """
        SELECT provider_id 
        FROM availability 
        WHERE date = %s
        AND %s::time >= start_time 
        AND %s::time < end_time
        AND status = 'available'
        LIMIT 1
        """

        cur.execute(
            availability_query, (appointment_date, appointment_time, appointment_time)
        )
        availability_result = cur.fetchone()

        if not availability_result:
            return "Error: No provider available at the specified date and time."

        provider_id = availability_result[0]
        # update the provider availability to unavailable
        update_availability_query = """
        UPDATE availability
        SET status = 'unavailable'
        WHERE provider_id = %s
        AND date = %s
        AND %s::time >= start_time 
        AND %s::time < end_time
        """
        print(f'update_availability_query: {update_availability_query}')
        cur.execute(
            update_availability_query,
            (provider_id, appointment_date, appointment_time, appointment_time),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return "Error: Failed to update provider availability."

        # Insert the appointment
        insert_query = """
        INSERT INTO appointments (
            member_id, provider_id, member_phone, date, time,
            street_address, city, state, zip_code, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'scheduled')
        RETURNING id
        """
        cur.execute(
            insert_query,
            (
                member_id,
                provider_id,
                member_phone,
                appointment_date,
                appointment_time,
                street_address,
                city,
                state,
                zip_code,
            ),
        )
        appointment_id = cur.fetchone()[0]
        conn.commit()
        return f"Appointment scheduled successfully. Appointment ID: {appointment_id}"

    except Exception as e:
        conn.rollback()
        return f"Error scheduling appointment: {str(e)}"

    finally:
        conn.close()


@tool
def cancel_appointment(appointment_id: int, phone_number: str) -> str:
    """
    Cancel an appointment.
    Args:
        appointment_id (int): The ID of the appointment
        phone_number (str): The phone number of the member, formatted as XXX-XXX-XXXX

    Returns:
    str: confirmation of the cancelled appointment
    """
    # update the member_info_cache
    if phone_number in member_info_cache:
        member_info_cache[phone_number]["up_to_date"] = False
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        # First, get the appointment details
        cur.execute(
            """
            SELECT provider_id, date, time
            FROM appointments
            WHERE id = %s AND status != 'cancelled'
        """,
            (appointment_id,),
        )

        appointment = cur.fetchone()
        if not appointment:
            return f"Error: Appointment with ID {appointment_id} not found or already cancelled."

        provider_id, appointment_date, appointment_time = appointment

        # Update the appointment status to 'cancelled'
        cur.execute(
            """
            UPDATE appointments
            SET status = 'cancelled'
            WHERE id = %s
        """,
            (appointment_id,),
        )

        if cur.rowcount == 0:
            conn.rollback()
            return f"Error: Failed to cancel appointment with ID {appointment_id}."

        # Update the provider's availability back to 'available'
        cur.execute(
            """
            UPDATE availability
            SET status = 'available'
            WHERE provider_id = %s
            AND date = %s
            AND %s::time >= start_time 
            AND %s::time < end_time
        """,
            (provider_id, appointment_date, appointment_time, appointment_time),
        )

        # Add this check
        if cur.rowcount == 0:
            conn.rollback()
            return f"Warning: Appointment cancelled, but failed to update provider availability."

        conn.commit()
        return f"Appointment with ID {appointment_id} has been successfully cancelled."

    except Exception as e:
        conn.rollback()
        return f"Error cancelling appointment: {str(e)}"

    finally:
        conn.close()


@tool
def escalate_call(phone_number, description):
    """
    Use this tool to escalate a call. This tool will notify the supervisors and provide them with a summary to call the member back.

    Args:
        phone_number (int): the caller's phone number, formatted as XXX-XXX-XXXX
        description (str): A summary description of the escalation.

    Returns:
        str: confirmation that the call was escalated and the supervisor will call back shortly.
    """
    conn = connect_to_db()
    cur = conn.cursor()

    try:
        current_time = datetime.now()
        cur.execute(
            """
            INSERT INTO escalations (phone_number, status, description, created_at)
            VALUES (%s, %s, %s, %s)
        """,
            (phone_number, "escalated", description, current_time),
        )

        if cur.rowcount == 0:
            conn.rollback()
            return "Failed to escalate call."

        conn.commit()
        return "Call escalated and supervisor will call back shortly."

    except Exception as e:
        conn.rollback()
        return f"Error escalating call: {str(e)}"

    finally:
        conn.close()
