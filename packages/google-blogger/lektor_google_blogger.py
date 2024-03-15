# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin
from lektor.context import get_ctx

import os.path
import os
import datetime
import re

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

def get_blogger_articles_test():
    return "Hello from Lektor Google Blogger !!!"

def safe_html(html_doc):
     return Markup(html_doc)

def get_blogger_articles(blog_id):
    """Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """

    print(f">>>>>>>>>>> {os.getcwd()}<<<<<<<<<<<<<<")
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("./packages/google-blogger/token.json"):
        creds = Credentials.from_authorized_user_file("./packages/google-blogger/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "./packages/google-blogger/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("./packages/google-blogger/token.json", "w") as token:
            token.write(creds.to_json())


    service = build("blogger", "v3", credentials=creds)

    print("Call the Blogger API")
    posts = []
    request = service.posts().list(
        blogId=blog_id, maxResults=20)

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
    description = u'Add your description here.'

    def on_process_template_context(self, context, **extra):
        def test_function():
            return 'Value from plugin %s' % self.name
        context['test_function'] = test_function

    def on_setup_env(self, **extra):
        config = self.get_config()
        blog_id = config.get('blog.blog_id', None)
        self.env.jinja_env.globals.update(
            get_blogger_articles_test=get_blogger_articles_test(),
            get_blogger_articles=get_blogger_articles(blog_id),
            # volatile=volatile()
        )


