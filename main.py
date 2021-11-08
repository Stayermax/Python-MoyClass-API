"""
Code last update 07.11.2021
This is example use of MoyClass library.
"""

from moyclass import MoyClassAPI
import credentials

import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option("max_colwidth", None)


# unnecessary
import os
from pprint import pprint

def func_df(function):
    """
    Generic function for DataFrame creation
    """
    l = function()
    df = pd.DataFrame(l)
    print(df.columns)
    return df

def resp_df(dict_list):
    """
    Generic function for DataFrame creation
    """
    df = pd.DataFrame(dict_list)
    print(df.columns)
    return df

def make_or_read(path, func):
    if (os.path.exists(path)):
        df = pd.read_csv(path)
    else:
        df = make_df(func)
        df.to_csv(path, index=False)
    return df

def get_dataframes():
    users_path = 'saved_data/users_df.csv'
    courses_path = 'saved_data/courses_df.csv'
    classes_path = 'saved_data/classes_df.csv'
    lessons_path = 'saved_data/lessons_df.csv'
    lessons_records_path = 'saved_data/lessons_records_df.csv'
    joins_path = 'saved_data/joins_df.csv'

    users_df = make_or_read(users_path, api.get_users)
    courses_df = make_or_read(courses_path, api.get_courses)
    classes_df = make_or_read(classes_path, api.get_classes)
    lessons_df = make_or_read(lessons_path, api.get_lessons)
    lessons_records_df = make_or_read(lessons_records_path, api.get_lesson_records)
    joins_df =  make_or_read(joins_path, api.get_joins)

    return users_df, courses_df, classes_df, lessons_df, lessons_records_df, joins_df


if __name__ == '__main__':
    API_KEY = credentials.API_KEY

    api = MoyClassAPI(api_key=API_KEY)
    # print(f"Branches : {api.get_company_branches()}")
    # print(f"Rooms : {api.get_company_rooms()}")
    # print(f"Managers : {api.get_company_managers()}")
    # print(f"Students : {api.get_students()}")
    # print(f"Records : {api.get_records()}") # + record info
    # print(f"Courses : {api.get_courses()}")
    # print(f"Classes : {api.get_classes()}") # + class info
    # print(f"Lessons : {api.get_lessons()}") # + lesson info
    # print(f"Lesson records : {api.get_lesson_records()}") # + lesson_record info

    # users_df, courses_df, classes_df, lessons_df, lessons_records_df, joins_df = get_dataframes()

    # Get clients list

    # pprint(api.get_users()['stats'])


    uid = 1715582 #1741162

    u_info = api.get_user_info(uid)
    print("USER INFO:")
    pprint(u_info)
    # Joins:
    joins_classes = {join['id']:join['classId'] for join in u_info['joins']}
    classes_joins = {join['classId']:join['id'] for join in u_info['joins']}
    print(f"User {uid} joins_ids to classes_ids: {joins_classes}")
    print(f"User {uid} classes_ids to joins_ids: {classes_joins}")

    params = [['userId',f'{uid}'], ['date','2021-10-08'],['date', '2021-11-08']]

    less = api.get_lessons(params)
    l_df = resp_df(less)
    print(f"LESSONS: ")
    print(l_df.head())

    less = api.get_lesson_records(params)['lessonRecords']
    lr_df = resp_df(less)
    print(f"LESSONS RECORDS: ")
    print(lr_df.head(30))


