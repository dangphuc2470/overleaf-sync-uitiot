"""Overleaf Client"""
##################################################
# MIT License
##################################################
# File: olclient.py
# Description: Overleaf API Wrapper
# Author: Moritz Glöckl
# License: MIT
# Version: 1.2.0
##################################################

import requests as reqs
from bs4 import BeautifulSoup
import json
import uuid
from socketIO_client import SocketIO
import time

# Where to get the CSRF Token and where to send the login request to
LOGIN_URL = "https://latex.uitiot.vn/login"
PROJECT_URL = "https://latex.uitiot.vn/project"  # The dashboard URL
# The URL to download all the files in zip format
DOWNLOAD_URL = "https://latex.uitiot.vn/project/{}/download/zip"
UPLOAD_URL = "https://latex.uitiot.vn/project/{}/upload"  # The URL to upload files
FOLDER_URL = "https://latex.uitiot.vn/project/{}/folder"  # The URL to create folders
DELETE_URL = "https://latex.uitiot.vn/project/{}/doc/{}"  # The URL to delete files
COMPILE_URL = "https://latex.uitiot.vn/project/{}/compile?enable_pdf_caching=true"  # The URL to compile the project
BASE_URL = "https://www.overleaf.com"  # The Overleaf Base URL
PATH_SEP = "/"  # Use hardcoded path separator for both windows and posix system

class OverleafClient(object):
    """
    Overleaf API Wrapper
    Supports login, querying all projects, querying a specific project, downloading a project and
    uploading a file to a project.
    """

    @staticmethod
    def filter_projects(json_content, more_attrs=None):
        more_attrs = more_attrs or {}
        for p in json_content:
            if not p.get("archived") and not p.get("trashed"):
                if all(p.get(k) == v for k, v in more_attrs.items()):
                    yield p

    def __init__(self, cookie=None, csrf=None):
        self._cookie = cookie  # Store the cookie for authenticated requests
        self._csrf = csrf  # Store the CSRF token since it is needed for some requests

    def login(self, username, password):
        """
        WARNING - DEPRECATED - Not working as Overleaf introduced captchas
        Login to the Overleaf Service with a username and a password
        Params: username, password
        Returns: Dict of cookie and CSRF
        """

        get_login = reqs.get(LOGIN_URL)
        self._csrf = BeautifulSoup(get_login.content, 'html.parser').find(
            'input', {'name': '_csrf'}).get('value')
        login_json = {
            "_csrf": self._csrf,
            "email": username,
            "password": password
        }
        post_login = reqs.post(LOGIN_URL, json=login_json,
                               cookies=get_login.cookies)

        # On a successful authentication the Overleaf API returns a new authenticated cookie.
        # If the cookie is different than the cookie of the GET request the authentication was successful
        if post_login.status_code == 200 and get_login.cookies["overleaf_session2"] != post_login.cookies[
            "overleaf_session2"]:
            self._cookie = post_login.cookies

            # Enrich cookie with GCLB cookie from GET request above
            self._cookie['GCLB'] = get_login.cookies['GCLB']

            # CSRF changes after making the login request, new CSRF token will be on the projects page
            projects_page = reqs.get(PROJECT_URL, cookies=self._cookie)
            self._csrf = BeautifulSoup(projects_page.content, 'html.parser').find('meta', {'name': 'ol-csrfToken'}) \
                .get('content')

            return {"cookie": self._cookie, "csrf": self._csrf}

    def all_projects(self):
        """
        Get all of a user's active projects (= not archived and not trashed)
        Returns: List of project objects
        """
        projects_page = reqs.get(PROJECT_URL, cookies=self._cookie)
        
        # Debug: Check if we're properly authenticated
        if "login" in projects_page.url.lower():
            raise Exception(f"Authentication failed - redirected to login page: {projects_page.url}")
        
        soup = BeautifulSoup(projects_page.content, 'html.parser')
        
        # Try multiple meta tag names for different Overleaf versions
        ol_projects_meta = (
            soup.find('meta', {'name': 'ol-projects'}) or
            soup.find('meta', {'name': 'ol-prefetchedProjectsBlob'})
        )
        
        if ol_projects_meta is None:
            # Try alternative methods to get project data
            print("⚠️  Meta tag 'ol-projects' not found. Trying alternative methods...")
            
            # Method 1: Try to find window.data or similar
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'project' in script.string.lower():
                    # Look for JSON data in scripts
                    import re
                    json_pattern = r'window\.(?:data|projects|state)\s*=\s*(\{.*?\});'
                    matches = re.findall(json_pattern, script.string, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            if 'projects' in data or isinstance(data, list):
                                print("✅ Found project data in window variable")
                                return list(OverleafClient.filter_projects(data.get('projects', data)))
                        except:
                            continue
            
            # Method 2: Look for data in body or other elements
            # This is a fallback - return empty list for now
            print("❌ Could not find project data with any method")
            print("🌐 Page title:", soup.find('title').text if soup.find('title') else 'Unknown')
            print("🔍 Available ol-* meta tags:")
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                if name.startswith('ol-'):
                    content = meta.get('content', '')[:50] + '...' if len(meta.get('content', '')) > 50 else meta.get('content', '')
                    print(f"  {name}: {content}")
            
            return []
        
        json_content = json.loads(ol_projects_meta.get('content'))
        
        # Handle different data formats
        if 'projects' in json_content:
            # ol-prefetchedProjectsBlob format: {"totalSize": N, "projects": [...]}
            projects_data = json_content['projects']
        else:
            # ol-projects format: [project, project, ...]
            projects_data = json_content
            
        return list(OverleafClient.filter_projects(projects_data))

    def get_project(self, project_name):
        """
        Get a specific project by project_name
        Params: project_name, the name of the project
        Returns: project object
        """
        # Use the improved all_projects method and filter
        all_projects = self.all_projects()
        return next((p for p in all_projects if p.get('name') == project_name), None)

    def download_project(self, project_id):
        """
        Download project in zip format
        Params: project_id, the id of the project
        Returns: bytes string (zip file)
        """
        r = reqs.get(DOWNLOAD_URL.format(project_id),
                     stream=True, cookies=self._cookie)
        return r.content

    def create_folder(self, project_id, parent_folder_id, folder_name):
        """
        Create a new folder in a project

        Params:
        project_id: the id of the project
        parent_folder_id: the id of the parent folder, root is the project_id
        folder_name: how the folder will be named

        Returns: folder id or None
        """

        params = {
            "parent_folder_id": parent_folder_id,
            "name": folder_name
        }
        headers = {
            "X-Csrf-Token": self._csrf
        }
        r = reqs.post(FOLDER_URL.format(project_id),
                      cookies=self._cookie, headers=headers, json=params)

        if r.ok:
            return json.loads(r.content)
        elif r.status_code == str(400):
            # Folder already exists
            return
        else:
            raise reqs.HTTPError()

    def get_project_infos(self, project_id):
        """
        Get detailed project infos about the project

        Params:
        project_id: the id of the project

        Returns: project details
        """
        project_infos = None

        # Callback function for the joinProject emitter
        def set_project_infos(a, project_infos_dict, c, d):
            # Set project_infos variable in outer scope
            nonlocal project_infos
            project_infos = project_infos_dict

        # Convert cookie from CookieJar to string
        cookie_parts = []
        
        # Handle different cookie formats for different Overleaf instances
        if "GCLB" in self._cookie:
            cookie_parts.append(f"GCLB={self._cookie['GCLB']}")
        if "overleaf_session2" in self._cookie:
            cookie_parts.append(f"overleaf_session2={self._cookie['overleaf_session2']}")
        if "overleaf.sid" in self._cookie:
            cookie_parts.append(f"overleaf.sid={self._cookie['overleaf.sid']}")
            
        cookie = "; ".join(cookie_parts)

        # Connect to Overleaf Socket.IO, send a time parameter and the cookies
        socket_io = SocketIO(
            BASE_URL,
            params={'t': int(time.time())},
            headers={'Cookie': cookie}
        )

        # Wait until we connect to the socket
        socket_io.on('connect', lambda: None)
        socket_io.wait_for_callbacks()

        # Send the joinProject event and receive the project infos
        socket_io.emit('joinProject', {'project_id': project_id}, set_project_infos)
        socket_io.wait_for_callbacks()

        # Disconnect from the socket if still connected
        if socket_io.connected:
            socket_io.disconnect()

        return project_infos

    def upload_file(self, project_id, project_infos, file_name, file_size, file):
        """
        Upload a file to the project

        Params:
        project_id: the id of the project
        file_name: how the file will be named
        file_size: the size of the file in bytes
        file: the file itself

        Returns: True on success, False on fail
        """

        # Set the folder_id to the id of the root folder
        folder_id = project_infos['rootFolder'][0]['_id']

        # The file name contains path separators, check folders
        if PATH_SEP in file_name:
            local_folders = file_name.split(PATH_SEP)[:-1]  # Remove last item since this is the file name
            current_overleaf_folder = project_infos['rootFolder'][0]['folders']  # Set the current remote folder

            for local_folder in local_folders:
                exists_on_remote = False
                for remote_folder in current_overleaf_folder:
                    # Check if the folder exists on remote, continue with the new folder structure
                    if local_folder.lower() == remote_folder['name'].lower():
                        exists_on_remote = True
                        folder_id = remote_folder['_id']
                        current_overleaf_folder = remote_folder['folders']
                        break
                # Create the folder if it doesn't exist
                if not exists_on_remote:
                    new_folder = self.create_folder(project_id, folder_id, local_folder)
                    current_overleaf_folder.append(new_folder)
                    folder_id = new_folder['_id']
                    current_overleaf_folder = new_folder['folders']
        params = {
            "folder_id": folder_id,
            "_csrf": self._csrf,
            "qquuid": str(uuid.uuid4()),
            "qqfilename": file_name,
            "qqtotalfilesize": file_size,
        }
        files = {
            "qqfile": file
        }

        # Upload the file to the predefined folder
        r = reqs.post(UPLOAD_URL.format(project_id), cookies=self._cookie, params=params, files=files)

        return r.status_code == str(200) and json.loads(r.content)["success"]

    def delete_file(self, project_id, project_infos, file_name):
        """
        Deletes a project's file

        Params:
        project_id: the id of the project
        file_name: how the file will be named

        Returns: True on success, False on fail
        """

        file = None

        # The file name contains path separators, check folders
        if PATH_SEP in file_name:
            local_folders = file_name.split(PATH_SEP)[:-1]  # Remove last item since this is the file name
            current_overleaf_folder = project_infos['rootFolder'][0]['folders']  # Set the current remote folder

            for local_folder in local_folders:
                for remote_folder in current_overleaf_folder:
                    if local_folder.lower() == remote_folder['name'].lower():
                        file = next((v for v in remote_folder['docs'] if v['name'] == file_name.split(PATH_SEP)[-1]),
                                    None)
                        current_overleaf_folder = remote_folder['folders']
                        break
        # File is in root folder
        else:
            file = next((v for v in project_infos['rootFolder'][0]['docs'] if v['name'] == file_name), None)

        # File not found!
        if file is None:
            return False

        headers = {
            "X-Csrf-Token": self._csrf
        }

        r = reqs.delete(DELETE_URL.format(project_id, file['_id']), cookies=self._cookie, headers=headers, json={})

        return r.status_code == str(204)

    def download_pdf(self, project_id):
        """
        Compiles and returns a project's PDF

        Params:
        project_id: the id of the project

        Returns: PDF file name and content on success
        """
        headers = {
            "X-Csrf-Token": self._csrf
        }

        body = {
            "check": "silent",
            "draft": False,
            "incrementalCompilesEnabled": True,
            "rootDoc_id": "",
            "stopOnFirstError": False
        }

        r = reqs.post(COMPILE_URL.format(project_id), cookies=self._cookie, headers=headers, json=body)

        if not r.ok:
            raise reqs.HTTPError()

        compile_result = json.loads(r.content)

        if compile_result["status"] != "success":
            raise reqs.HTTPError()

        pdf_file = next(v for v in compile_result['outputFiles'] if v['type'] == 'pdf')

        download_req = reqs.get(BASE_URL + pdf_file['url'], cookies=self._cookie, headers=headers)

        if download_req.ok:
            return pdf_file['path'], download_req.content

        return None
