#!/usr/bin/python
import requests
import json

class SikanaApi:
    """
    Class to get data from Sikana's API
    """
    base_url = "https://www.sikana.tv/"
    client_id = None
    secret = None
    token = None

    def __init__(self, client_id, secret, base_url=None):
        self.base_url = base_url or "https://www.sikana.tv/"
        self.client_id = client_id
        self.secret = secret
        self.token = self.__build_token(client_id, secret)

    def __build_token(self, client_id, secret):
        """
        Private method
        Builds an OAuth access token and returns it
        """
        build_token_url = self.base_url + "oauth/v2/token"
        data = {
            'grant_type':'client_credentials',
            'client_id':client_id,
            'client_secret':secret}
        response = requests.post(build_token_url, data=data)
        if response.status_code != 200:
            raise Exception("POST /oauth/v2/token returned code " + format(response.status_code) + ": " + format(response.text))
        resp = response.json()
        return resp['access_token']

    def get_languages(self):
        """
        Returns a Sikana's list of languages
        """
        url = self.base_url + "api/languages?access_token=" + self.token
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("GET /api/languages returned code " + format(response.status_code) + ": " + format(response.text))
        return response.json()

    def get_categories(self, language_code):
        """
        Returns Sikana's categories for a given language
        """
        if language_code == 'pt':  # workaround for incomlet pt strings; use pt-br instead
            url_v1 = self.base_url + "api/categories/languages/" + language_code + '-br' + "?access_token=" + self.token
        else:
            url_v1 = self.base_url + "api/categories/languages/" + language_code + "?access_token=" + self.token
        url = url_v1 + "&version=2"
        
        # A. Extract string translations from url_v1 (used in step C.)
        name2localizedName = {}
        for cat in requests.get(url_v1).json()['categories']:
            name2localizedName[cat['name']] = cat['localizedName']
        print(name2localizedName)
        # helper method
        def get_localizedName(name, localizedName):
            if '__' in localizedName:
                if name in name2localizedName:
                    localizedName = name2localizedName[name]
                elif name == 'diy':
                    localizedName = 'DIY'
                elif name == 'cooking' and 'food' in name2localizedName:
                    localizedName = name2localizedName['food']
                else:
                    print('coundnt find transaltion for', name, 'so returning default', localizedName)
                    localizedName = localizedName.replace('_', '')
            return localizedName

        # B. Get the v2 categories
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("GET /api/categories/languages/" + language_code + " returned code " + format(response.status_code) + ": " + format(response.text))
        response_json = response.json()

        # C. Get translations from localizedName in v1 API
        for key, cat in response_json['categories'].items():
            cat['localizedName'] = get_localizedName(cat['name'], cat['localizedName'])

        return response_json 



    def get_programs(self, language_code, category_name):
        """
        Returns Sikana's programs for given language and category
        """
        url = self.base_url + "api/programs/categories/" + category_name + "/languages/" + language_code + "?access_token=" + self.token + "&version=2"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("GET /api/programs/categories/" + category_name + "/languages/" + language_code + " returned code " + format(response.status_code) + ": " + format(response.text))
        return response.json()

    def get_program(self, language_code, name_canonical):
        """
        Returns the prograrm with given name canonical for the given language
        """
        url = self.base_url + "api/programs/" + name_canonical + "/languages/" + language_code + "?access_token=" + self.token + "&version=2"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("GET /api/programs/" + name_canonical + "/languages/" + language_code + " returned code " + format(response.status_code) + ": " + format(response.text))
        return response.json()

    def get_video(self, language_code, name_canonical):
        """
        Returns the video with the asked name canonical for the given language
        """
        url = self.base_url + "api/videos/" + name_canonical + "/languages/" + language_code + "?access_token=" + self.token + "&version=2"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("GET /api/videos/" + name_canonical + "/languages/" + language_code + " returned code " + format(response.status_code) + ": " + format(response.text))
        return response.json()
