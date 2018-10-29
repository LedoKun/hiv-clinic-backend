from backend.app import app, logger, db
from backend.models import ICD10, User
from sqlalchemy import exc
import threading
import time

import bcrypt


@app.before_first_request
def activate_job():
    # https://networklore.com/start-task-with-flask/

    def read_icd10_file():
        icd10_file_path = "./backend/icd10cm_codes_2019.txt"

        with open(icd10_file_path) as file:
            for line in file:
                columns = line.rstrip().split(maxsplit=1)

                yield {"icd10": columns[0], "description": columns[1]}

    def insert_icd10_into_db():
        """
        Add ICD10 data into DB
        """
        task_finished = False

        while not task_finished:
            try:
                is_table_empty = not bool(ICD10.query.first())

                if is_table_empty:
                    logger.info("Inserting ICD10 codes to DB...")
                    icd10_codes = read_icd10_file()

                    for icd10_code in icd10_codes:
                        icd10 = ICD10(**icd10_code)
                        db.session.add(icd10)

                    db.session.commit()

                else:
                    logger.debug(
                        "No need to insert ICD10 codes into the DB..."
                    )

                task_finished = True

            except exc.SQLAlchemyError as e:
                logger.debug(
                    "Unable to connect to the DB, retrying in 5 sec..."
                )
                logger.debug(e)

                time.sleep(5)

    def run_job():
        # Looking for default user tb01:tb01
        is_table_empty = not bool(User.query.first())

        if is_table_empty:
            hashed = bcrypt.hashpw("tb01".encode(), bcrypt.gensalt()).decode(
                "utf-8"
            )
            user = User(username="tb01", password=hashed)

            db.session.add(user)
            db.session.commit()

            # insert icd10 data
            insert_icd10_into_db()
            logger.info("Done indexing ICD10 codes...")

    thread = threading.Thread(target=run_job)
    thread.start()
