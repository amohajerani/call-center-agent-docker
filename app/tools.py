from psycopg2 import sql
import psycopg2
from langchain.tools import BaseTool, StructuredTool, tool
from dotenv import load_dotenv
import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
import ast
import re
from datetime import datetime, date

# Ensure environment variables are loaded
load_dotenv()

# Get the connection string from environment variables
connection_string = os.getenv('DATABASE_URL')
openai_api_key = os.getenv('OPENAI_API_KEY')


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


@tool
def verify_identity(name: str) -> bool:
    """Verify the identify of the user based on their name"""
    return True


@tool
def get_member_information(phone_number: str) -> dict:
    """Get member information based on their phone number
    Args:
        phone_number: the member's phone number formatted as XXX-XXX-XXXX
    """
    conn = connect_to_db()
    cur = conn.cursor()
    print(f'phone_number in the function call: {phone_number}')
    query = f"""
    SELECT 
        id, first_name, last_name, phone_number, 
        date_of_birth, gender, street_address, city, 
        state, zip_code, email
    FROM members
    WHERE phone_number = '{phone_number}'
    """
    print(f'query: {query}')
    cur.execute(query)
    result = cur.fetchone()
    conn.close()

    if not result:
        return {"error": "Member not found"}

    member_info = {
        "id": result[0],
        "first_name": result[1],
        "last_name": result[2],
        "phone_number": result[3],
        "date_of_birth": str(result[4]),
        "gender": result[5],
        "street_address": result[6],
        "city": result[7],
        "state": result[8],
        "zip_code": result[9],
        "email": result[10]
    }

    return member_info


@tool
def get_appointment_information(phone_number: str) -> dict:
    """Get appointment information for a member based on the member's phone number
    Args:
        phone_number: the member's phone number, formatted as XXX-XXX-XXXX
    """
    conn = connect_to_db()
    cur = conn.cursor()
    query = f"""
    SELECT 
        a.id, a.date, a.time, a.street_address, a.city, 
        a.state, a.zip_code, a.procedures, a.status,
        p.first_name AS provider_first_name, p.last_name AS provider_last_name
    FROM appointments a
    JOIN providers p ON a.provider_id = p.id
    WHERE a.member_phone = '{phone_number}'
    ORDER BY a.date DESC, a.time DESC
    LIMIT 1
    """

    print(f'query: {query}')
    cur.execute(query)
    result = cur.fetchone()
    conn.close()
    if not result:
        return {"error": "No appointments found for this member"}

    appointment_info = {
        "id": result[0],
        "date": str(result[1]),
        "time": str(result[2]),
        "street_address": result[3],
        "city": result[4],
        "state": result[5],
        "zip_code": result[6],
        "procedures": result[7],
        "status": result[8],
        "provider_name": f"{result[9]} {result[10]}"
    }

    return appointment_info


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
    print(f'query: {query}')
    cur.execute(query)
    result = cur.fetchone()
    conn.close()

    if not result:
        return {"error": "Provider not found"}

    provider_info = {
        "id": result[0],
        "first_name": result[1],
        "last_name": result[2],
        "phone_number": result[3],
        "email": result[4],
        "street_address": result[5],
        "city": result[6],
        "state": result[7],
        "zip_code": result[8],
        "degree": result[9],
        "procedures": result[10]
    }

    return provider_info


# @tool
def schedule_appointment(member_phone: str, appointment_date: str, appointment_time: str) -> str:
    """
    Schedule an appointment for a member with an available provider.

    Args:
    member_phone (str): The phone number of the member.
    appointment_date (str): The date of the appointment (format: YYYY-MM-DD).
    appointment_time (str): The time of the appointment (format: HH:MM).

    Returns:
    str: A confirmation message for the scheduled appointment.
    """
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
        #AND %s::time >= start_time 
        #AND %s::time < end_time
        AND status = 'available'
        LIMIT 1
        """
        print(
            f"availability_query: {cur.mogrify(availability_query, (appointment_date, appointment_time, appointment_time)).decode('utf-8')}")

        cur.execute(availability_query, (appointment_date,
                    appointment_time, appointment_time))
        availability_result = cur.fetchone()

        if not availability_result:
            return "Error: No provider available at the specified date and time."

        provider_id = availability_result[0]

        # Insert the appointment
        insert_query = """
        INSERT INTO appointments (
            member_id, provider_id, member_phone, date, time,
            street_address, city, state, zip_code, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'scheduled')
        RETURNING id
        """
        cur.execute(insert_query, (
            member_id, provider_id, member_phone, appointment_date, appointment_time,
            street_address, city, state, zip_code
        ))
        appointment_id = cur.fetchone()[0]
        conn.commit()
        return f"Appointment scheduled successfully. Appointment ID: {appointment_id}"

    except Exception as e:
        conn.rollback()
        return f"Error scheduling appointment: {str(e)}"

    finally:
        conn.close()
