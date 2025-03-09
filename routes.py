from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import pandas as pd
from app import app, db
from models import Campaign, Donor, User
from utils import generate_donor_code, create_pdf_report
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    # Get basic statistics
    total_donors = Donor.query.count()
    eligible_donors = Donor.query.filter_by(is_eligible=True).count()
    active_campaigns = Campaign.query.filter(
        Campaign.end_date >= datetime.utcnow()
    ).count()

    # Calculate success rate
    success_rate = round((eligible_donors / total_donors * 100) if total_donors > 0 else 0, 1)

    # Calculate total blood collected (assuming each eligible donor gives 450ml)
    blood_collected = round((eligible_donors * 0.45), 1)  # in liters

    # Get recent donations
    recent_donations = Donor.query.order_by(Donor.donation_date.desc()).limit(5).all()

    return render_template('dashboard.html',
                         total_donors=total_donors,
                         blood_collected=blood_collected,
                         success_rate=success_rate,
                         active_campaigns=active_campaigns,
                         recent_donations=recent_donations)

@app.route('/donor-form/<campaign_id>')
@login_required
def donor_form(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('donor_form.html', campaign=campaign)

@app.route('/submit-donor', methods=['POST'])
@login_required
def submit_donor():
    try:
        data = request.form
        new_donor = Donor(
            unique_code=generate_donor_code(),
            campaign_id=data['campaign_id'],
            name=data['name'],
            age=int(data['age']),
            gender=data['gender'],
            blood_type=data['blood_type'],
            weight=float(data['weight']),
            hemoglobin=float(data['hemoglobin']),
            location=data['location'],
            medical_conditions=data.get('medical_conditions', ''),
            is_eligible=data.get('is_eligible', 'true') == 'true'
        )

        db.session.add(new_donor)
        db.session.commit()

        return jsonify({'success': True, 'donor_code': new_donor.unique_code})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/campaigns')
@login_required
def campaigns():
    return render_template('campaigns.html')

@app.route('/campaign/new', methods=['POST'])
@login_required
def create_campaign():
    try:
        data = request.form
        new_campaign = Campaign(
            name=data['name'],
            description=data['description'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
            location=data['location'],
            target_goal=int(data['target_goal'])
        )

        db.session.add(new_campaign)
        db.session.commit()

        return jsonify({
            'success': True,
            'campaign_id': new_campaign.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/campaign-stats/<campaign_id>')
@login_required
def campaign_stats(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    donors = Donor.query.filter_by(campaign_id=campaign_id).all()

    stats = {
        'total_donors': len(donors),
        'eligible_donors': len([d for d in donors if d.is_eligible]),
        'blood_types': {},
        'gender_distribution': {},
        'age_groups': {'18-25': 0, '26-35': 0, '36-45': 0, '46+': 0}
    }

    for donor in donors:
        stats['blood_types'][donor.blood_type] = stats['blood_types'].get(donor.blood_type, 0) + 1
        stats['gender_distribution'][donor.gender] = stats['gender_distribution'].get(donor.gender, 0) + 1

        if donor.age <= 25:
            stats['age_groups']['18-25'] += 1
        elif donor.age <= 35:
            stats['age_groups']['26-35'] += 1
        elif donor.age <= 45:
            stats['age_groups']['36-45'] += 1
        else:
            stats['age_groups']['46+'] += 1

    return jsonify(stats)

@app.route('/export/csv/<campaign_id>')
@login_required
def export_csv(campaign_id):
    donors = Donor.query.filter_by(campaign_id=campaign_id).all()
    df = pd.DataFrame([{
        'Donor Code': d.unique_code,
        'Name': d.name,
        'Blood Type': d.blood_type,
        'Age': d.age,
        'Gender': d.gender,
        'Weight': d.weight,
        'Hemoglobin': d.hemoglobin,
        'Location': d.location,
        'Donation Date': d.donation_date,
        'Is Eligible': d.is_eligible
    } for d in donors])

    return df.to_csv(index=False)

@app.route('/export/pdf/<campaign_id>')
@login_required
def export_pdf(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    donors = Donor.query.filter_by(campaign_id=campaign_id).all()
    return create_pdf_report(campaign, donors)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html',
                         default_settings=None)  # You can add default settings from database later

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.form
        # Update user profile logic here
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.form
        # Password change logic here
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/update_campaign_settings', methods=['POST'])
@login_required
def update_campaign_settings():
    try:
        data = request.form
        # Update campaign settings logic here
        return jsonify({
            'success': True,
            'message': 'Campaign settings updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400