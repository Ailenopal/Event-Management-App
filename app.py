import streamlit as st
import pandas as pd
from datetime import datetime
import json

# --- Configuration & Utility Functions ---

def load_events():
    """Loads events from Streamlit's session state (or initializes an empty list)."""
    if 'events' not in st.session_state:
        # For a truly persistent app (like in your JS example), you'd use a file (JSON/CSV) or DB.
        # Here we use session state for simplicity, as Streamlit is stateless on a per-session basis.
        st.session_state.events = []
    return st.session_state.events

def save_events(event_list):
    """Saves events to Streamlit's session state."""
    st.session_state.events = event_list

def add_event(event_data):
    """Adds a new event or updates an existing one."""
    events = load_events()
    
    if st.session_state.editing_id is not None:
        # Edit existing event
        index = next((i for i, event in enumerate(events) if event['id'] == st.session_state.editing_id), -1)
        if index != -1:
            events[index] = {**event_data, 'id': st.session_state.editing_id}
        st.session_state.editing_id = None
        st.toast("✅ Event updated successfully!")
    else:
        # Add new event
        event_data['id'] = datetime.now().timestamp() # Use timestamp for unique ID
        events.append(event_data)
        st.toast("✅ New Event created!")
    
    save_events(events)
    # Automatically switch to view tab after create/edit
    st.session_state.current_tab = 'View Events'


def delete_event(event_id):
    """Deletes an event by its ID."""
    events = [event for event in load_events() if event['id'] != event_id]
    save_events(events)
    st.toast("🗑️ Event deleted.")
    st.rerun() # Rerun to refresh the list

def start_edit_event(event_id):
    """Sets up session state for editing an event."""
    st.session_state.editing_id = event_id
    st.session_state.current_tab = 'Create Event'

def get_event_by_id(event_id):
    """Retrieves a single event object."""
    return next((e for e in load_events() if e['id'] == event_id), None)

def sort_events(event_list):
    """Sorts events by date and time."""
    return sorted(event_list, key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %H:%M"))

# --- Streamlit UI Components ---

def create_event_tab():
    """Renders the Create/Edit Event form."""
    
    event_categories = ["Meeting", "Conference", "Workshop", "Social", "Other"]
    
    # Check if we are editing an existing event
    editing_event = get_event_by_id(st.session_state.editing_id) if 'editing_id' in st.session_state and st.session_state.editing_id else None
    
    st.subheader(f"{'Edit' if editing_event else 'Create New'} Event")
    
    # Pre-fill form fields if editing
    default_title = editing_event.get('title', '') if editing_event else ''
    default_date = editing_event.get('date', datetime.today().strftime('%Y-%m-%d')) if editing_event else datetime.today().strftime('%Y-%m-%d')
    default_time = editing_event.get('time', datetime.now().strftime('%H:%M')) if editing_event else datetime.now().strftime('%H:%M')
    default_location = editing_event.get('location', '') if editing_event else ''
    default_category = editing_event.get('category', event_categories[0]) if editing_event else event_categories[0]
    default_description = editing_event.get('description', '') if editing_event else ''

    with st.form(key='eventForm'):
        event_title = st.text_input("Event Title *", default_title, key='eventTitle')
        
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Date *", datetime.strptime(default_date, '%Y-%m-%d'), key='eventDate')
        with col2:
            event_time = st.time_input("Time *", datetime.strptime(default_time, '%H:%M').time(), key='eventTime')
        
        event_location = st.text_input("Location", default_location, key='eventLocation', placeholder="Event location")
        event_category = st.selectbox("Category", event_categories, index=event_categories.index(default_category), key='eventCategory')
        event_description = st.text_area("Description", default_description, key='eventDescription', placeholder="Event details and notes")
        
        submit_button = st.form_submit_button(label=f"{'Update Event' if editing_event else 'Create Event'}", use_container_width=True)

        if submit_button:
            if not event_title:
                st.error("Event Title is required!")
            else:
                event_data = {
                    'title': event_title,
                    'date': event_date.strftime('%Y-%m-%d'),
                    'time': event_time.strftime('%H:%M'),
                    'location': event_location,
                    'category': event_category,
                    'description': event_description
                }
                add_event(event_data)
                # st.rerun() # Rerun handled by add_event switching tab

def view_events_tab():
    """Renders the View Events list with search and filters."""
    st.subheader("Your Events")
    
    all_events = load_events()
    event_categories = ["All Categories"] + ["Meeting", "Conference", "Workshop", "Social", "Other"]

    # --- Filter Bar ---
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("🔍 Search events...", key='searchInput', placeholder="Title, location, or description")
    with col2:
        category_filter = st.selectbox("Filter by Category", event_categories, key='categoryFilter')

    # --- Filtering Logic ---
    filtered_events = []
    
    if all_events:
        for event in all_events:
            matches_search = search_query.lower() in event['title'].lower() or \
                             search_query.lower() in event['description'].lower() or \
                             search_query.lower() in event['location'].lower()
            
            matches_category = category_filter == "All Categories" or event['category'] == category_filter

            if matches_search and matches_category:
                filtered_events.append(event)

    sorted_events = sort_events(filtered_events)

    # --- Display Events ---
    
    if not all_events:
        st.markdown(
            """
            <div style='text-align: center; padding: 60px 20px; color: #6c757d;'>
                <div style='font-size: 4rem; margin-bottom: 20px; opacity: 0.5;'>📋</div>
                <h3>No events yet</h3>
                <p>Create your first event to get started!</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    elif not sorted_events:
        st.markdown(
            """
            <div style='text-align: center; padding: 60px 20px; color: #6c757d;'>
                <div style='font-size: 4rem; margin-bottom: 20px; opacity: 0.5;'>🔍</div>
                <h3>No events found</h3>
                <p>Try adjusting your search criteria</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Use columns to mimic the grid layout
        cols = st.columns(3) # Adjust number of columns as needed
        
        for i, event in enumerate(sorted_events):
            with cols[i % 3]: # Cycle through columns
                # Custom HTML/Markdown for the event card styling
                badge_style = "background-color: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;"
                
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                        border-radius: 12px; 
                        padding: 20px; 
                        margin-bottom: 20px;
                        border-left: 4px solid #667eea;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                    ">
                        <div style="font-size: 1.3rem; font-weight: 700; color: #212529; margin-bottom: 10px;">
                            {event['title']}
                        </div>
                        <div style="color: #6c757d; margin-bottom: 8px;">
                            📅 {datetime.strptime(event['date'], '%Y-%m-%d').strftime('%a, %b %d, %Y')}
                        </div>
                        <div style="color: #6c757d; margin-bottom: 8px;">
                            🕐 {datetime.strptime(event['time'], '%H:%M').strftime('%I:%M %p')}
                        </div>
                        {f"<div style='color: #6c757d; margin-bottom: 8px;'>📍 {event['location']}</div>" if event['location'] else ''}
                        
                        <div style="margin: 10px 0;">
                            <span style='{badge_style}'>{event['category']}</span>
                        </div>
                        
                        {f"<div style='color: #495057; margin: 15px 0; line-height: 1.6;'>{event['description']}</div>" if event['description'] else ''}
                        
                        <div style='display: flex; gap: 10px; margin-top: 15px;'>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Streamlit buttons need a unique key and must be outside markdown block for functionality
                col_edit, col_delete = st.columns(2)
                with col_edit:
                    st.button("Edit", key=f"edit_{event['id']}", on_click=start_edit_event, args=(event['id'],), use_container_width=True)
                with col_delete:
                    st.button("Delete", key=f"delete_{event['id']}", on_click=delete_event, args=(event['id'],), use_container_width=True)
                
                # Close the div structure started in the markdown block
                st.markdown("</div></div>", unsafe_allow_html=True)


# --- Main App Execution ---

def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(layout="wide", page_title="Event Manager App")
    
    # Initialize session state for active tab and editing
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 'Create Event'
    if 'editing_id' not in st.session_state:
        st.session_state.editing_id = None
        
    st.markdown("""
        <style>
            /* Custom CSS to match the original gradient background */
            .main {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }
            /* Custom styling for the main app container */
            .stApp > header { visibility: hidden; }
            .block-container {
                max-width: 1200px;
                padding: 0px 20px; /* Adjust inner padding */
            }
            .app-wrapper {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
                padding-top: 0px; 
            }
            /* Streamlit specific adjustments */
            .stTabs [data-baseweb="tab-list"] {
                background: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
                padding: 0 30px; /* Match inner content padding */
            }
            .stTabs [data-baseweb="tab"] {
                flex: 1;
                padding: 20px 0;
                text-align: center;
                font-weight: 600;
                color: #6c757d;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                color: #667eea;
                border-bottom-color: #667eea !important;
                background: white;
            }
            /* Remove standard Streamlit padding from tab content area */
            .stTabs > div > div:nth-child(2) {
                padding: 30px; 
            }
        </style>
        <div style="text-align: center; color: white; margin-bottom: 30px;">
            <h1 style="font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">📅 Event Manager</h1>
            <p style="font-size: 1.1rem; opacity: 0.9;">Organize and track your events effortlessly</p>
        </div>
        <div class="app-wrapper">
    """, unsafe_allow_html=True)

    # Streamlit Tabs
    tab1, tab2 = st.tabs(["Create Event", "View Events"])

    # Manually switch tabs based on session state for programmatic transitions (like after creating/editing)
    if st.session_state.current_tab == 'Create Event':
        with tab1:
            create_event_tab()
    elif st.session_state.current_tab == 'View Events':
        with tab2:
            view_events_tab()

    st.markdown("</div>", unsafe_allow_html=True) # Close app-wrapper

if __name__ == "__main__":
    main()
