# coding=utf-8
import json
import requests
import time
import pandas as pd
import datetime
import json

def datetime_parser(DT: str):
    """ datetime in iso8601 format parser """
    a, b = DT.split('+')
    dt = datetime.datetime.strptime(a, "%Y-%m-%dT%H:%M:%S")
    return dt

def json_print(json_object):
    """
    Json object pretty print
    """
    parsed = json.loads(json_object)
    print(json.dumps(parsed, indent=4, sort_keys=True))


class MoyClassAPI:

    def __init__(self, api_key):

        self.api_key = api_key  # your access key
        self.token = self.__get_token()

    def __get_token(self):
        """
        Authorization. Obtaining a token for working with the API.
        You can create and view API keys in the CRM section "My Class" - "Settings - API".
        """
        url = "https://api.moyklass.com/v1/company/auth/getToken"
        return self._post_request(url, headers=None)['accessToken']

    #################################################################
    ##################### G E T   M E T H O D S #####################
    #################################################################

    def _get_request(self, url, get_auth="default", headers="default", params=None):
        """
        Get request template
        """
        if(get_auth == "default"):
            get_auth = {'apiKey':self.api_key}
        if(headers == "default"):
            headers = {"x-access-token": self.token}
        r = requests.get(
            url=url,
            json=get_auth,
            headers=headers,
            params=params
        )
        if (r.status_code == 200):
            return r.json()
        else:
            print(f"Error: {r.status_code}, Message: {r.json()['code']}")
            return None

    def get_company_branches(self, params=None):
        """
        Returns a list of branches
        """
        url = "https://api.moyklass.com/v1/company/filials"
        return self._get_request(url, params=params)

    def get_company_rooms(self, params=None):
        """
        Company audiences
        """
        url = "https://api.moyklass.com/v1/company/rooms"
        return self._get_request(url, params=params)

    def get_company_managers(self, params=None):
        """
        Company employees
        """
        url = "https://api.moyklass.com/v1/company/managers"
        return self._get_request(url, params=params)

    def get_users(self, params=None):
        """
        Company users (clients / students )
        """
        url = "https://api.moyklass.com/v1/company/users"
        return self._get_request(url, params=params)

    def get_user_info(self, uid, params=None):
        """
        uid: user id
        Returns info about the user
        """
        url = f"https://api.moyklass.com/v1/company/users/{uid}"
        return self._get_request(url, params=params)

    def get_joins(self, params=None):
        """
        Returns a list of joins ( requests / records ) in groups ( Список заявок )
        """
        url = "https://api.moyklass.com/v1/company/joins"
        return self._get_request(url, params=params)

    def get_joins_info(self, jid, params=None):
        """
        jid: join id
        Returns info about the join ( request / record ) ( Информация о заявке )
        """
        url = f"https://api.moyklass.com/v1/company/joins/{jid}"
        return self._get_request(url, params=params)

    def get_courses(self, params=None):
        """
        Returns a list of courses ( Список программ )
        """
        url = "https://api.moyklass.com/v1/company/courses"
        return self._get_request(url, params=params)

    def get_classes(self, params=None):
        """
        Returns a list of classes ( Список групп )
        """
        url = "https://api.moyklass.com/v1/company/classes"
        return self._get_request(url, params=params)

    def get_class_info(self, cid, params=None):
        """
        cid: class id
        Returns info about the class ( Информация о группе )
        """
        url = f"https://api.moyklass.com/v1/company/classes/{cid}"
        return self._get_request(url, params=params)

    def get_lessons(self, params=None):
        """
        Returns a list of lessons ( Список занятий )
        """
        url = "https://api.moyklass.com/v1/company/lessons"
        return self._get_request(url, params=params)

    def get_lesson_info(self, lid, params=None):
        """
        lid: lesson id
        Returns info about the lesson ( Информация о занятии )
        """
        url = f"https://api.moyklass.com/v1/company/lessons/{lid}"
        return self._get_request(url, params=params)

    def get_lesson_records(self, params=None):
        """
        Returns a list of lessonRecords ( Список записей на занятия )
        """
        url = "https://api.moyklass.com/v1/company/lessonRecords"
        return self._get_request(url, params=params)

    def get_lesson_record_info(self, lrid, params=None):
        """
        lrid: lesson record id
        Returns info about the lesson record ( Информация о записи на занятие )
        """
        url = f"https://api.moyklass.com/v1/company/lessonRecords/{lrid}"
        return self._get_request(url, params=params)

    def get_(self, params=None):
        """
        Returns a list of
        """
        url = ""
        return self._get_request(url, params=params)

    def get__info(self, id, params=None):
        """
        id:  id
        Returns info about the  ( Информация о  )
        """
        url = f"/{id}"
        return self._get_request(url, params=params)

    #################################################################
    #################### P O S T   M E T H O D S ####################
    #################################################################

    def _post_request(self, url, post_auth="default", headers="default", params=None):
        """
        Post request template
        """
        if(post_auth == "default"):
            post_auth = {'apiKey':self.api_key}
        if(headers == "default"):
            post_auth = {"x-access-token": self.token}
        r = requests.post(
            url = url,
            json = post_auth,
            headers = headers,
            params = params
        )
        if(r.status_code == 200):
            print('Token granted')
            return r.json()
        else:
            print('Autorisation error')

    # def create_manager(self):
    #     """
    #     Create company employee
    #     """
    #     url = "https://api.moyklass.com/v1/company/managers"
    #     return self._post_request(url)