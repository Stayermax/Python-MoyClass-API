"""
Code last update 07.11.2021
This is example use of MoyClass library.
"""

from moyclass import MoyClassAPI
import pandas as pd
import credentials

def get_df(function):
    """
    Generic function for DataFrame creation
    """
    l = function()
    df = pd.DataFrame(l)
    print(df.columns)
    return df

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

    # stud_df = get_df(api.get_students)
    # rec_df = get_df(api.get_records)
    df = get_df(api.get_lessons)
    print(api.get_lesson_info(df['id'][0]))
    # print(df)



    # Show debugging process
    # api.show_debugging()
    #
    # # Get user token from the system
    # # You can save this token (like bearer token)
    # #   and there is no need to update it every time
    # user_token = api.get_user_token(login, password)
    #
    # # Update autorisation parameters of the api class with user token
    # api.update_user_token(user_token)
    #
    # # Shows user permissions
    # api.show_user_permissions()
    #
    # # Get clients list
    # clients_data_list = api.get_clients_data()
    #
    # # parse clients data
    # df = api.parse_clients_data(clients_data_list)
    # # show id, name and number of visits for all clients
    # print(df[['id', 'name', 'visits']])
    #
    # # clients ids list
    # all_clients_ids = list(df['id'])
    #
    # # show all visits for client with cid
    # cid = 20419758
    # client_visits = api.get_visits_for_client(cid)
    # print(f'Client {cid} visits')
    # print(f'{pd.DataFrame(client_visits)}')
    #
    # # show all visits for all clients
    # all_clients_visits = api.get_visits_data_for_clients_list(all_clients_ids)
    # for cid in all_clients_visits.keys():
    #     print(f'Client {cid} visits')
    #     print(f'{pd.DataFrame(all_clients_visits[cid])}')
    #
    # # show all attended visits for client with cid
    # cid = 20419758
    # client_visits = api.get_attended_visits_for_client(cid)
    # print(f'Client {cid} attended visits')
    # print(f'{pd.DataFrame(client_visits)}')
    #
    # # show attended visits information for clients:
    # df = api.get_attended_visits_dates_information(all_clients_ids)
    # print(f'Attended visits dataframe: {df}')
    #
    # # show attended visits information for clients with at least one visit:
    # print(f"Attended visits ndataframe with no gaps {df[df['visits_number']>0]}")