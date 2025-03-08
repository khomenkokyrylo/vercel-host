from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
import time  # Add this import for the timestamp
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Context processor to add css_version to all templates
@app.context_processor
def inject_css_version():
    """Add css_version to all templates automatically."""
    return {'css_version': int(time.time())}

# Helper function to format ISO timestamps
def format_timestamp(ts):
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts

# Custom filter to display dates in human-readable format
@app.template_filter('human_date')
def human_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%A, %d %B %Y")
    except Exception:
        return date_str

# Custom filter to display time in friendly format (e.g., "10pm", "3am")
@app.template_filter('human_time')
def human_time(time_str):
    try:
        dt = datetime.strptime(time_str, "%H:%M:%S")
        return dt.strftime("%I%p").lstrip("0").lower()
    except Exception:
        try:
            dt = datetime.strptime(time_str, "%H:%M")
            return dt.strftime("%I%p").lstrip("0").lower()
        except Exception:
            return time_str

########################################
# Public-Facing Pages
########################################

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/events')
def list_events():
    page = int(request.args.get('page', 1))
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page - 1
    response = (
        supabase.table('events')
        .select("*, event_user:admin_id(full_name)")
        .eq('event_page_status', True)
        .order("event_start_date", desc=False)  # Public events sorted oldest first
        .range(start, end)
        .execute()
    )
    events = response.data if response.data else []
    
    count_response = (
        supabase.table('events')
        .select("id", count="exact")
        .eq('event_page_status', True)
        .execute()
    )
    total_events = count_response.count if count_response.count is not None else 0
    total_pages = (total_events + per_page - 1) // per_page
    return render_template('events.html', events=events, page=page, total_pages=total_pages)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

########################################
# Event Check-In/Check-Out
########################################

@app.route('/event/<event_id>/checkin', methods=['GET', 'POST'])
def event_checkin(event_id):
    event_resp = supabase.table('events').select("*").eq("id", event_id).execute()
    event = event_resp.data[0] if event_resp.data else None

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        dob = request.form.get('dob')
        attendance_type = request.form.get('attendance_type')
        checkin_time = datetime.now()

        user_resp = supabase.table('event_user').select('*').eq('email', email).execute()
        if user_resp.data:
            user_record = user_resp.data[0]
        else:
            user_data = {
                'user_id': None,
                'role': 'user',
                'full_name': username,
                'email': email,
                'date_of_birth': dob
            }
            new_user_resp = supabase.table('event_user').insert(user_data).execute()
            user_record = new_user_resp.data[0]

        user_id = user_record['id']
        data = {
            'event_id': event_id,
            'user_id': user_id,
            'checkin_time': checkin_time.isoformat(),
            'attendance_type': attendance_type
        }
        supabase.table('checkins').insert(data).execute()
        flash('Checked in successfully!', 'success')
        return redirect(url_for('list_events'))

    return render_template('checkin.html', event_id=event_id, event=event)

@app.route('/event/<event_id>/checkout', methods=['GET', 'POST'])
def event_checkout(event_id):
    if request.method == 'POST':
        # Assuming box_number is not part of our current schema
        # Instead, simply find a checkin record to update the checkout_time
        checkin_resp = (
            supabase.table('checkins')
            .select('*')
            .eq('event_id', event_id)
            .execute()
        )
        if checkin_resp.data:
            checkin_record = checkin_resp.data[0]
            checkout_time = datetime.now().isoformat()
            update_data = {'checkout_time': checkout_time}
            supabase.table('checkins').update(update_data).eq('id', checkin_record['id']).execute()
            flash('Checked out successfully!', 'success')
            return redirect(url_for('list_events'))
        else:
            flash('No check-in record found.', 'danger')
            return redirect(url_for('event_checkout', event_id=event_id))
    return render_template('checkout.html', event_id=event_id)

########################################
# Admin / Superadmin Dashboards
########################################

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user = auth_response.user
            if not user:
                flash("Invalid username or password. Please try again.", "danger")
                return redirect(url_for('dashboard'))
            
            profile_resp = supabase.table('event_user').select('*').eq('user_id', user.id).execute()
            if profile_resp.data:
                profile = profile_resp.data[0]
                session['user'] = profile
                if profile.get('role') == 'superadmin':
                    return redirect(url_for('superadmin_dashboard'))
                elif profile.get('role') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Access denied: Not an admin', 'warning')
                    return redirect(url_for('welcome'))
            else:
                flash('Profile not found', 'danger')
                return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Authentication error: {str(e)}", "danger")
            return redirect(url_for('dashboard'))
    return render_template('dashboard_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user' not in session or session['user'].get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    admin_profile = session['user']
    
    # Fetch admin's events sorted by most recent (descending by event_start_date)
    events_resp = (
        supabase.table('events')
        .select('*')
        .eq('admin_id', admin_profile['id'])
        .order('event_start_date', desc=True)
        .execute()
    )
    events = events_resp.data if events_resp.data else []

    # Fetch check-ins and join with event_user and events
    checkins_resp = supabase.table('checkins').select(
        'id, checkin_time, checkout_time, attendance_type, '
        'user:event_user(full_name, email, entry_fee_payment, guest_seat_no, checkin_status), '
        'event:events(event_title, admin_id)'
    ).execute()

    checkins = []
    if checkins_resp.data:
        for c in checkins_resp.data:
            # Only include checkins for events owned by the current admin
            if c.get('event') and c['event'].get('admin_id') == admin_profile['id']:
                try:
                    payment = float(c['user'].get('entry_fee_payment') or 0)
                except:
                    payment = 0
                c['payment_status'] = 'Paid' if payment > 0 else 'Unpaid'
                if c['user'].get('checkin_status'):
                    c['checkin_status'] = c['user']['checkin_status']
                else:
                    c['checkin_status'] = 'Checked In' if not c.get('checkout_time') else 'Checked Out'
                c['event_name'] = c['event'].get('event_title', 'Unknown Event')
                c['full_name'] = c['user'].get('full_name', 'Unknown User')
                c['checkin_date_time'] = c.get('checkin_time')
                checkins.append(c)
                
    return render_template('admin_dashboard.html', events=events, profile=admin_profile, checkins=checkins)

@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    if 'user' not in session or session['user'].get('role') != 'superadmin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    events_resp = supabase.table('events').select('*').execute()
    events = events_resp.data if events_resp.data else []
    return render_template('superadmin_dashboard.html', events=events)

########################################
# Admin Event CRUD
########################################

@app.route('/admin/event/<event_id>/view')
def admin_view_event(event_id):
    if 'user' not in session or session['user'].get('role') not in ['admin', 'superadmin']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    event_resp = supabase.table('events').select('*').eq('id', event_id).execute()
    if not event_resp.data:
        flash('Event not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    event = event_resp.data[0]
    if event.get('event_checkin_time'):
        event['formatted_checkin_time'] = format_timestamp(event['event_checkin_time'])
    return render_template('view_event.html', event=event)


def parse_float(field_name):
    value = request.form.get(field_name)
    if not value or value == "None":
        return None
    try:
        return float(value)
    except ValueError:
        return None

@app.route('/admin/event/<event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    if 'user' not in session or session['user'].get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        event_resp = supabase.table('events').select('*').eq('id', event_id).execute()
        if not event_resp.data:
            flash('Event not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        event = event_resp.data[0]
        if event.get('event_checkin_time'):
            event['formatted_checkin_time'] = format_timestamp(event['event_checkin_time'])
        return render_template('edit_event.html', event=event)
    else:
        event_data = {
            'event_title': request.form.get('event_title'),
            'event_description': request.form.get('event_description'),
            'event_start_date': request.form.get('event_start_date'),
            'event_start_time': request.form.get('event_start_time'),
            'event_venue': request.form.get('event_venue'),
            'postcode': request.form.get('postcode'),
            'event_image_video': request.form.get('event_image_video'),
            'event_checkout_url': request.form.get('event_checkout_url'),
            'event_end_time': request.form.get('event_end_time'),
            'event_page_status': request.form.get('event_page_status') == 'true',
            'event_checkin_time': request.form.get('event_checkin_time'),
            'box_number_range': request.form.get('box_number_range'),
            'exception_list': request.form.get('exception_list'),
            'event_status': request.form.get('event_status') == 'true',
            'men_price': parse_float('men_price'),
            'women_price': parse_float('women_price'),
            'couple_mm_price': parse_float('couple_mm_price'),
            'couple_ff_price': parse_float('couple_ff_price'),
            'tv_ts_single_price': parse_float('tv_ts_single_price'),
            'tv_ts_married_price': parse_float('tv_ts_married_price')
        }
        supabase.table('events').update(event_data).eq('id', event_id).execute()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/event/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    if 'user' not in session or session['user'].get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    supabase.table('events').delete().eq('id', event_id).execute()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create-event', methods=['GET', 'POST'])
def create_event():
    if 'user' not in session or session['user'].get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        event_data = {
            'admin_id': session['user']['id'],
            'event_title': request.form.get('event_title'),
            'event_description': request.form.get('event_description'),
            'event_start_date': request.form.get('event_start_date'),
            'event_start_time': request.form.get('event_start_time'),
            'event_venue': request.form.get('event_venue'),
            'postcode': request.form.get('postcode'),
            'event_image_video': request.form.get('event_image_video'),
            'event_checkout_url': request.form.get('event_checkout_url'),
            'event_end_time': request.form.get('event_end_time'),
            'event_page_status': request.form.get('event_page_status') == 'true',
            'event_checkin_time': request.form.get('event_checkin_time'),
            'box_number_range': request.form.get('box_number_range'),
            'exception_list': request.form.get('exception_list'),
            'event_status': request.form.get('event_status') == 'true',
            'men_price': parse_float('men_price'),
            'women_price': parse_float('women_price'),
            'couple_mm_price': parse_float('couple_mm_price'),
            'couple_ff_price': parse_float('couple_ff_price'),
            'tv_ts_single_price': parse_float('tv_ts_single_price'),
            'tv_ts_married_price': parse_float('tv_ts_married_price')
        }
        supabase.table('events').insert(event_data).execute()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_event.html')

########################################
# Public Event Details
########################################

@app.route('/event/<event_id>')
def public_view_event(event_id):
    event_resp = supabase.table('events').select('*, event_user:admin_id(full_name, id)').eq('id', event_id).execute()
    if not event_resp.data:
        flash('Event not found', 'danger')
        return redirect(url_for('list_events'))
    
    event = event_resp.data[0]
    if event.get('event_checkin_time'):
        event['formatted_checkin_time'] = format_timestamp(event['event_checkin_time'])
    
    checkins_resp = supabase.table('checkins').select('id', count='exact').eq('event_id', event_id).execute()
    secured_seats = checkins_resp.count if checkins_resp.count is not None else 0
    
    admin_id = event['admin_id']
    future_events_resp = (
        supabase.table('events')
        .select('id, event_title, event_start_date, event_image_video')
        .eq('admin_id', admin_id)
        .gt('event_start_date', datetime.now().strftime('%Y-%m-%d'))
        .neq('id', event_id)
        .eq('event_page_status', True)
        .order('event_start_date')
        .limit(3)
        .execute()
    )
    
    future_events = future_events_resp.data if future_events_resp.data else []
    
    is_admin = False
    if 'user' in session and session['user'].get('role') in ['admin', 'superadmin']:
        is_admin = True
        
    return render_template(
        'view_event.html', 
        event=event,
        secured_seats=secured_seats,
        future_events=future_events,
        is_admin=is_admin
    )

if __name__ == '__main__':
    app.run(debug=True)