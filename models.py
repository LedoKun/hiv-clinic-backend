"""
Database model, using Flask-SQLAlchemy
"""

from backend.app import db, logger
from datetime import datetime
from sqlalchemy import exists, desc
from sqlalchemy import DateTime as SdateTime
from sqlalchemy.types import TypeDecorator
from sqlalchemy.inspection import inspect
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import make_searchable, SearchQueryMixin
from flask_sqlalchemy import BaseQuery
import json
import pytz

make_searchable(db.metadata)


class DateTime(TypeDecorator):
    impl = SdateTime

    def process_bind_param(self, value, engine):
        return value

    def process_result_value(self, value, engine):
        return value.replace(tzinfo=timezone("UTC"))


class Serializer(object):
    """
    Serialize Model object
    """

    def serialize(self):
        # Skip a relationship backref
        return {
            c: getattr(self, c)
            for c in inspect(self).attrs.keys()
            if not isinstance(
                getattr(self, c), (Patient, Visit, Lab, Imaging, Appointment)
            )
        }

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class SearchableMixin(BaseQuery, SearchQueryMixin):
    pass


class BaseModel(db.Model, Serializer):
    """
    Base model for all tables
    """

    __abstract__ = True
    __skip__ = ["_sa_instance_state", "search_vector"]

    query_class = SearchableMixin

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
            for key in self.__children__:
                try:
                    del d[key]

                except (KeyError, IndexError):
                    pass

        except AttributeError:
            pass

        try:
            # Convert JSON data to proper data structure
            for key in self.__json__:
                try:
                    if d[key]:
                        d[key] = json.loads(d[key])

                except KeyError:
                    pass

        except AttributeError:
            pass

        return d

    @classmethod
    def convert_to_json(self, data):
        """
        Convert list data to JSON format
        """

        try:
            for key in self.__json__:
                try:
                    if isinstance(data[key], (list, tuple)):
                        data[key].sort()

                    data[key] = json.dumps(data[key], default=str)

                except KeyError as e:
                    logger.debug(e)

                except TypeError as e:
                    logger.debug(e)
                    data[key] = None

        except AttributeError:
            pass

        return data


class Patient(BaseModel):
    """
    Store patient information
    """

    __tablename__ = "patient"
    __protected__ = ["id", "hn", "timestamp", "modify_timestamp"]
    __json__ = ["tel", "relative_tel", "plans"]
    __children__ = ["visits", "labs", "imaging", "appointments"]
    __unique__ = ["hn", "hiv_clinic_id", "gov_id", "nap"]

    hn = db.Column(db.Unicode(), index=True, nullable=False, unique=True)
    hiv_clinic_id = db.Column(db.Unicode(), unique=True)
    gov_id_type = db.Column(db.Unicode())
    gov_id = db.Column(db.Unicode(), unique=True)
    name = db.Column(db.Unicode())
    dob = db.Column(db.Date)
    first_encounter = db.Column(db.Date)
    sex = db.Column(db.Unicode())
    gender = db.Column(db.Unicode())
    marital = db.Column(db.Unicode())
    nationality = db.Column(db.Unicode())
    education = db.Column(db.Unicode())
    address = db.Column(db.Unicode())
    tel = db.Column(db.Unicode())
    relative_tel = db.Column(db.Unicode())
    is_refer = db.Column(db.Unicode())
    refer_from = db.Column(db.Unicode())
    nap = db.Column(db.Unicode(), unique=True)
    bill_payer = db.Column(db.Unicode())
    plans = db.Column(db.Unicode())

    # Full text search support
    search_vector = db.Column(
        TSVectorType(
            "hn",
            "name",
            "gov_id",
            "nationality",
            "nap",
            "refer_from",
            regconfig="pg_catalog.thai",
        )
    )

    # relationship
    visits = db.relationship(
        "Visit",
        backref="patient_id",
        lazy="dynamic",
        order_by="desc(Visit.date)",
        cascade="all, delete, delete-orphan",
    )
    labs = db.relationship(
        "Lab",
        backref="patient_id",
        lazy="dynamic",
        order_by="desc(Lab.date)",
        cascade="all, delete, delete-orphan",
    )
    imaging = db.relationship(
        "Imaging",
        backref="patient_id",
        lazy="dynamic",
        order_by="desc(Imaging.date)",
        cascade="all, delete, delete-orphan",
    )
    appointments = db.relationship(
        "Appointment",
        backref="patient_id",
        lazy="dynamic",
        order_by="desc(Appointment.date)",
        cascade="all, delete, delete-orphan",
    )


class Visit(BaseModel):
    """
    Store patient visit information
    """

    __tablename__ = "visit"
    __protected__ = ["id", "paitent_id", "timestamp", "modify_timestamp"]
    __json__ = ["abn_pe", "imp", "arv", "oi_prophylaxis", "anti_tb", "vaccination"]

    date = db.Column(db.Date, nullable=False)
    is_art_adherence = db.Column(db.Unicode())
    art_adherence_scale = db.Column(db.Float)
    art_delay = db.Column(db.Float)
    art_adherence_problem = db.Column(db.Unicode())
    hx_contact_tb = db.Column(db.Unicode())
    bw = db.Column(db.Float)
    abn_pe = db.Column(db.Unicode())
    imp = db.Column(db.Unicode(), nullable=False)
    arv = db.Column(db.Unicode())
    why_switched_arv = db.Column(db.Unicode())
    oi_prophylaxis = db.Column(db.Unicode())
    anti_tb = db.Column(db.Unicode())
    vaccination = db.Column(db.Unicode())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class Lab(BaseModel):
    """
    Store lab information
    """

    __tablename__ = "lab"
    __protected__ = ["id", "paitent_id", "timestamp", "modify_timestamp"]

    date = db.Column(db.Date, nullable=False)
    anti_hiv = db.Column(db.Unicode(3))
    cd4 = db.Column(db.Integer)
    p_cd4 = db.Column(db.Float)
    vl = db.Column(db.Unicode())
    hiv_resistence = db.Column(db.Unicode())
    vdrl = db.Column(db.Unicode(3))
    rpr = db.Column(db.Unicode())
    hbsag = db.Column(db.Unicode(3))
    anti_hbs = db.Column(db.Unicode(3))
    anti_hcv = db.Column(db.Unicode(3))
    ppd = db.Column(db.Integer)
    afb = db.Column(db.Unicode(10))
    sputum_gs = db.Column(db.Unicode())
    sputum_cs = db.Column(db.Unicode())
    genexpert = db.Column(db.Unicode())
    hain_test = db.Column(db.Unicode())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class Imaging(BaseModel):
    """
    Store Imaging information
    """

    __tablename__ = "imaging"
    __protected__ = ["id", "paitent_id", "timestamp", "modify_timestamp"]

    date = db.Column(db.Date, nullable=False)
    film_type = db.Column(db.Unicode())
    result = db.Column(db.Unicode())

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class Appointment(BaseModel):
    """
    Store Appointment information
    """

    __tablename__ = "appointment"
    __protected__ = ["id", "paitent_id", "timestamp", "modify_timestamp"]

    date = db.Column(db.Date, nullable=False)
    appointment_for = db.Column(db.Unicode(), nullable=False)

    paitent_id = db.Column(db.Integer, db.ForeignKey("patient.id"))


class ICD10(BaseModel):
    """
    Store ICD10 Information
    """

    __tablename__ = "icd10"
    __protected__ = ["id"]

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    icd10 = db.Column(db.Unicode(), nullable=False)
    description = db.Column(db.Unicode(), nullable=False)

    # Full text search support
    search_vector = db.Column(
        TSVectorType("icd10", "description", regconfig="pg_catalog.english")
    )


db.configure_mappers()
