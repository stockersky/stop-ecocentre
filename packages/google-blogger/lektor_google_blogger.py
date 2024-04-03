# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin
from lektor.context import get_ctx

import os.path
import os
import datetime
import re
import sys
import json

from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from icecream import ic
from markupsafe import Markup, escape

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/blogger"]

@dataclass
class Publication:
    title: str
    content: str
    published: datetime.datetime
    
    @staticmethod
    def from_entry(post):
        return Publication(
            title=safe_html(post['title']),
            content=safe_html(post['content']),
            published=Publication.get_date(post['published'])
        )

    @staticmethod
    def get_date(date_string):
        # Google Blogger date string has a wrong format
        # 2024-03-13T16:53:00-07:00 should be : 2024-03-13T16:53:00-0700
        standard_string = re.sub(r"-(\d+):(\d+)$", r"-\1\2", date_string)
        pub_date = datetime.datetime.strptime(standard_string, '%Y-%m-%dT%H:%M:%S%z')
        ic(pub_date)
        return pub_date

def volatile():
    """Set the dirty flag on the artifact currently being built."""
    ctx = get_ctx()
    ic(f"ctx --> {ctx}")
    ctx.artifact.set_dirty_flag()

def safe_html(html_doc):
     return Markup(html_doc)

def get_google_oauth2_credentials(credentials_dir):
    if "GOOGLE_TOKEN" in os.environ:
        ic("FROM env vars")
        google_token = json.loads(os.environ["GOOGLE_TOKEN"])
        creds = Credentials.from_authorized_user_info(google_token, SCOPES)
        return creds
    else:
        print(">>>> FROM FILE <<<<<<<<")
        print(f">>>>>>>>>>> {os.getcwd()}<<<<<<<<<<<<<<")
        if not os.path.isdir(credentials_dir):
            print(f"Directory {credentials_dir} does not exists. Exiting")
            sys.exit(0)
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(f"{credentials_dir}/token.json"):
            creds = Credentials.from_authorized_user_file(f"{credentials_dir}//token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        f"{credentials_dir}/credentials.json", SCOPES
                    )
                except Exception as exc:
                    print(exc)
                    sys.exit(0)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(f"{credentials_dir}/token.json", "w") as token:
                token.write(creds.to_json())
        return creds
        


def get_blogger_articles(blog_id, credentials_dir):
    print(f">>>>>>>>>>> {os.getcwd()}<<<<<<<<<<<<<<")
    
    creds = get_google_oauth2_credentials(credentials_dir)

    service = build("blogger", "v3", credentials=creds)

    print("Call the Blogger API")
    posts = []
    request = service.posts().list(
        blogId=blog_id, status="DRAFT", maxResults=20)

    while request is not None:
        response = request.execute()
        posts.extend(response['items'])
        request = service.posts().list_next(request, response)

    print("----------------")
    
    
    for post in posts:
        # ic(post)
        print(post['title'])
        print(post['published'])
        print(f"published type : {type(post['published'])}")
        # print(f">>> {get_image_link(post['content'])}")
        print(f"{safe_html(post['content'])}")
        print("-----------------")

    return [Publication.from_entry(post) for post in posts]


class GoogleBloggerPlugin(Plugin):
    name = 'google-blogger'
    description = u'A Lektor plugin to retrieve posts from Google Blogger.'

    def on_process_template_context(self, context, **extra):
        def test_function():
            return 'Value from plugin %s' % self.name
        context['test_function'] = test_function

    def on_setup_env(self, **extra):
        # Read Lektor google-blogger plugin configuration file
        config = self.get_config()
        if "BLOG_ID" in os.environ:
            blog_id = os.environ["BLOG_ID"]
            credentials_dir = None
        else:
            blog_id = config.get('blog.blog_id', None)
            credentials_dir = config.get('blog.credentials_dir', None)
        
        self.env.jinja_env.globals.update(
            get_blogger_articles=get_blogger_articles(blog_id, credentials_dir),
            # volatile=volatile()
            get_blogger_updated = datetime.datetime.now()
        )


