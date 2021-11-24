"""
Code last update 23.11.2021
This is example use of MoyClass library.
"""

from moyclass import MoyClassCompanyAPI
import credentials
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option("max_colwidth", None)

# Libraries for my example
from datetime import datetime, timedelta
import json
from pprint import pprint

def badUsersSearch(api : MoyClassCompanyAPI, load_new_data = True):
    """
    We assume that user is good if he attended at least one of the
     last two lessons in at least one of his groups (classes) during the last month.
     If there were no lessons last month for this user he's not good.
     The user is bad if he isn't good.

    :param api: MoyClassAPI object
    :param load_new_data: load new data from the server if True, load from 'saved_data' folder o.w.
    :return: list of bad users ids and names: [[uId, uName], ... ]
    """

    # Get all users as dataframe and turn them into dictionary {uId: {'name': 'Oleg', 'clientStateId': 179}}
    user_df = api.data_load(api.get_users, 'users', load_new_data=load_new_data)
    user_data_dict = user_df[['name', 'filials', 'id']].set_index('id').to_dict(orient='index')

    # Get joins where user status is 'Учится' ('statusId': 2)
    params = [['statusId', '2']]
    joins_df = api.data_load(api.get_joins, 'joins', params=params, load_new_data=load_new_data)
    user_good_groups = joins_df[['userId', 'classId']].groupby('userId')
    for userId in user_data_dict:
        user_data_dict[userId]['StudyGroups'] = []
        if userId in user_good_groups.groups:
            user_data_dict[userId]['StudyGroups'] = user_good_groups.get_group(userId)['classId'].values

    # Get last month (last 31 days) lessons with lesson records:
    from_date = datetime.today().date() - timedelta(days=31)
    to_date = datetime.today().date()
    params = [['date', f"{from_date}"], ['date', f"{to_date}"], ['includeRecords', 'true']]
    lessons_with_records_df = api.data_load(api.get_lessons, 'lessons', params=params, load_new_data=load_new_data)

    drop_cols = ['beginTime', 'endTime', 'createdAt', 'filialId', 'roomId', 'comment', 'maxStudents',
                 'topic', 'description', 'teacherIds', 'status']
    lessons_with_records_df = lessons_with_records_df.drop(drop_cols, axis=1)

    branches = api.get_company_branches()
    branches_df = pd.DataFrame(branches)
    branches_id = branches_df[['name', 'id']].set_index('id').to_dict(orient='index')

    # user_visits structure:
    # {userId: {classId: [['date', 'visit_status']]}}

    user_visits = {}
    for index, row in lessons_with_records_df.iterrows():
        classId = row['classId']
        date = row['date']
        record = row['records']
        if (len(record)):
            # if(type(record)==str):
            #     record = record.replace("\'", "\"")
            #     record = record.replace("True", "\"True\"")
            #     record = record.replace("False", "\"False\"")
            #     record = record.replace("None", "\"None\"")
            #     record = json.loads(record)
            for el in record:
                userId = el['userId']
                lessonId = el['lessonId']
                if(classId not in user_data_dict[userId]['StudyGroups']):
                    continue
                if(type(el['visit']) == bool and el['visit'] == True):
                    visit = 1
                # elif(type(el['visit']) == str and el['visit'] == "True"):
                #     visit = 1
                else:
                    visit = 0
                if (userId in user_visits.keys()):
                    if (classId in user_visits[userId].keys()):
                        user_visits[userId][classId].append([date, visit])
                    else:
                        user_visits[userId][classId] = [[date, visit]]
                else:
                    user_visits[userId] = {classId: [[date, visit]]}

    good_users = []
    bad_users = []
    for userId in user_visits.keys():
        isBad = True
        for classId in user_visits[userId]:
            dates_visits = user_visits[userId][classId]
            dates_visits.sort(key=lambda el: datetime.strptime(el[0], "%Y-%m-%d"))
            if (len(dates_visits) == 1):
                if (dates_visits[-1][1] == 1):
                    isBad = False
            elif (len(dates_visits) > 1):
                if (dates_visits[-1][1] == 1 or dates_visits[-2][1] == 1):
                    isBad = False
        user_visits[userId]['isBad'] = isBad

        filials = [branches_id[fid]['name'] for fid in user_data_dict[userId]['filials']]
        if (isBad == True):
            bad_users.append([userId, user_data_dict[userId]['name'], filials])
        else:
            good_users.append([userId, user_data_dict[userId]['name'], filials])

    file = open(f'saved_data/bu_{datetime.now()}.txt', 'w')
    file.write(f"Bad users number: {len(bad_users)}\n")
    for el in bad_users:
        file.write(f"{el[0]}, {el[1]} : {el[2]}\n")
    file.close()

    return bad_users

def examplesFunction(api : MoyClassCompanyAPI):
    # Example 1: Get all managers:
    print(f"Managers as list : {api.get_company_managers()}")

    # Example 2: Get all users as dataframe
    user_df = api.data_load(api.get_users, 'users')
    print(f"Users as dataframe : {user_df}")

    # Example 3: Get all lessons as dataframe:
    print(f"Lessons as dataframe : {api.data_load(api.get_lessons, 'lessons')}")

    # Example 4: Get last month (last 31 days) lessons with lesson records:
    from_date = datetime.today().date() - timedelta(days=31)
    to_date = datetime.today().date()
    params = [['date', f"{from_date}"], ['date', f"{to_date}"], ['includeRecords', 'true']]
    lessons_with_records_df = api.data_load(api.get_lessons, 'lessons', params=params)
    print(f"Lessons with records dataframe : {lessons_with_records_df}")

    # Example 5: Create two new managers, change one of them, then delete both of them
    Existed_manager = api.get_company_managers()[0]
    m1_data = {'name': 'Николай Николаевич','phone': '88005553535',
               'filials': [Existed_manager['filials'][0]],'roles': Existed_manager['roles']}
    m2_data = {'name': 'Петр Петрович','phone': '84952128506',
               'filials': [Existed_manager['filials'][0]],'roles': Existed_manager['roles']}
    New_manager_1 = api.create_manager(manager_info=m1_data)
    New_manager_2 = api.create_manager(manager_info=m2_data)

    m1_new_data = {'name': 'Николай Николаевич Николаев','phone': '88005553535',
               'filials': [Existed_manager['filials'][0]],'roles': Existed_manager['roles'],
                   'enabled':False, 'color':'#FFFFFF'}
    New_manager_1 = api.change_manager(New_manager_1['id'], manager_info=m1_new_data)

    api.delete_manager(New_manager_1['id'], replaceToManagerId=Existed_manager['id'])
    api.delete_manager(New_manager_2['id'], replaceToManagerId=Existed_manager['id'])

    # Example 6:



def string_parser(string):
    els = string.split("\n\n")
    for el in els:

        parts = el.split('\n')
        # print(f"\n{parts}")
        p_name = parts[0].replace(" ", "").replace("\t", "")
        if(parts[1]=='required'):
            p_req = 'required'
            p_type = parts[2]
        else:
            p_req = None
            p_type = parts[1]
        p_desc = parts[-1]
        p_default = None
        p_example = None
        p_enum = None
        if (len(parts) > 3 and p_req is None) or (len(parts) > 4 and p_req is 'required'):
            for part in parts[2:-1]:
                if('Default: ' in part):
                    p_default = part
                if('Example: ' in part):
                    p_example = part
                if('Enum: ' in part):
                    p_enum = part
        if(p_req is not None):
            print(f"{p_name} ( required ): {p_desc} [ {p_type} ] ")
        else:
            print(f"{p_name} : {p_desc} [ {p_type} ] ")
        if (p_default is not None):
            if(p_enum is not None):
                print(f" {p_default}, {p_enum}")
            else:
                print(f" {p_default}")
        elif(p_enum is not None):
            print(f" {p_enum}")




def API_test_functions(api: MoyClassCompanyAPI):
    pprint(api.data_load(api.get_invoices, 'invoices'))


if __name__ == '__main__':
    st = datetime.now()
    API_KEY = credentials.API_KEY
    api = MoyClassCompanyAPI(api_key=API_KEY)

    # bu = badUsersSearch(api, load_new_data=True)
    # print(f'bad users number: {len(bu)}')

    # examplesFunction(api)

    # API_test_functions(api)

    print(f"Total time taken: {datetime.now() - st}")

    string = """comment
required
string
Текст комментария

showToUser	
boolean
Default: true
Видимость комментария для ученика

lessonId	
integer or null <int64>
ID занятия

classId	
integer or null <int64>
ID группы

managerId	
integer or null <int64>
ID менеджера"""
    # string_parser(string)