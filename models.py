"""
Database model, using Flask-SQLAlchemy
"""

from backend.app import db
from datetime import datetime
from sqlalchemy import exists, desc
from sqlalchemy.inspection import inspect
import json


class Serializer(object):
    """
    Serialize Model object
    """

    def serialize(self):
        # Skip a relationship backref
        return {
            c: getattr(self, c)
            for c in inspect(self).attrs.keys()
            if not isinstance(getattr(self, c), (Patient, Visit, Lab, Imaging, Appointment))
        }

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class BaseModel(db.Model, Serializer):
    """
    Base model for all tables
    """

    __abstract__ = True
    __skip__ = ["_sa_instance_state"]

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    modify_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def update(self, **kwargs):
        """
        Update column using the provided dictionary
        """

        all_keys = list(vars(self).keys())
        updated_keys = list(kwargs.keys())

        for key in all_keys:
            if key in self.__skip__:
                continue

            elif (key in updated_keys) and (not key in self.__protected__):
                setattr(self, key, kwargs[key])

            elif not key in self.__protected__:
                setattr(self, key, None)

        self.modify_timestamp = datetime.utcnow()

    @classmethod
    def is_exists(self, col, str_filter):
        """
        Check if the value in the specific column exists or not
        """

        if not col or not str_filter:
            return None

        # Check if the data exists in the db
        is_exists = db.session.query(exists().where(col == str_filter)).scalar()

        return is_exists

    def serialize(self):
        """
        Serialize Model object
        """

        d = Serializer.serialize(self)

        try:
            # Remove key from serialize data
            for key in self.__remove__:
                try:
                    del d[key]

                except (KeyError, IndexError):
                    pass

            # Convert JSON data to proper data structure
            for key in self.__json__:
                if d[key]:
                    d[key] = json.loads(d[key])

        except AttributeError:
            pass

        return d


class Patient(BaseModel):
    """
    Store patient information
    """

    __tablename__ = "patient"
    __protected__ = ["id", "hn", "timestamp", "modify_timestamp"]
    __remove__ = ["visits", "labs", "imaging", "appointments"]
    __json__ = ["tel", "relative_tel", "plan"]

    hn = db.Column(db.String(), index=True, nullable=False, unique=True)

    hiv_clinic_id = db.Column(db.String(), unique=True)

    gov_id_type = db.Column(db.String())
    gov_id = db.Column(db.String(), unique=True)

    name = db.Column(db.String())
    dob = db.Column(db.Date)
    first_encounter = db.Column(db.Date)
    sex = db.Column(db.String())
    gender = db.Column(db.String())
    marital = db.Column(db.String())
    nationality = db.Column(db.String())
    education = db.Column(db.Integer)

    address = db.Column(db.String())

    tel = db.Column(db.String())
    relative_tel = db.Column(db.String())

    is_refer = db.Column(db.String())
    refer_from = db.Column(db.String())

    nap = db.Column(db.String())
    bill_payer = db.Column(db.String())

    plan = db.Column(db.String())

    # relationship
    visits = db.relationship("Visit", backref="patient_id", lazy="dynamic", order_by="desc(Visit.date)", cascade="all, delete, delete-orphan")
    labs = db.relationship("Lab", backref="patient_id", lazy="dynamic", order_by="desc(Lab.date)", cascade="all, delete, delete-orphan")
    imaging = db.relationship("Imaging", backref="patient_id", lazy="dynamic", order_by="desc(Imaging.date)", cascade="all, delete, delete-orphan")
    appointments = db.relationship("Appointment", backref="patient_id", lazy="dynamic", order_by="desc(Appointment.date)", cascade="all, delete, delete-orphan")


class Visit(BaseModel):
    """
    Store patient visit information
    """

    __tablename__ = "visit"
    __protected__ = ["id", "date", "paitent_id", "timestamp", "modify_timestamp"]
    __json__ = ["imp", "arv", "oi_prophylaxis", "anti_tb", "vaccination"]

    date = db.Column(db.Date, nullable=False)

    is_art_adherence = db.Column(db.String())
    art_adherence_scale = db.Column(db.Integer)
    art_delay = db.Column(db.Float)
    art_adherence_problem = db.Column(db.String())

    hx_contact_tb = db.Column(db.String())

    bw = db.Column(db.Float)

    imp = db.Column(db.String())
    arv = db.Column(db.String())
    why_switched_arv = db.Column(db.String())
    oi_prophylaxis = db.Column(db.String())
    anti_tb = db.Column(db.String())
    vaccination = db.Column(db.String())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class Lab(BaseModel):
    """
    Store lab information
    """

    __tablename__ = "lab"
    __protected__ = [
        "id",
        "date",
        "paitent_id",
        "paitent",
        "timestamp",
        "modify_timestamp",
    ]

    date = db.Column(db.Date, nullable=False)
    anti_hiv = db.Column(db.String())

    cd4 = db.Column(db.Integer)
    p_cd4 = db.Column(db.Float)
    vl = db.Column(db.String())
    hiv_resistence = db.Column(db.String())

    hbsag = db.Column(db.String())
    anti_hbs = db.Column(db.String())
    anti_hcv = db.Column(db.String())

    afb = db.Column(db.String())
    sputum_cs = db.Column(db.String())
    genexpert = db.Column(db.String())

    vdrl = db.Column(db.String())
    rpr = db.Column(db.String())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    paitent = db.relationship("Patient")


class Imaging(BaseModel):
    """
    Store Imaging information
    """

    __tablename__ = "imaging"
    __protected__ = [
        "id",
        "date",
        "paitent_id",
        "paitent",
        "timestamp",
        "modify_timestamp",
    ]

    date = db.Column(db.Date, nullable=False)
    result = db.Column(db.String())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    paitent = db.relationship("Patient")


class Appointment(BaseModel):
    """
    Store Appointment information
    """

    __tablename__ = "appointment"
    __protected__ = [
        "id",
        "date",
        "paitent_id",
        "paitent",
        "timestamp",
        "modify_timestamp",
    ]

    date = db.Column(db.Date, nullable=False)
    appointment_for = db.Column(db.String())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    paitent = db.relationship("Patient")
