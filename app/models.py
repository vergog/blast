from flask_sqlalchemy import SQLAlchemy
from . import db  # Import db from app package instead of creating new instance

class Bridge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin = db.Column(db.String, unique=True, nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    county = db.Column(db.String)
    region = db.Column(db.String)
    due = db.Column(db.String)
    completed = db.Column(db.String)
    prev_gr = db.Column(db.String)
    spans = db.Column(db.String)
    flags = db.Column(db.String)
    flags_info = db.Column(db.String)
    posting = db.Column(db.String)
    posting_info = db.Column(db.String)
    access = db.Column(db.String)
    access_info = db.Column(db.String)
    spe = db.Column(db.String)
    stds = db.Column(db.String)
    field_time = db.Column(db.String)
    week = db.Column(db.String)
    issued = db.Column(db.String)
    due_month = db.Column(db.String)

    def to_dict(self):
        return {
            'bin': self.bin,
            'region': self.region,
            'county': self.county,
            'due': self.due,
            'completed': self.completed,
            'week': self.week,
            'flags': self.flags,
            'flags_info': self.flags_info,
            'posting': self.posting,
            'posting_info': self.posting_info,
            'access': self.access,
            'access_info': self.access_info,
            'spe': self.spe,
            'stds': self.stds,
            'field_time': self.field_time,
            'due_month': self.due_month,
            'lat': self.lat,
            'lon': self.lon,
            'spans': self.spans,
            'prev_gr': self.prev_gr,
            'issued': self.issued
        }

    def get_status(self):
        if self.completed and self.completed.strip():
            return "Inspected"
        elif self.week and self.week.strip().lower() != "unscheduled":
            return "Scheduled"
        else:
            return "Assigned"

    def serialize(self):
        return self.to_dict()