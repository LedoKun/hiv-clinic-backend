from flask_restful import Resource
from backend.models import Patient, Visit, Lab, Imaging, Appointment
from backend.app import app, db, logger
from flask import jsonify
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from datetime import datetime as dt


class StatsResource(Resource):
    statistics = {}

    def get(self):
        logger.debug("Prearing statistics.")

        # dermographic
        self.patient_stats()

        return jsonify(self.statistics)

    def patient_stats(self):
        patient_query = Patient.query
        patient_df = pd.read_sql(patient_query.statement, db.session.bind)

        # remove unnecessary data
        patient_df.drop(
            [
                "id",
                "timestamp",
                "modify_timestamp",
                "hn",
                "hiv_clinic_id",
                "gov_id_type",
                "gov_id",
                "name",
                "address",
                "tel",
                "relative_tel",
                "plans",
                "search_vector",
            ], inplace=True, axis=1
        )

        ###############
        # Prepare DF
        ###############

        # convert data to datetime object
        patient_df["dob"] = pd.to_datetime(patient_df["dob"])
        patient_df["first_encounter"] = pd.to_datetime(patient_df["first_encounter"])

        # calculate age in months
        patient_df['today'] = dt.now()
        patient_df['age_months'] = patient_df.today.dt.to_period('M') - patient_df.first_encounter.dt.to_period('M')
        patient_df['age_years'] = patient_df['age_months'] / 12
        patient_df.drop(['today', 'dob'], inplace=True, axis=1)

        # first encounter per month
        patient_df['first_encounter'] = patient_df.first_encounter.dt.to_period('M')

        ###############
        # Demographics Data
        ###############

        # No of patient by age group
        # less than 1 year old
        max_age_year = patient_df["age_years"].max()      
        min_age_months = patient_df["age_months"].min()
        min_age_year = patient_df["age_years"].min()

        df_less_than_one = patient_df["age_months"].groupby(pd.cut(patient_df["age_months"], np.arange(min_age_months, 13))).count()
        df_age = patient_df["age_years"].groupby(pd.cut(patient_df["age_years"], np.arange(min_age_year, max_age_year))).count()

        self.statistics["age_less_than_one"] = df_less_than_one
        self.statistics["age"] = df_age

        # No of patient by months and by sex
        df_sex = patient_df["sex"].groupby().count()
        self.statistics["sex"] = df_sex

        import sys
        print(patient_df, file=sys.stdout)

        self.statistics["all"] = patient_df
