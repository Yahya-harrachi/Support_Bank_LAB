from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField
from wtforms.validators import DataRequired, Email, Length

class TicketForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])