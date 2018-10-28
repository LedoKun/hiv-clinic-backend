from flask_restful import Resource
from backend.models import Patient, Visit, Lab
from backend.app import db, logger
from flask import jsonify
import pandas as pd
import numpy as np
from datetime import datetime as dt
import json
from collections import Counter
from flask_jwt_extended import jwt_required


# Workaround for pd's warnings
pd.options.mode.chained_assignment = None


class StatsResource(Resource):
    statistics = {}

    @staticmethod
    def count_in_list(data_list):
        if not isinstance(data_list, list) or not data_list:
            return None

        else:
            flat_list = [item for sublist in data_list for item in sublist]
            return Counter(flat_list)

    @staticmethod
    def list_to_string(data_list):
        if not isinstance(data_list, list) or not data_list:
            return None

        else:
            return ", ".join(map(str, data_list))

    @staticmethod
    def json_to_list(json_string):
        try:
            return json.loads(json_string)

        except ValueError:
            return None

    @staticmethod
    def groupby(
        df,
        target_column: str,
        output_column_name: str = "output",
        fill_na: bool = False,
        fill_na_by: str = "Missing/None",
        drop_na: bool = False,
    ):
        groupby_series = df.groupby(target_column, squeeze=True)[
            target_column
        ].count()
        groupby_df = groupby_series.reset_index(name=output_column_name)
        groupby_df.columns = [output_column_name, "Count"]
        groupby_df.replace(r"^\s*$", np.nan, regex=True, inplace=True)

        if drop_na:
            groupby_df.dropna(inplace=True)

        if fill_na:
            groupby_df.fillna(fill_na_by, inplace=True)

        return groupby_df

    @jwt_required
    def get(self):
        """
        Serves Clinic Statistics
        """
        logger.debug("Prearing statistics.")

        # dermographic
        self.patient_stats()

        # visit information
        self.visit_stats()

        self.lab_stats()

        return jsonify(self.statistics)

    def lab_stats(self):
        """
        Calculates and serves Lab statistics
        """
        lab_query = Lab.query
        lab_df = pd.read_sql(lab_query.statement, db.session.bind)

        if lab_df.empty:
            return

        # remove unnecessary data
        lab_df.drop(
            ["id", "timestamp", "modify_timestamp"], inplace=True, axis=1
        )

        try:
            print(lab_df)

        except AttributeError as e:
            print(e)

    def visit_stats(self):
        """
        Serves Visit Statistics
        """
        visit_query = Visit.query
        visit_df = pd.read_sql(visit_query.statement, db.session.bind)

        if visit_df.empty:
            return

        # Remove unnecessary data
        visit_df.drop(
            ["id", "timestamp", "modify_timestamp"], inplace=True, axis=1
        )

        # Prepare DF
        # Convert data to datetime object
        visit_df["date"] = pd.to_datetime(visit_df["date"])
        visit_df.set_index(["date"], inplace=True)

        # convert json to string
        for column in Visit.__json__:
            try:
                visit_df[column] = visit_df[column].apply(
                    StatsResource.json_to_list
                )

            except KeyError:
                pass

        # Prepare Lastest Visit DF
        # Only Select Lastest Visit
        visit_df.sort_values("date", ascending=True, inplace=True)
        last_visit_df = visit_df.drop_duplicates(
            subset=["paitent_id"], keep="last"
        )

        # Monthly Stats
        # No of patient by months and by sex
        df_monthly_visit = (
            visit_df.groupby(pd.Grouper(freq="M"))["imp"]
            .count()
            .reset_index(name="Month/Year")
        )
        df_monthly_visit.columns = ["Month/Year", "Number of Visit"]
        df_monthly_visit["Month/Year"] = df_monthly_visit["Month/Year"].apply(
            lambda x: x.strftime("%m/%Y")
        )
        self.statistics["count_monthly_visit"] = df_monthly_visit

        # Overall Stats
        # Current ARV Regimens
        last_visit_df["arv_regimen"] = last_visit_df["arv"].apply(
            StatsResource.list_to_string
        )
        self.statistics["count_arv_regimen"] = StatsResource.groupby(
            df=last_visit_df,
            target_column="arv_regimen",
            output_column_name="ARV Regimens",
        )

        # ARV Breakdown
        count_arv = StatsResource.count_in_list(
            last_visit_df["arv"].values.tolist()
        )
        self.statistics["count_arv_breakdown"] = pd.DataFrame(
            list(count_arv.items()), columns=["ARV Breakdown", "Count"]
        )

        last_visit_df["arv_breakdown"] = last_visit_df["arv"].apply(
            StatsResource.count_in_list
        )

        # Switching ARV?
        self.statistics["count_why_switched_arv"] = StatsResource.groupby(
            df=visit_df,
            target_column="why_switched_arv",
            output_column_name="Why Change ARV Regimens",
            fill_na=True,
        )

        # OI
        count_oi = StatsResource.count_in_list(
            last_visit_df["oi_prophylaxis"].values.tolist()
        )
        self.statistics["count_oi_prophylaxis"] = pd.DataFrame(
            list(count_oi.items()), columns=["OI Prophylaxis", "Count"]
        )

        # Anti TB
        count_anti_tb = StatsResource.count_in_list(
            last_visit_df["anti_tb"].values.tolist()
        )
        self.statistics["count_anti_tb"] = pd.DataFrame(
            list(count_anti_tb.items()),
            columns=["Anti_TB Medications", "Count"],
        )

        # vaccination
        count_vaccine = StatsResource.count_in_list(
            visit_df["vaccination"].values.tolist()
        )
        self.statistics["count_vaccination"] = pd.DataFrame(
            list(count_vaccine.items()), columns=["Vaccines", "Count"]
        )

        # imp
        count_imp = StatsResource.count_in_list(
            visit_df["imp"].values.tolist()
        )
        self.statistics["count_imp"] = pd.DataFrame(
            list(count_imp.items()), columns=["Impressions", "Count"]
        )

    def patient_stats(self):
        """
        Serves Demographics Statistics
        """
        patient_query = Patient.query
        patient_df = pd.read_sql(patient_query.statement, db.session.bind)

        if patient_df.empty:
            return

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
            ],
            inplace=True,
            axis=1,
        )

        # Prepare DF
        # convert data to datetime object
        patient_df["dob"] = pd.to_datetime(patient_df["dob"])
        patient_df["first_encounter"] = pd.to_datetime(
            patient_df["first_encounter"]
        )

        # calculate age in months
        patient_df["today"] = dt.now()
        patient_df["age_months"] = patient_df.today.dt.to_period(
            "M"
        ) - patient_df.dob.dt.to_period("M")
        patient_df["age_years"] = patient_df["age_months"] / 12
        patient_df.drop(["today", "dob"], inplace=True, axis=1)

        # first encounter per month
        patient_df[
            "first_encounter"
        ] = patient_df.first_encounter.dt.to_period("M")

        # Fill na
        patient_df.fillna("Missing/None", inplace=True)

        # Demographics Data
        # No of patient by age group
        # less than one
        self.statistics["count_age_less_than_one"] = (
            patient_df["age_months"]
            .groupby(pd.cut(patient_df["age_months"], np.arange(0, 13)))
            .count()
        ).reset_index(name="Age-Months")
        self.statistics["count_age_less_than_one"].columns = [
            "Age-Years",
            "Count",
        ]

        # more than one
        self.statistics["count_age"] = (
            patient_df["age_years"]
            .groupby(
                pd.cut(
                    patient_df["age_years"],
                    np.arange(0, patient_df["age_years"].max() + 1, 10),
                )
            )
            .count()
        ).reset_index(name="Age-Years")
        self.statistics["count_age"].columns = ["Age-Years", "Count"]

        # Monthly Stats
        # No of patient by months and by sex
        df_monthly_sex = pd.crosstab(
            patient_df.first_encounter, patient_df.sex, margins=True
        ).reset_index()
        df_monthly_sex.rename(
            columns={"first_encounter": "First Encounter"}, inplace=True
        )
        self.statistics["monthly_sex"] = df_monthly_sex

        # No of patient by months and by nationality
        df_monthly_gender = pd.crosstab(
            patient_df.first_encounter, patient_df.nationality, margins=True
        ).reset_index()
        df_monthly_gender.rename(
            columns={"first_encounter": "First Encounter"}, inplace=True
        )
        self.statistics["monthly_gender"] = df_monthly_gender

        # No of patient by months and by is_refer
        df_monthly_is_refer = pd.crosstab(
            patient_df.first_encounter, patient_df.is_refer, margins=True
        ).reset_index()
        df_monthly_is_refer.rename(
            columns={"first_encounter": "First Encounter"}, inplace=True
        )
        self.statistics["monthly_is_refer"] = df_monthly_is_refer

        # No of patient by months and by refer_from
        df_monthly_refer_from = pd.crosstab(
            patient_df.first_encounter, patient_df.refer_from, margins=True
        ).reset_index()
        df_monthly_refer_from.rename(
            columns={"first_encounter": "First Encounter"}, inplace=True
        )
        self.statistics["monthly_refer_from"] = df_monthly_refer_from

        # No of patient by months and by bill_payer
        df_monthly_bill_payer = pd.crosstab(
            patient_df.first_encounter, patient_df.bill_payer, margins=True
        ).reset_index()
        df_monthly_bill_payer.rename(
            columns={"first_encounter": "First Encounter"}, inplace=True
        )
        self.statistics["monthly_bill_payer"] = df_monthly_bill_payer

        # Overall Stats
        # first_encounter
        self.statistics["count_first_encounter"] = StatsResource.groupby(
            df=patient_df,
            target_column="first_encounter",
            output_column_name="เข้ารับการรักษาครั้งแรก",
        )

        # education
        self.statistics["count_education"] = StatsResource.groupby(
            df=patient_df,
            target_column="education",
            output_column_name="Education Level",
        )

        # nationality
        self.statistics["count_nationality"] = StatsResource.groupby(
            df=patient_df,
            target_column="nationality",
            output_column_name="Nationality",
        )

        # sex
        self.statistics["count_sex"] = StatsResource.groupby(
            df=patient_df, target_column="sex", output_column_name="Sex"
        )

        # gender
        self.statistics["count_gender"] = StatsResource.groupby(
            df=patient_df, target_column="gender", output_column_name="Gender"
        )

        # marital
        self.statistics["count_marital"] = StatsResource.groupby(
            df=patient_df,
            target_column="marital",
            output_column_name="Marital Status",
        )

        # is_refer
        self.statistics["count_is_refer"] = StatsResource.groupby(
            df=patient_df,
            target_column="is_refer",
            output_column_name="Referral Status",
        )

        # refer_from
        self.statistics["count_refer_from"] = StatsResource.groupby(
            df=patient_df,
            target_column="refer_from",
            output_column_name="Referred From",
        )

        # bill_payer
        self.statistics["count_bill_payer"] = StatsResource.groupby(
            df=patient_df,
            target_column="bill_payer",
            output_column_name="สิทธิ์การรักษา",
        )
